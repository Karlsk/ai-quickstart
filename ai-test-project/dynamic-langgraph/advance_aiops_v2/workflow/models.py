from pydantic import BaseModel, Field, create_model
from typing import Dict, Any, List, Optional, Type, Callable, Literal
from enum import Enum
from langchain_core.runnables import Runnable, RunnableLambda
from langgraph.graph import StateGraph, END
from datetime import datetime
import json


# --- 工作流模型更新 ---

class NodeType(str, Enum):
    """更新节点类型，包含实际的 LangChain/LangGraph 组件"""
    Planner = "plan"
    Worker = "worker"
    Reflection = "reflection"
    Agent = "agent"
    LLM = "llm"
    Tool = "tool"


class WorkerSubType(str, Enum):
    """Worker 节点的子类型"""
    MCP = "mcp"
    RAG = "rag"


class NodeDefinition(BaseModel):
    name: str = Field(..., description="节点名称")
    type: NodeType = Field(..., description="节点类型")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点的实例化配置")


class EdgeDefinition(BaseModel):
    source: str = Field(..., description="源节点名称")
    target: str = Field(..., description="目标节点名称")
    condition: Optional[str] = Field(None, description="条件路由键名")


class StateFieldSchema(BaseModel):
    """定义状态字段的 Schema"""
    type: str = Field(..., description="字段类型，例如: 'str', 'int', 'List[str]'")
    default: Any = Field(None, description="字段默认值")
    description: str = Field("", description="字段描述")

class PlannerConfig(BaseModel):
    """Planner 节点配置"""
    graph_db_name: str = Field(..., description="图数据库名称")
    event_name: str = Field(..., description="事件名称")


class WorkerConfig(BaseModel):
    """Worker 节点配置（MCP 或 RAG）"""
    sub_type: WorkerSubType = Field(..., description="Worker 子类型：MCP 或 RAG")
    # MCP 配置
    mcp_config: Optional[Dict[str, Any]] = Field(None, description="MCP 服务器配置")
    # RAG 配置
    rag_config: Optional[Dict[str, Any]] = Field(None, description="RAG 配置")


class ReflectionConfig(BaseModel):
    """Reflection 节点配置"""
    rag_config: Optional[Dict[str, Any]] = Field(None, description="可选的 RAG 配置")


class AgentConfig(BaseModel):
    """Agent 节点配置（运行时动态编译的工作流）"""
    workflow_id: str = Field(..., description="引用的工作流 ID")


class ExecutionLog(BaseModel):
    """单次节点执行的详细日志"""
    node_name: str = Field(..., description="节点名称")
    node_type: NodeType = Field(..., description="节点类型")
    timestamp: datetime = Field(default_factory=datetime.now, description="执行时间")
    input_data: Dict[str, Any] = Field(..., description="输入数据")
    output_data: Dict[str, Any] = Field(..., description="输出数据")
    execution_time_ms: float = Field(..., description="执行耗时（毫秒）")
    error: Optional[str] = Field(None, description="执行错误信息")


class OperatorLog(BaseModel):
    """操作符日志：记录节点的输入输出 schema"""
    node_name: str = Field(..., description="节点名称")
    input_schema: Dict[str, StateFieldSchema] = Field(..., description="操作符输入的状态字段定义")
    output_schema: Dict[str, StateFieldSchema] = Field(..., description="操作符输出的状态字段定义")


class WorkflowDefinition(BaseModel):
    """整个工作流的定义"""
    workflow_id: str = Field(..., description="工作流唯一ID")
    nodes: List[NodeDefinition] = Field(default_factory=list)
    edges: List[EdgeDefinition] = Field(default_factory=list)
    entry_point: str = Field(..., description="唯一的入口节点名称")
    state_schema: Dict[str, StateFieldSchema] = Field(..., description="工作流状态的字段定义")
    operator_logs: Dict[str, OperatorLog] = Field(default_factory=dict, description="每个节点的操作符日志")
    execution_history: List[ExecutionLog] = Field(default_factory=list, description="工作流执行历史")
