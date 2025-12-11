"""
API 路由定义

包含所有 API 端点的路由定义
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime

from .api_schema import (
    WorkflowCreateRequest, WorkflowExecuteRequest,
    WorkflowResponse, WorkflowListResponse, WorkflowDetailResponse,
    WorkflowExecuteResponse, OperatorLogResponse, ExecutionHistoryResponse,
    WorkflowLogsResponse, NodeExecutionHistoryResponse, ApiInfoResponse
)
from .service import workflow_service


# 创建路由器
router = APIRouter()


# ==================== 基础 API ====================

@router.get("/", response_model=ApiInfoResponse, tags=["基础"])
async def root():
    """根路由 - API 信息"""
    return {
        "name": "动态工作流管理 API",
        "version": "1.0.0",
        "description": "支持创建、配置、执行和监控 LangGraph 工作流",
        "endpoints": {
            "工作流管理": [
                "POST /workflows - 创建工作流",
                "GET /workflows - 列出所有工作流",
                "GET /workflows/{workflow_id} - 查看工作流详情",
                "DELETE /workflows/{workflow_id} - 删除工作流",
            ],
            "工作流执行": [
                "POST /workflows/{workflow_id}/execute - 执行工作流",
            ],
            "工作流日志": [
                "GET /workflows/{workflow_id}/logs - 查看完整日志",
                "GET /workflows/{workflow_id}/execution-history - 查看执行历史",
                "GET /workflows/{workflow_id}/operator-logs - 查看操作符日志",
                "GET /workflows/{workflow_id}/node/{node_name}/execution-history - 查看节点执行历史",
            ]
        }
    }


# ==================== 工作流管理 API ====================

@router.post("/workflows", response_model=WorkflowResponse, tags=["工作流管理"])
async def create_workflow(request: WorkflowCreateRequest):
    """
    创建和注册一个新工作流
    
    示例请求体:
    ```json
    {
        "workflow_id": "my_workflow",
        "entry_point": "planner",
        "state_schema": {
            "input": {"type": "str", "description": "输入查询"},
            "planner_result": {"type": "dict", "default": null}
        },
        "nodes": [
            {
                "name": "planner",
                "type": "planner",
                "config": {"graph_db_name": "kb", "event_name": "start"}
            }
        ],
        "edges": [
            {"source": "planner", "target": "END"}
        ]
    }
    ```
    """
    try:
        return await _handle_service_call(
            lambda: workflow_service.create_workflow(request)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/workflows", response_model=WorkflowListResponse, tags=["工作流管理"])
async def list_workflows():
    """列出所有已注册的工作流"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.list_workflows()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}", response_model=WorkflowDetailResponse, tags=["工作流管理"])
async def get_workflow(workflow_id: str):
    """获取工作流的详细信息"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.get_workflow(workflow_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/workflows/{workflow_id}", tags=["工作流管理"])
async def delete_workflow(workflow_id: str):
    """删除一个工作流"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.delete_workflow(workflow_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工作流执行 API ====================

@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecuteResponse, tags=["工作流执行"])
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """
    执行一个工作流
    
    示例请求体:
    ```json
    {
        "workflow_id": "my_workflow",
        "input_data": {
            "input": "这是一个测试查询"
        }
    }
    ```
    """
    try:
        # 验证 workflow_id 一致性
        if request.workflow_id != workflow_id:
            raise ValueError("请求体中的 workflow_id 与 URL 中的 workflow_id 不一致")
        
        return await _handle_service_call(
            lambda: workflow_service.execute_workflow(workflow_id, request.input_data)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工作流日志 API ====================

@router.get("/workflows/{workflow_id}/logs", response_model=WorkflowLogsResponse, tags=["工作流日志"])
async def get_workflow_logs(workflow_id: str):
    """获取工作流的完整日志（包括操作符日志和执行历史）"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.get_workflow_logs(workflow_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/execution-history", response_model=ExecutionHistoryResponse, tags=["工作流日志"])
async def get_execution_history(workflow_id: str):
    """获取工作流的执行历史"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.get_execution_history(workflow_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/operator-logs", response_model=OperatorLogResponse, tags=["工作流日志"])
async def get_operator_logs(workflow_id: str):
    """获取工作流的操作符日志（节点的输入输出 Schema）"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.get_operator_logs(workflow_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/{workflow_id}/node/{node_name}/execution-history", 
            response_model=NodeExecutionHistoryResponse, tags=["工作流日志"])
async def get_node_execution_history(workflow_id: str, node_name: str):
    """获取特定节点的执行历史"""
    try:
        return await _handle_service_call(
            lambda: workflow_service.get_node_execution_history(workflow_id, node_name)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 工具函数 ====================

async def _handle_service_call(service_func):
    """处理服务调用的通用函数"""
    try:
        return service_func()
    except Exception as e:
        raise
