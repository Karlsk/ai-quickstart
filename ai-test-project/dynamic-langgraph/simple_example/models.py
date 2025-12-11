from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from enum import Enum


# 假设我们的工作流状态是一个简单的字典
# LangGraph 要求有一个定义的 State (TypedDict 或 Pydantic Model)
# 为了简化，我们使用一个通用的 Dict[str, Any] 作为状态

class NodeType(str, Enum):
    """定义节点类型，例如 'llm', 'tool', 'custom_agent'"""
    LLM = "llm"
    TOOL = "tool"
    CUSTOM = "custom"


class NodeDefinition(BaseModel):
    """定义一个工作流节点"""
    name: str = Field(..., description="节点名称")
    type: NodeType = Field(..., description="节点类型")
    # 实际的可执行对象（如LLM或Tool）的配置，
    # 在实际应用中，你需要根据type来实例化相应的对象
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置参数")
    is_entry: bool = Field(False, description="是否是图的起点")


class EdgeDefinition(BaseModel):
    """定义工作流的边"""
    source: str = Field(..., description="源节点名称")
    target: str = Field(..., description="目标节点名称")
    # 条件路由的键名，如果为空则为普通边
    condition: Optional[str] = Field(None, description="条件路由键名，例如 '__end__' 或下一个节点名")

class WorkflowDefinition(BaseModel):
    """整个工作流的定义"""
    workflow_id: str = Field(..., description="工作流唯一ID")
    nodes: List[NodeDefinition] = Field(default_factory=list)
    edges: List[EdgeDefinition] = Field(default_factory=list)
    entry_point: str = Field(..., description="唯一的入口节点名称")
    # 状态的定义（简化处理，使用通用Dict）
    state_schema: Optional[Dict[str, Any]] = Field(None, description="工作流状态Schema (可选)")