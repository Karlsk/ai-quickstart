from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


# --- 工作流模型更新 ---

class NodeType(str, Enum):
    """更新节点类型，包含实际的 LangChain/LangGraph 组件"""
    LLM = "llm"
    TOOL = "tool"
    CUSTOM = "custom"


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


class WorkflowDefinition(BaseModel):
    """整个工作流的定义"""
    workflow_id: str = Field(..., description="工作流唯一ID")
    nodes: List[NodeDefinition] = Field(default_factory=list)
    edges: List[EdgeDefinition] = Field(default_factory=list)
    entry_point: str = Field(..., description="唯一的入口节点名称")
    # **核心更新：** 状态定义现在是一个完整的字段 Schema
    state_schema: Dict[str, StateFieldSchema] = Field(..., description="工作流状态的字段定义")