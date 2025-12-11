"""
API 数据模型定义

包含所有 FastAPI 接口所需的请求和响应模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime


# ==================== 工作流配置相关 ====================

class NodeDefinitionRequest(BaseModel):
    """节点定义请求"""
    name: str = Field(..., description="节点名称")
    type: str = Field(..., description="节点类型: planner, worker, reflection, agent")
    config: Dict[str, Any] = Field(..., description="节点配置")


class EdgeDefinitionRequest(BaseModel):
    """边定义请求"""
    source: str = Field(..., description="源节点名称")
    target: str = Field(..., description="目标节点名称")
    condition: Optional[str] = Field(None, description="条件路由键名")


class StateFieldRequest(BaseModel):
    """状态字段定义请求"""
    type: str = Field(..., description="字段类型: str, int, float, bool, dict, list")
    description: str = Field("", description="字段描述")
    default: Optional[Any] = Field(None, description="默认值")


class WorkflowCreateRequest(BaseModel):
    """工作流创建请求"""
    workflow_id: str = Field(..., description="工作流唯一ID")
    nodes: List[NodeDefinitionRequest] = Field(..., description="节点列表")
    edges: List[EdgeDefinitionRequest] = Field(..., description="边列表")
    state_schema: Dict[str, StateFieldRequest] = Field(..., description="状态字段定义")
    entry_point: str = Field(..., description="入口节点名称")


# ==================== 工作流执行相关 ====================

class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    workflow_id: str = Field(..., description="工作流ID")
    input_data: Dict[str, Any] = Field(..., description="输入数据")


# ==================== API 响应相关 ====================

class WorkflowResponse(BaseModel):
    """工作流操作响应"""
    workflow_id: str
    status: str
    message: str
    data: Optional[Any] = None


class WorkflowListResponse(BaseModel):
    """工作流列表响应"""
    total: int
    workflows: List[str]
    timestamp: str


class WorkflowDetailResponse(BaseModel):
    """工作流详情响应"""
    workflow_id: str
    entry_point: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    state_fields: Dict[str, Dict[str, Any]]


class WorkflowExecuteResponse(BaseModel):
    """工作流执行响应"""
    status: str
    workflow_id: str
    message: str
    result: Dict[str, Any]
    timestamp: str


class OperatorLogSchema(BaseModel):
    """操作符日志字段定义"""
    type: str
    description: str


class OperatorLogResponse(BaseModel):
    """操作符日志响应"""
    workflow_id: str
    total_nodes: int
    operator_logs: Dict[str, Dict[str, Dict[str, OperatorLogSchema]]]


class ExecutionLogEntry(BaseModel):
    """执行日志条目"""
    node_name: str
    node_type: str
    timestamp: str
    execution_time_ms: float
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error: Optional[str] = None


class ExecutionHistoryResponse(BaseModel):
    """执行历史响应"""
    workflow_id: str
    total_logs: int
    logs: List[ExecutionLogEntry]


class WorkflowLogsResponse(BaseModel):
    """完整工作流日志响应"""
    workflow_id: str
    operator_logs: Dict[str, Dict[str, Dict[str, OperatorLogSchema]]]
    execution_history: List[ExecutionLogEntry]
    total_executions: int
    timestamp: str


class NodeExecutionHistoryResponse(BaseModel):
    """节点执行历史响应"""
    workflow_id: str
    node_name: str
    total_logs: int
    logs: List[ExecutionLogEntry]


class ApiInfoResponse(BaseModel):
    """API 信息响应"""
    name: str
    version: str
    description: str
    endpoints: Dict[str, List[str]]


class ErrorResponse(BaseModel):
    """错误响应"""
    status: str = "error"
    message: str
    timestamp: str


class SuccessResponse(BaseModel):
    """成功响应"""
    status: str = "success"
    message: str
    timestamp: str
