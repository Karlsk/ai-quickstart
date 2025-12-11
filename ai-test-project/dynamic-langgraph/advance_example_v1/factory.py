# 假设你已经安装了 langchain-openai, langchain-community
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.runnables import RunnableLambda, Runnable
from langchain.tools import BaseTool
from typing import Callable, Any, List, Dict
from pydantic import BaseModel

from models import NodeDefinition, EdgeDefinition, WorkflowDefinition, NodeType


# ----------------- 模拟/实际组件 -----------------

# 模拟一个工具
@tool
def dummy_calculator(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b


TOOLS: List[BaseTool] = [dummy_calculator]  # 注册所有可用工具

class RunnableFactory:
    """动态创建 LangChain Runnable 实例的工厂类。"""
    @staticmethod
    def create_runnable(node_def: NodeDefinition) -> Runnable:
        """
        根据节点定义实例化并返回一个 LangChain Runnable。
        """
        if node_def.type == NodeType.LLM:
            return RunnableFactory._create_llm_node(node_def)
        elif node_def.type == NodeType.TOOL:
            return RunnableFactory._create_tool_node(node_def)
        elif node_def.type == NodeType.CUSTOM:
            return RunnableFactory._create_custom_node(node_def)
        else:
            raise ValueError(f"Unsupported node type: {node_def.type}")

    @staticmethod
    def _create_llm_node(node_def: NodeDefinition) -> Runnable:
        from dotenv import load_dotenv
        load_dotenv()
        """实例化 LangChain LLM (如 ChatOpenAI)，包装成接收状态对象的 Runnable"""
        # 实际应用中，应从 config 中获取 model_name, api_key 等
        model_name = node_def.config.get("model_name", "gpt-3.5-turbo")
        temperature = node_def.config.get("temperature", 0.7)
        # 为了演示，我们假设 ChatOpenAI 可以实例化
        # 生产环境请确保配置了 OPENAI_API_KEY 环境变量
        try:
            # 注意：LLM 节点通常需要与 LangGraph 的状态结构和 prompt 结合，
            # 这里返回 LLM 实例本身
            llm = ChatOpenAI(model=model_name, temperature=temperature)
            
            # 包装 LLM，使其能处理 Pydantic 状态对象
            def llm_node_func(state: BaseModel) -> Dict[str, Any]:
                # 将 Pydantic 模型转换为字典
                if hasattr(state, 'model_dump'):
                    state_dict = state.model_dump()
                else:
                    state_dict = dict(state) if hasattr(state, '__dict__') else state
                
                # 从状态中提取查询文本（假设有 'query' 或 'input' 字段）
                query = state_dict.get('query') or state_dict.get('input') or str(state_dict)
                
                # 调用 LLM
                response = llm.invoke(query)
                
                # 返回字典格式的更新
                return {"llm_output": response.content if hasattr(response, 'content') else str(response)}
            
            return RunnableLambda(llm_node_func)
        except Exception:
            # 如果没有安装或配置，返回一个模拟的 Runnable
            print("Warning: OpenAI config not found. Using a dummy LLM runnable.")

            def dummy_llm_func(state: BaseModel) -> Dict[str, Any]:
                # 将 Pydantic 模型转换为字典
                if hasattr(state, 'model_dump'):
                    state_dict = state.model_dump()
                else:
                    state_dict = dict(state) if hasattr(state, '__dict__') else state
                    
                return {"llm_output": f"Mock LLM response for: {state_dict.get('query', state_dict.get('input', 'No Query'))}"}

            return RunnableLambda(dummy_llm_func)

    @staticmethod
    def _create_tool_node(node_def: NodeDefinition) -> Runnable:
        """实例化 Tool 或 AgentExecutor"""
        # 实际应用中，您可能需要创建一个 ToolExecutor 或 AgentExecutor

        tool_name = node_def.config.get("tool_name")
        if not tool_name:
            raise ValueError("Tool node must specify 'tool_name' in config.")

        # 查找注册的工具
        selected_tool = next((t for t in TOOLS if t.name == tool_name), None)

        if not selected_tool:
            raise ValueError(f"Tool '{tool_name}' not found in registry.")

        # 返回一个简单的 RunnableLambda 来执行工具（简化处理，不使用AgentExecutor）
        def tool_executor(state: BaseModel) -> Dict[str, Any]:
            # 假设工具需要一个名为 'tool_input' 的状态字段
            tool_input = getattr(state, "tool_input", None)
            if tool_input is None:
                raise ValueError("Tool input required but not found in state.")

            print(f"Executing tool '{tool_name}' with input: {tool_input}")
            # 假设工具的输入只有一个参数
            result = selected_tool.invoke({"a": tool_input.get("a", 0), "b": tool_input.get("b", 0)})
            return {"tool_output": result}

        return RunnableLambda(tool_executor)

    @staticmethod
    def _create_custom_node(node_def: NodeDefinition) -> Runnable:
        """实例化自定义函数 (RunnableLambda)"""

        # 这里的自定义节点通常是一个 Python 函数，用于业务逻辑或状态转换
        # 由于我们是运行时配置，我们不能动态加载任意 Python 函数
        # **解决方案：** 预注册一组可用的自定义函数，通过 name 查找

        AVAILABLE_CUSTOM_FUNCTIONS: Dict[str, Callable] = {
            "extract_input": lambda state: {"input_key": getattr(state, 'user_prompt', 'N/A').upper()},
            "final_formatter": lambda state: {"final_result": f"Done: {getattr(state, 'history', [])}"}
        }

        function_name = node_def.config.get("function_name")
        if not function_name:
            # 如果没有指定函数名，返回一个通用的打印/更新节点
            def generic_custom_func(state: BaseModel) -> Dict[str, Any]:
                print(f"Running generic custom node: {node_def.name}")
                return {"generic_log": f"Node {node_def.name} executed."}

            return RunnableLambda(generic_custom_func)

        custom_func = AVAILABLE_CUSTOM_FUNCTIONS.get(function_name)
        if not custom_func:
            raise ValueError(f"Custom function '{function_name}' not registered.")

        return RunnableLambda(custom_func)