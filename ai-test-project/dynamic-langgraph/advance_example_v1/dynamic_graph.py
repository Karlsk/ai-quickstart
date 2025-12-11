import json
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.graph import StateGraph, END
from typing import Callable, Type, Dict, Any, List, Optional
from pydantic import BaseModel, Field, create_model

from models import WorkflowDefinition, NodeDefinition, EdgeDefinition, StateFieldSchema
from factory import RunnableFactory
# ----------------- 动态图构建与存储 -----------------

# 模拟一个内存中的图注册表
# 实际应用中，应该使用 Redis 或数据库存储
WORKFLOW_REGISTRY: Dict[str, Any] = {}

def create_dynamic_state_model(schema: Dict[str, StateFieldSchema]) -> Type[BaseModel]:
    """根据 Schema 动态创建 Pydantic BaseModel 类"""
    field_definitions = {}

    # 映射字符串类型到实际 Python 类型
    TYPE_MAP = {
        "str": str, "int": int, "float": float, "bool": bool,
        "List[str]": List[str], "Dict[str, Any]": Dict[str, Any],
        # 可以在这里扩展更多类型
    }
    for field_name, field_schema in schema.items():
        py_type = TYPE_MAP.get(field_schema.type, str)  # 默认使用 str
        default_val = field_schema.default

        # Pydantic 字段定义是 (type, FieldInfo)
        field_definitions[field_name] = (
            py_type,
            Field(default=default_val, description=field_schema.description)
        )

        # 确保图状态至少包含一个通用的历史或日志字段
    if "history" not in field_definitions:
        field_definitions["history"] = (List[str], Field(default_factory=list, description="Execution history"))

        # 动态创建 Pydantic 模型
    DynamicState = create_model(
        'DynamicWorkflowState',
        **field_definitions,
        __base__=BaseModel  # 必须继承 BaseModel
    )
    return DynamicState


def build_and_register_workflow(definition: WorkflowDefinition) -> str:
    """
    根据 WorkflowDefinition 动态构建 LangGraph StateGraph，并注册。
    """
    try:
        # 1. 动态创建状态模型
        DynamicState = create_dynamic_state_model(definition.state_schema)

        # 2. 定义状态更新函数
        def update_state(current: DynamicState, new: Dict[str, Any]) -> DynamicState:
            """自定义的图状态更新函数"""
            current_dict = current.model_dump()

            # 将执行历史也加入更新（如果节点有输出）
            if 'llm_output' in new:
                 new['history'] = current_dict['history'] + [f"LLM: {new['llm_output'][:30]}..."]
            elif 'tool_output' in new:
                 new['history'] = current_dict['history'] + [f"Tool: {new['tool_output']}"]
            elif 'generic_log' in new:
                 new['history'] = current_dict['history'] + [f"Custom: {new['generic_log']}"]

            current_dict.update(new)
            return DynamicState(**current_dict)


        graph = StateGraph(DynamicState, update_state)

        # 3. 添加节点 (使用 RunnableFactory)
        for node_def in definition.nodes:
            runnable = RunnableFactory.create_runnable(node_def)
            graph.add_node(node_def.name, runnable)

        # 4. 添加边
        for edge_def in definition.edges:
            source = edge_def.source
            target = edge_def.target

            target_obj = END if target.upper() == "END" else target

            if edge_def.condition:
                # **简化条件路由：** 假设所有条件路由都依赖于一个状态字段
                # 生产环境需要更健壮的路由函数生成器

                # 路由函数必须接受状态，并返回下一个节点名或 END
                def router_func_factory(condition_val: str, next_node: Any) -> Callable:
                    def router(state: DynamicState) -> Any:
                        # 假设我们检查状态中是否存在一个名为 'route_key' 的字段
                        if getattr(state, 'route_key', None) == condition_val:
                            return next_node
                        return "" # 返回空字符串表示不匹配
                    return router

                graph.add_conditional_edges(
                    source,
                    router_func_factory(edge_def.condition, target_obj),
                    # 这里只需要提供一个键值到目标节点的映射 (如果路由函数是通用的)
                    # 由于我们动态生成了路由函数，可以直接调用
                    path_map={
                        edge_def.condition: target_obj
                    }
                )
            else:
                # 普通边
                graph.add_edge(source, target_obj)

        # 5. 设置入口点
        graph.set_entry_point(definition.entry_point)

        # 6. 编译图并注册
        compiled_graph = graph.compile()
        # 直接存储编译后的图对象（不进行序列化）
        WORKFLOW_REGISTRY[definition.workflow_id] = compiled_graph
        
        return definition.workflow_id

    except Exception as e:
        print(f"Error building graph: {e}")
        raise

def load_and_run_workflow(workflow_id: str, input_data: Dict[str, Any]) -> Any:
    """
    从注册表中加载 LangGraph 并运行。
    """
    if workflow_id not in WORKFLOW_REGISTRY:
        raise ValueError(f"Workflow ID '{workflow_id}' not found.")
        
    # 1. 获取编译后的图
    compiled_graph = WORKFLOW_REGISTRY[workflow_id]
    
    # 2. 运行图
    # 假设输入是一个包含 'input' 键的字典
    # 注意：StateGraph 的输入必须符合其状态模型
    result = compiled_graph.invoke(input_data)
    
    return result