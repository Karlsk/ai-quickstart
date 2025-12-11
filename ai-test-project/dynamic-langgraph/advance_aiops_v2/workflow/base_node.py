"""
基础节点接口和工厂函数
定义所有节点类型的统一接口，确保工业级代码质量
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, Type
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel
import time
from .models import (
    NodeType, NodeDefinition, ExecutionLog, OperatorLog, 
    StateFieldSchema, PlannerConfig, WorkerConfig, ReflectionConfig, AgentConfig
)


# --- 工具函数 ---

def convert_state_to_dict(state: Any) -> Dict[str, Any]:
    """
    将状态转换为字典
    支持 Pydantic 模型、字典和其他类型
    
    Args:
        state: 任何类型的状态对象
        
    Returns:
        Dict: 转换后的字典
    """
    if hasattr(state, 'model_dump'):
        return state.model_dump()
    elif isinstance(state, dict):
        return state
    else:
        return {}


def map_output_to_state(node_name: str, node_output: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    将节点输出映射到状态更新
    采用类似 Dify 的机制：将输出存储为 {node_name}_result
    后续节点可通过 state[f"{prev_node_name}_result"] 获取前面节点的数据
    
    Args:
        node_name: 节点名称
        node_output: 节点返回的输出
        state: 当前状态（用于更新 history）
        
    Returns:
        Dict: 返回给 LangGraph 的状态更新
    """
    # 使用通用的模式：{node_name}_result
    # 这样后续节点可以灵活访问任何前面节点的输出
    state_update = {}
    
    # 主要输出存储为 {node_name}_result
    state_update[f"{node_name}_result"] = node_output
    
    # 同时保留原始的逐字段更新（用于兼容旧的使用方式）
    state_update.update(node_output)
    
    # 更新 history（如果存在）
    if state and "history" in state:
        # 获取当前 history
        history = state.get("history", [])
        if not isinstance(history, list):
            history = []
        
        # 添加当前节点的执行记录
        entry = f"{node_name}: {str(node_output)[:100]}..."
        history_update = history + [entry]
        state_update["history"] = history_update
    
    return state_update


class BaseNode(ABC):
    """
    所有节点类型的基类
    定义节点的统一接口和生命周期
    """
    
    def __init__(
        self,
        name: str,
        node_type: NodeType,
        config: Dict[str, Any],
        operator_log: Optional[OperatorLog] = None
    ):
        """
        初始化节点
        
        Args:
            name: 节点名称
            node_type: 节点类型
            config: 节点配置
            operator_log: 操作符日志（记录输入输出 schema）
        """
        self.name = name
        self.node_type = node_type
        self.config = config
        self.operator_log = operator_log
        self._execution_history: list[ExecutionLog] = []
    
    @abstractmethod
    def build_runnable(self) -> Runnable:
        """
        构建可执行的 Runnable 对象
        每种节点类型需要实现自己的 Runnable 逻辑
        
        Returns:
            Runnable: LangChain 的可执行对象
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        验证节点配置的合法性
        
        Returns:
            bool: 配置是否合法
            
        Raises:
            ValueError: 配置不合法时抛出异常
        """
        pass
    
    def get_execution_history(self) -> list[ExecutionLog]:
        """获取节点的执行历史"""
        return self._execution_history.copy()
    
    def log_execution(self, execution_log: ExecutionLog) -> None:
        """记录一次执行日志"""
        self._execution_history.append(execution_log)
    
    def clear_execution_history(self) -> None:
        """清除执行历史"""
        self._execution_history.clear()
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, type={self.node_type})"


class PlannerNode(BaseNode):
    """
    Planner 节点：基于 LangGraph 的规划工作流
    配置包含：图数据库名称和事件名称
    """
    
    def __init__(self, name: str, config: Dict[str, Any], operator_log: Optional[OperatorLog] = None):
        super().__init__(name, NodeType.Planner, config, operator_log)
        self.planner_config = PlannerConfig(**config)
    
    def validate_config(self) -> bool:
        """验证 Planner 配置"""
        if not self.planner_config.graph_db_name:
            raise ValueError(f"Planner '{self.name}': graph_db_name is required")
        if not self.planner_config.event_name:
            raise ValueError(f"Planner '{self.name}': event_name is required")
        return True
    
    def build_runnable(self) -> Runnable:
        """构建 Planner 节点的 Runnable"""
        self.validate_config()
        
        def planner_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            执行规划逻辑
            实际应用中应该调用真实的 Planner 工作流
            """
            state_dict = convert_state_to_dict(state)
            
            # 这里应该调用真实的 Planner 工作流
            start_time = time.time()
            try:
                output = {
                    "plan": f"Plan from {self.name} using graph_db={self.planner_config.graph_db_name}, event={self.planner_config.event_name}",
                    "status": "planned"
                }
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                return map_output_to_state(self.name, output, state_dict)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=str(e)
                ))
                raise
        
        return RunnableLambda(planner_func).with_config(tags=[self.name])


class WorkerNode(BaseNode):
    """
    Worker 节点：支持 MCP 和 RAG 两种子类型
    """
    
    def __init__(self, name: str, config: Dict[str, Any], operator_log: Optional[OperatorLog] = None):
        super().__init__(name, NodeType.Worker, config, operator_log)
        self.worker_config = WorkerConfig(**config)
    
    def validate_config(self) -> bool:
        """验证 Worker 配置"""
        if self.worker_config.sub_type.value == "mcp":
            if not self.worker_config.mcp_config:
                raise ValueError(f"Worker '{self.name}': mcp_config is required for MCP type")
        elif self.worker_config.sub_type.value == "rag":
            if not self.worker_config.rag_config:
                raise ValueError(f"Worker '{self.name}': rag_config is required for RAG type")
        return True
    
    def build_runnable(self) -> Runnable:
        """构建 Worker 节点的 Runnable"""
        self.validate_config()
        
        def worker_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """
            执行 Worker 逻辑（MCP 或 RAG）
            """
            state_dict = convert_state_to_dict(state)
            
            start_time = time.time()
            try:
                sub_type = self.worker_config.sub_type.value
                if sub_type == "mcp":
                    output = self._execute_mcp_worker(state_dict)
                elif sub_type == "rag":
                    output = self._execute_rag_worker(state_dict)
                else:
                    raise ValueError(f"Unknown worker sub_type: {sub_type}")
                
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                return map_output_to_state(self.name, output, state_dict)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=str(e)
                ))
                raise
        
        return RunnableLambda(worker_func).with_config(tags=[self.name])
    
    def _execute_mcp_worker(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 MCP 类型的 Worker"""
        # 实际应用中应该调用真实的 MCP 服务
        return {
            "result": f"MCP Worker '{self.name}' executed",
            "mcp_config": self.worker_config.mcp_config
        }
    
    def _execute_rag_worker(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行 RAG 类型的 Worker"""
        # 实际应用中应该调用真实的 RAG 系统
        return {
            "result": f"RAG Worker '{self.name}' executed",
            "rag_config": self.worker_config.rag_config
        }


class ReflectionNode(BaseNode):
    """
    Reflection 节点：反思工作流
    配置包含可选的 RAG 配置
    """
    
    def __init__(self, name: str, config: Dict[str, Any], operator_log: Optional[OperatorLog] = None):
        super().__init__(name, NodeType.Reflection, config, operator_log)
        self.reflection_config = ReflectionConfig(**config)
    
    def validate_config(self) -> bool:
        """验证 Reflection 配置"""
        # Reflection 的 RAG 配置是可选的，所以这里不做强制检查
        return True
    
    def build_runnable(self) -> Runnable:
        """构建 Reflection 节点的 Runnable"""
        self.validate_config()
        
        def reflection_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """执行反思逻辑"""
            state_dict = convert_state_to_dict(state)
            
            start_time = time.time()
            try:
                output = {
                    "reflection": f"Reflection from {self.name}",
                    "status": "reflected"
                }
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output,
                    execution_time_ms=execution_time
                ))
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                return map_output_to_state(self.name, output, state_dict)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=str(e)
                ))
                raise
        
        return RunnableLambda(reflection_func).with_config(tags=[self.name])


class AgentNode(BaseNode):
    """
    Agent 节点：运行时动态编译的工作流
    配置包含引用的工作流 ID
    """
    
    def __init__(
        self, 
        name: str, 
        config: Dict[str, Any], 
        operator_log: Optional[OperatorLog] = None,
        workflow_registry: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, NodeType.Agent, config, operator_log)
        self.agent_config = AgentConfig(**config)
        self.workflow_registry = workflow_registry or {}
    
    def validate_config(self) -> bool:
        """验证 Agent 配置"""
        if not self.agent_config.workflow_id:
            raise ValueError(f"Agent '{self.name}': workflow_id is required")
        if self.agent_config.workflow_id not in self.workflow_registry:
            raise ValueError(f"Agent '{self.name}': workflow_id '{self.agent_config.workflow_id}' not found in registry")
        return True
    
    def build_runnable(self) -> Runnable:
        """构建 Agent 节点的 Runnable"""
        self.validate_config()
        
        def agent_func(state: Dict[str, Any]) -> Dict[str, Any]:
            """执行动态工作流"""
            state_dict = convert_state_to_dict(state)
            
            start_time = time.time()
            try:
                # 从注册表中获取子工作流
                sub_workflow = self.workflow_registry.get(self.agent_config.workflow_id)
                if not sub_workflow:
                    raise ValueError(f"Workflow '{self.agent_config.workflow_id}' not found")
                
                # 执行子工作流
                output = sub_workflow.invoke(state_dict)
                
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data=output if isinstance(output, dict) else {"result": output},
                    execution_time_ms=execution_time
                ))
                # 使用 map_output_to_state 将输出映射到状态更新
                # 采用 Dify 风格，为输出添加 {node_name}_result 字段
                output_dict = output if isinstance(output, dict) else {"result": output}
                return map_output_to_state(self.name, output_dict, state_dict)
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                self.log_execution(ExecutionLog(
                    node_name=self.name,
                    node_type=self.node_type,
                    input_data=state_dict,
                    output_data={},
                    execution_time_ms=execution_time,
                    error=str(e)
                ))
                raise
        
        return RunnableLambda(agent_func).with_config(tags=[self.name])


# --- 节点工厂函数 ---

def create_node(
    definition: NodeDefinition,
    operator_log: Optional[OperatorLog] = None,
    workflow_registry: Optional[Dict[str, Any]] = None
) -> BaseNode:
    """
    统一的节点工厂函数
    根据节点定义创建对应的节点实例
    
    Args:
        definition: 节点定义
        operator_log: 操作符日志
        workflow_registry: 工作流注册表（用于 Agent 节点）
    
    Returns:
        BaseNode: 创建的节点实例
        
    Raises:
        ValueError: 不支持的节点类型
    """
    node_type = definition.type
    
    # 如果没有提供 operator_log，创建一个默认的
    if not operator_log:
        operator_log = OperatorLog(
            node_name=definition.name,
            input_schema={},  # 默认空 schema
            output_schema={}
        )
    
    if node_type == NodeType.Planner:
        return PlannerNode(definition.name, definition.config, operator_log)
    elif node_type == NodeType.Worker:
        return WorkerNode(definition.name, definition.config, operator_log)
    elif node_type == NodeType.Reflection:
        return ReflectionNode(definition.name, definition.config, operator_log)
    elif node_type == NodeType.Agent:
        return AgentNode(definition.name, definition.config, operator_log, workflow_registry)
    elif node_type == NodeType.LLM:
        raise NotImplementedError(f"Node type '{node_type}' is not yet implemented")
    elif node_type == NodeType.Tool:
        raise NotImplementedError(f"Node type '{node_type}' is not yet implemented")
    else:
        raise ValueError(f"Unknown node type: {node_type}")
