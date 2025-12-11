"""
动态图构建器
根据工作流定义动态构建 LangGraph 状态图
支持普通边和条件边的自动处理
"""

from typing import Dict, Any, Callable, Optional, Type
from pydantic import create_model, BaseModel, Field
from langgraph.graph import StateGraph, END
import logging

from .models import (
    WorkflowDefinition, NodeDefinition, EdgeDefinition, StateFieldSchema,
    OperatorLog, NodeType, ExecutionLog
)
from .base_node import BaseNode, create_node

logger = logging.getLogger(__name__)


def auto_generate_operator_logs(definition: WorkflowDefinition) -> None:
    """
    自动为工作流的节点生成 operator_logs
    如果节点已有 operator_log，则保持不变
    
    Args:
        definition: 工作流定义（会被修改）
    """
    if not definition.operator_logs:
        definition.operator_logs = {}
    
    # 为每个节点生成 operator_log（如果还没有的话）
    for node_def in definition.nodes:
        if node_def.name not in definition.operator_logs:
            # 根据节点类型生成合理的 schema
            if node_def.type == NodeType.Planner:
                # Planner 节点：接收 input，输出 plan
                op_log = OperatorLog(
                    node_name=node_def.name,
                    input_schema={
                        "input": StateFieldSchema(type="str", description="输入查询")
                    },
                    output_schema={
                        "plan": StateFieldSchema(type="str", description="规划结果"),
                        "status": StateFieldSchema(type="str", description="状态")
                    }
                )
            elif node_def.type == NodeType.Worker:
                # Worker 节点：接收前面节点的结果，输出执行结果
                op_log = OperatorLog(
                    node_name=node_def.name,
                    input_schema={
                        "plan": StateFieldSchema(type="str", description="输入计划")
                    },
                    output_schema={
                        "result": StateFieldSchema(type="str", description="执行结果")
                    }
                )
            elif node_def.type == NodeType.Reflection:
                # Reflection 节点：接收 result，输出 reflection
                op_log = OperatorLog(
                    node_name=node_def.name,
                    input_schema={
                        "result": StateFieldSchema(type="str", description="输入结果")
                    },
                    output_schema={
                        "reflection": StateFieldSchema(type="str", description="反思结果"),
                        "status": StateFieldSchema(type="str", description="状态")
                    }
                )
            elif node_def.type == NodeType.Agent:
                # Agent 节点：动态工作流
                op_log = OperatorLog(
                    node_name=node_def.name,
                    input_schema={
                        "input": StateFieldSchema(type="str", description="输入")
                    },
                    output_schema={
                        "output": StateFieldSchema(type="str", description="输出")
                    }
                )
            else:
                # 其他类型：创建空的 operator_log
                op_log = OperatorLog(
                    node_name=node_def.name,
                    input_schema={},
                    output_schema={}
                )
            
            definition.operator_logs[node_def.name] = op_log


class GraphBuilder:
    """
    工业级的动态图构建器
    负责根据工作流定义构建编译后的 LangGraph
    """
    
    def __init__(self, workflow_registry: Optional[Dict[str, Any]] = None):
        """
        初始化图构建器
        
        Args:
            workflow_registry: 工作流注册表，用于 Agent 节点引用
        """
        self.workflow_registry = workflow_registry or {}
        self._parent_registry = None
    
    def set_parent_registry(self, parent_registry: 'WorkflowRegistry') -> None:
        """设置父级WorkflowRegistry，用于Agent节点查询已注册的工作流"""
        self._parent_registry = parent_registry
    
    def build_graph(self, definition: WorkflowDefinition) -> Any:
        """
        根据工作流定义构建 LangGraph
        
        Args:
            definition: 工作流定义
            
        Returns:
            编译后的 LangGraph
            
        Raises:
            ValueError: 工作流定义不合法
        """
        logger.info(f"Building workflow: {definition.workflow_id}")
        
        # 1. 验证工作流定义
        self._validate_definition(definition)
        
        # 2. 创建动态状态模型
        state_model = self._create_state_model(definition.state_schema)
        
        # 3. 创建状态图
        graph = StateGraph(state_model)
        
        # 4. 创建所有节点并添加到图中
        nodes_map = self._add_nodes_to_graph(graph, definition)
        
        # 保存节点引用到注册表（便于后续查询执行日志）
        if self._parent_registry:
            self._parent_registry._nodes_map[definition.workflow_id] = nodes_map
        
        # 5. 添加边
        self._add_edges_to_graph(graph, definition, nodes_map)
        
        # 6. 设置入口点
        graph.set_entry_point(definition.entry_point)
        
        # 7. 编译图
        compiled_graph = graph.compile()
        
        logger.info(f"Workflow '{definition.workflow_id}' built successfully")
        
        return compiled_graph
    
    def _validate_definition(self, definition: WorkflowDefinition) -> None:
        """验证工作流定义的合法性"""
        if not definition.workflow_id:
            raise ValueError("workflow_id is required")
        
        if not definition.nodes:
            raise ValueError(f"Workflow '{definition.workflow_id}': nodes list is empty")
        
        if not definition.entry_point:
            raise ValueError(f"Workflow '{definition.workflow_id}': entry_point is required")
        
        # 验证入口点存在
        node_names = {node.name for node in definition.nodes}
        if definition.entry_point not in node_names:
            raise ValueError(
                f"Workflow '{definition.workflow_id}': entry_point '{definition.entry_point}' not found in nodes"
            )
        
        # 验证所有边的源和目标存在
        for edge in definition.edges:
            if edge.source not in node_names and edge.source != "END":
                raise ValueError(
                    f"Workflow '{definition.workflow_id}': edge source '{edge.source}' not found in nodes"
                )
            if edge.target not in node_names and edge.target != "END":
                raise ValueError(
                    f"Workflow '{definition.workflow_id}': edge target '{edge.target}' not found in nodes"
                )
    
    def _create_state_model(self, state_schema: Dict[str, StateFieldSchema]) -> Type[BaseModel]:
        """
        动态创建状态模型
        
        Args:
            state_schema: 状态字段定义
            
        Returns:
            动态创建的 Pydantic BaseModel 类
        """
        field_definitions = {}
        
        # 类型映射
        TYPE_MAP = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": Any,  # dict 类型用 Any 接收任意数据
            "List[str]": list,
            "Dict[str, Any]": Any,
        }
        
        for field_name, field_schema in state_schema.items():
            py_type = TYPE_MAP.get(field_schema.type, str)
            default_val = field_schema.default
            
            field_definitions[field_name] = (
                py_type,
                Field(default=default_val, description=field_schema.description)
            )
        
        # 自动添加 history 字段用于追踪执行历史
        if "history" not in field_definitions:
            field_definitions["history"] = (
                list,
                Field(default_factory=list, description="Execution history tracking")
            )
        
        # 关键：使用 ConfigDict 允许任意字段添加（Dify 风格）
        from pydantic import ConfigDict
        
        # 创建有 ConfigDict 的基类
        class DynamicStateBase(BaseModel):
            model_config = ConfigDict(extra='allow')
        
        # 动态创建模型，继承自定义基类
        DynamicState = create_model(
            'DynamicWorkflowState',
            **field_definitions,
            __base__=DynamicStateBase
        )
        
        return DynamicState
    
    def _add_nodes_to_graph(
        self,
        graph: StateGraph,
        definition: WorkflowDefinition
    ) -> Dict[str, BaseNode]:
        """
        创建所有节点并添加到图中
        
        Args:
            graph: StateGraph 实例
            definition: 工作流定义
            
        Returns:
            节点名称到节点实例的映射
        """
        # 构建可用的工作流注册表（包括已注册的和当前注册中的）
        available_workflows = {}
        if self._parent_registry:
            available_workflows.update(self._parent_registry._registry)
        available_workflows.update(self.workflow_registry)
        
        nodes_map = {}
        
        for node_def in definition.nodes:
            try:
                # 获取操作符日志
                operator_log = definition.operator_logs.get(node_def.name)
                
                # 创建节点
                node = create_node(
                    node_def,
                    operator_log=operator_log,
                    workflow_registry=available_workflows
                )
                
                # 构建节点的 Runnable
                runnable = node.build_runnable()
                
                # 如果节点没有 operator_log，为其添加一个空的（或从节点提取）
                if not operator_log and hasattr(node, 'operator_log'):
                    definition.operator_logs[node_def.name] = node.operator_log
                
                # 添加到图中
                graph.add_node(node_def.name, runnable)
                
                nodes_map[node_def.name] = node
                
                logger.debug(f"Added node: {node_def.name} (type: {node_def.type})")
                
            except Exception as e:
                logger.error(f"Failed to create node '{node_def.name}': {e}")
                raise
        
        return nodes_map
    
    def _add_edges_to_graph(
        self,
        graph: StateGraph,
        definition: WorkflowDefinition,
        nodes_map: Dict[str, BaseNode]
    ) -> None:
        """
        添加边到图中
        支持普通边和条件边
        
        Args:
            graph: StateGraph 实例
            definition: 工作流定义
            nodes_map: 节点映射
        """
        for edge_def in definition.edges:
            source = edge_def.source
            target = edge_def.target
            condition = edge_def.condition
            
            try:
                # 处理目标节点
                if target == "END":
                    target_obj = END
                else:
                    target_obj = target
                
                # 根据是否有条件来处理
                if condition:
                    # 添加条件边
                    self._add_conditional_edge(graph, source, target_obj, condition)
                else:
                    # 添加普通边
                    self._add_normal_edge(graph, source, target_obj)
                
                logger.debug(f"Added edge: {source} -> {target}" + 
                           (f" (condition: {condition})" if condition else ""))
                
            except Exception as e:
                logger.error(f"Failed to add edge {source} -> {target}: {e}")
                raise
    
    def _add_normal_edge(self, graph: StateGraph, source: str, target: Any) -> None:
        """添加普通边"""
        graph.add_edge(source, target)
    
    def _add_conditional_edge(
        self,
        graph: StateGraph,
        source: str,
        target: Any,
        condition_key: str
    ) -> None:
        """
        添加条件边
        
        Args:
            graph: StateGraph 实例
            source: 源节点名称
            target: 目标节点（可以是节点名称或 END）
            condition_key: 条件路由键名
        """
        def router_func(state: Any) -> str:
            """
            路由函数：根据状态中的条件键确定下一个节点
            """
            # 将 Pydantic 模型转换为字典
            if hasattr(state, 'model_dump'):
                state_dict = state.model_dump()
            else:
                state_dict = state
            
            # 获取条件值
            condition_value = state_dict.get(condition_key)
            
            # 如果条件值为 None 或空，返回原始目标
            if condition_value is None:
                return target if isinstance(target, str) else "END"
            
            # 如果条件值匹配目标节点名称或是一个有效的路由值
            # 这里可以扩展更复杂的路由逻辑
            return condition_value if isinstance(condition_value, str) else str(condition_value)
        
        # 添加条件边
        # path_map 需要包含所有可能的路由值到目标节点的映射
        path_map = {}
        if isinstance(target, str):
            path_map[target] = target
            path_map[condition_key] = target
        
        graph.add_conditional_edges(source, router_func, path_map)


class WorkflowRegistry:
    """
    工作流注册表
    管理已编译的工作流，支持存储、加载和执行
    """
    
    def __init__(self):
        """初始化注册表"""
        self._registry: Dict[str, Any] = {}
        self._definitions: Dict[str, WorkflowDefinition] = {}  # 存储工作流定义
        self._nodes_map: Dict[str, Dict[str, BaseNode]] = {}  # 存储每个工作流的节点
        self._graph_builder = GraphBuilder(self._registry)
        self._graph_builder.set_parent_registry(self)
    
    def register_workflow(self, definition: WorkflowDefinition) -> str:
        """
        注册（编译）一个工作流
        
        Args:
            definition: 工作流定义
            
        Returns:
            工作流 ID
        """
        try:
            # 自动为没有 operator_logs 的节点生成默认值
            auto_generate_operator_logs(definition)
            
            # 保存工作流定义
            self._definitions[definition.workflow_id] = definition
            
            compiled_graph = self._graph_builder.build_graph(definition)
            self._registry[definition.workflow_id] = compiled_graph
            logger.info(f"Workflow '{definition.workflow_id}' registered successfully")
            return definition.workflow_id
        except Exception as e:
            logger.error(f"Failed to register workflow '{definition.workflow_id}': {e}")
            raise
    
    def get_workflow(self, workflow_id: str) -> Any:
        """
        获取已注册的工作流
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            编译后的工作流
            
        Raises:
            ValueError: 工作流不存在
        """
        if workflow_id not in self._registry:
            raise ValueError(f"Workflow '{workflow_id}' not found in registry")
        return self._registry[workflow_id]
    
    def has_workflow(self, workflow_id: str) -> bool:
        """检查工作流是否存在"""
        return workflow_id in self._registry
    
    def list_workflows(self) -> list[str]:
        """列出所有已注册的工作流 ID"""
        return list(self._registry.keys())
    
    def unregister_workflow(self, workflow_id: str) -> bool:
        """
        移除一个工作流
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            是否成功移除
        """
        if workflow_id in self._registry:
            del self._registry[workflow_id]
            logger.info(f"Workflow '{workflow_id}' unregistered")
            return True
        return False
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Any:
        """
        执行一个工作流
        
        Args:
            workflow_id: 工作流 ID
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        workflow = self.get_workflow(workflow_id)
        logger.info(f"Executing workflow '{workflow_id}'")
        
        try:
            result = workflow.invoke(input_data)
            logger.info(f"Workflow '{workflow_id}' executed successfully")
            
            # 收集所有节点的执行日志回工作流定义
            self._collect_execution_logs(workflow_id)
            
            return result
        except Exception as e:
            logger.error(f"Workflow '{workflow_id}' execution failed: {e}")
            raise
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        return {
            "total_workflows": len(self._registry),
            "workflow_ids": self.list_workflows()
        }
    
    def _collect_execution_logs(self, workflow_id: str) -> None:
        """
        收集所有节点的执行日志並変新到工作流定义
        
        Args:
            workflow_id: 工作流 ID
        """
        definition = self.get_workflow_definition(workflow_id)
        if not definition:
            return
        
        nodes_map = self._nodes_map.get(workflow_id, {})
        execution_history = []
        
        # 收集每个节点的执行日志
        for node_name, node in nodes_map.items():
            node_logs = node.get_execution_history()
            execution_history.extend(node_logs)
        
        # 按时间排序执行日志
        execution_history.sort(key=lambda log: log.timestamp)
        
        # 更新工作流定义中的执行历史
        definition.execution_history = execution_history
    
    # --- 查询接口 ---
    
    def get_workflow_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """
        获取工作流的定义
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            工作流定义，不存在時返回 None
        """
        return self._definitions.get(workflow_id)
    
    def get_operator_logs(self, workflow_id: str) -> Dict[str, OperatorLog]:
        """
        获取工作流的操作符日志
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            操作符日志字典 {node_name: OperatorLog}
        """
        definition = self.get_workflow_definition(workflow_id)
        if not definition:
            logger.warning(f"Workflow '{workflow_id}' not found")
            return {}
        return definition.operator_logs
    
    def get_operator_log_by_node(self, workflow_id: str, node_name: str) -> Optional[OperatorLog]:
        """
        获取特定节点的操作符日志
        
        Args:
            workflow_id: 工作流 ID
            node_name: 节点名称
            
        Returns:
            操作符日志，不存在時返回 None
        """
        logs = self.get_operator_logs(workflow_id)
        return logs.get(node_name)
    
    def get_execution_history(self, workflow_id: str) -> list[ExecutionLog]:
        """
        获取工作流的执行历史
        
        Args:
            workflow_id: 工作流 ID
            
        Returns:
            执行日志列表 [ExecutionLog]
        """
        definition = self.get_workflow_definition(workflow_id)
        if not definition:
            logger.warning(f"Workflow '{workflow_id}' not found")
            return []
        return definition.execution_history
    
    def get_node_execution_history(self, workflow_id: str, node_name: str) -> list[ExecutionLog]:
        """
        获取特定节点的执行历史
        
        Args:
            workflow_id: 工作流 ID
            node_name: 节点名称
            
        Returns:
            特定节点的执行日志列表
        """
        history = self.get_execution_history(workflow_id)
        return [log for log in history if log.node_name == node_name]
    
    def get_node_by_name(self, workflow_id: str, node_name: str) -> Optional[BaseNode]:
        """
        获取特定节点的对象（便于直接调用其方法）
        
        Args:
            workflow_id: 工作流 ID
            node_name: 节点名称
            
        Returns:
            节点对象，不存在時返回 None
        """
        nodes_map = self._nodes_map.get(workflow_id, {})
        return nodes_map.get(node_name)
    
    def print_workflow_logs(self, workflow_id: str) -> None:
        """
        打印工作流的全部日志（便于调试）
        
        Args:
            workflow_id: 工作流 ID
        """
        definition = self.get_workflow_definition(workflow_id)
        if not definition:
            print(f"\u26a0️  工作流 '{workflow_id}' 不存在")
            return
        
        print(f"\n{'='*80}")
        print(f"📄 工作流日志: {workflow_id}")
        print(f"{'='*80}")
        
        # 打印操作符日志
        if definition.operator_logs:
            print(f"\n💼 操作符日志 (OperatorLog):")
            print("-" * 80)
            for node_name, op_log in definition.operator_logs.items():
                print(f"  节点: {node_name}")
                print(f"    输入 Schema:")
                for field_name, field_schema in op_log.input_schema.items():
                    print(f"      - {field_name}: {field_schema.type} ({field_schema.description})")
                print(f"    输出 Schema:")
                for field_name, field_schema in op_log.output_schema.items():
                    print(f"      - {field_name}: {field_schema.type} ({field_schema.description})")
        
        # 打印执行历史
        if definition.execution_history:
            print(f"\n⏱️  执行历史 (ExecutionLog):")
            print("-" * 80)
            for idx, exec_log in enumerate(definition.execution_history, 1):
                print(f"  [{idx}] {exec_log.node_name} ({exec_log.node_type.value})")
                print(f"      执行时间: {exec_log.timestamp}")
                print(f"      耗时: {exec_log.execution_time_ms:.2f}ms")
                if exec_log.error:
                    print(f"      错误: {exec_log.error}")
                else:
                    print(f"      输入: {exec_log.input_data}")
                    print(f"      输出: {exec_log.output_data}")
        else:
            print("\n  暂无执行日志")
        
        print(f"{'='*80}\n")
