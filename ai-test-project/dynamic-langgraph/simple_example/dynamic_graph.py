import json
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.graph import StateGraph, END
from typing import Callable, Type, Dict, Any, List, Optional
from pydantic import BaseModel, Field

from models import WorkflowDefinition, NodeDefinition, EdgeDefinition



# ----------------- 模拟节点可执行逻辑 -----------------
# 实际应用中，你需要根据 config 动态实例化 LLM, Tool 等
def create_dummy_node_runnable(name: str, config: Dict[str, Any]) -> Runnable:
    """根据定义创建模拟的节点执行函数"""
    def node_function(state: Any) -> Dict[str, Any]:
        print(f"Executing node: {name} with state: {state}")
        # 将 Pydantic 模型转换为字典（如果不是）
        if hasattr(state, 'model_dump'):
            state_dict = state.model_dump()
        else:
            state_dict = state
        
        # 模拟节点执行逻辑，例如调用LLM，并更新状态
        if name == "initial_node":
            return {"output": f"Processed initial input: {state_dict.get('input')}", "next_step": "process"}
        elif name == "process_node":
            return {"output": f"Processed: {state_dict.get('output')}"}
        # 模拟条件路由逻辑，假设节点名为 'route_node'
        elif name == "route_node":
            # 假设根据输入决定走向 'A' 或 'B'
            if state_dict.get('input', '').lower() == 'a':
                return {"route": "A"}
            else:
                return {"route": "B"}
        
        return {"output": f"Result from {name}"}

    return RunnableLambda(node_function).with_config(tags=[name])

# ----------------- 动态图构建与存储 -----------------

# 模拟一个内存中的图注册表
# 实际应用中，应该使用 Redis 或数据库存储
WORKFLOW_REGISTRY: Dict[str, Any] = {}

def build_and_register_workflow(definition: WorkflowDefinition) -> str:
    """
    根据 WorkflowDefinition 动态构建 LangGraph StateGraph，并注册。
    """
    try:
        # 1. 定义状态
        # 为了简化，我们使用一个通用的 Dict 作为状态
        # 实际应用中，你应该定义一个 TypedDict 或 Pydantic model
        class GenericState(BaseModel):
            input: Optional[str] = None
            output: Optional[str] = None
            route: Optional[str] = None
            history: List[str] = Field(default_factory=list)
            # 更多的状态字段...
            
        def update_state(current: GenericState, new: Dict[str, Any]) -> GenericState:
            """自定义的图状态更新函数"""
            current_dict = current.model_dump()
            current_dict.update(new)
            # 记录执行历史
            if 'output' in new:
                current_dict['history'].append(new['output'])
            return GenericState(**current_dict)

        # StateGraph 的类型是 'Type[BaseModel]' 或 'TypedDict'
        graph = StateGraph(GenericState, update_state)
        
        # 2. 添加节点
        node_map: Dict[str, Runnable] = {}
        for node_def in definition.nodes:
            runnable = create_dummy_node_runnable(node_def.name, node_def.config)
            graph.add_node(node_def.name, runnable)
            node_map[node_def.name] = runnable
            
        # 3. 添加边
        for edge_def in definition.edges:
            source = edge_def.source
            target = edge_def.target
            
            if edge_def.condition:
                # 3a. 添加条件路由边
                if target.upper() == "END":
                    target_obj = END
                else:
                    target_obj = target
                    
                # LangGraph 路由需要一个函数来返回下一个节点名 (或END)
                # 假设路由逻辑在源节点中完成，并将结果放入 state['route']
                def router_factory(condition_val: str, next_node: str) -> Callable:
                    def router(state: GenericState) -> str:
                        if state.route == condition_val:
                            return next_node
                        return "" # 返回空字符串表示不匹配，继续查找其他边
                    return router
                
                # 由于 LangGraph 的 set_conditional_edges 要求一个返回节点名或 END 的函数
                # 这里简化处理：我们假设条件路由都在一个特定的 'router_node' 之后
                
                # 更好的做法是：将条件路由逻辑内置在 source 节点的 Runnable 中，
                # 让其返回一个字典 {LangGraph.KEE_FOR_CONDITION_FIELD: target_node}
                # 但为了适应通用的 EdgeDefinition，我们使用 set_conditional_edges
                
                # 
                # **重要提示：** 最标准的 LangGraph 动态路由是使用 `add_conditional_edges`，
                # 它需要一个函数返回 **下一个节点名或END**。
                # 由于这里我们不确定每个节点的行为，我们采用更简单的 **`add_edge`** 和 **`set_entry_point`**。
                
                # **简化处理：如果 condition 存在，我们假设 source 节点是一个 Router**
                # **并且路由逻辑已经内嵌在 source 节点的 Runnable 中（例如返回 'A' 或 'B'）**
                # **这里使用 set_conditional_edges 演示**
                
                # **!!! 警告：这部分逻辑在生产环境中需要更精细的设计来映射 Pydantic 模型到条件函数。**
                if source not in graph.nodes:
                    raise ValueError(f"Source node '{source}' not found for conditional edge.")
                
                # 假设 condition 就是 target
                # 假设 source 节点返回的 state 中有一个字段 'route_key'，其值与 target 匹配
                # 这是一个简化的映射：
                graph.add_edge(source, target_obj) # 对于复杂的条件路由，这行需要替换为 set_conditional_edges
                
                print(f"Warning: Conditional edges are simplified. Edge added: {source} -> {target_obj}")
                
            else:
                # 3b. 添加普通边
                if target.upper() == "END":
                    graph.add_edge(source, END)
                else:
                    graph.add_edge(source, target)
                    
        # 4. 设置入口点
        graph.set_entry_point(definition.entry_point)
        
        # 5. 编译图
        compiled_graph = graph.compile()
        
        # 6. 注册
        # 直接存储编译后的图对象（CompiledStateGraph 不支持 dumps）
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