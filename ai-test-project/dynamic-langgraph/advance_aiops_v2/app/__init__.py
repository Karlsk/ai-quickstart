"""
app 包 - 工作流 API 应用

包含：
- api_schema: API 数据模型
- service: 业务逻辑层
- routes: API 路由定义
"""

from .service import WorkflowService, workflow_service
from .api_schema import (
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
)

__all__ = [
    'WorkflowService',
    'workflow_service',
    'WorkflowCreateRequest',
    'WorkflowExecuteRequest',
    'WorkflowResponse',
]
