"""
业务逻辑层 - 工作流服务

处理工作流的创建、执行、查询等业务逻辑
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import sys
sys.path.insert(0, '/Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/dynamic-langgraph/advance_aiops_v2')

from workflow.models import (
    WorkflowDefinition, NodeDefinition, EdgeDefinition, StateFieldSchema,
    NodeType
)
from workflow.graph_builder import WorkflowRegistry
from .api_schema import (
    WorkflowCreateRequest, WorkflowExecuteRequest,
    NodeDefinitionRequest, EdgeDefinitionRequest, StateFieldRequest
)


class WorkflowService:
    """工作流服务类 - 处理所有业务逻辑"""
    
    def __init__(self):
        """初始化服务"""
        self.registry = WorkflowRegistry()
    
    # ==================== 工作流管理 ====================
    
    def create_workflow(self, request: WorkflowCreateRequest) -> Dict[str, Any]:
        """
        创建工作流
        
        Args:
            request: 工作流创建请求
            
        Returns:
            包含创建结果的字典
        """
        try:
            # 构建状态字段定义
            state_schema = {
                field_name: StateFieldSchema(
                    type=field_def.type,
                    description=field_def.description,
                    default=field_def.default
                )
                for field_name, field_def in request.state_schema.items()
            }
            
            # 构建节点定义
            nodes = [
                NodeDefinition(
                    name=node.name,
                    type=NodeType(node.type),
                    config=node.config
                )
                for node in request.nodes
            ]
            
            # 构建边定义
            edges = [
                EdgeDefinition(
                    source=edge.source,
                    target=edge.target,
                    condition=edge.condition
                )
                for edge in request.edges
            ]
            
            # 创建工作流定义
            workflow_def = WorkflowDefinition(
                workflow_id=request.workflow_id,
                entry_point=request.entry_point,
                state_schema=state_schema,
                nodes=nodes,
                edges=edges
            )
            
            # 注册工作流
            self.registry.register_workflow(workflow_def)
            
            return {
                "status": "success",
                "workflow_id": request.workflow_id,
                "message": f"工作流 '{request.workflow_id}' 创建成功",
                "data": {
                    "nodes_count": len(nodes),
                    "edges_count": len(edges),
                    "entry_point": request.entry_point
                }
            }
        except Exception as e:
            raise ValueError(f"创建工作流失败: {str(e)}")
    
    def list_workflows(self) -> Dict[str, Any]:
        """
        列出所有工作流
        
        Returns:
            包含工作流列表的字典
        """
        workflows = self.registry.list_workflows()
        return {
            "total": len(workflows),
            "workflows": workflows,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流详情
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流详情
        """
        definition = self.registry.get_workflow_definition(workflow_id)
        if not definition:
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        return {
            "workflow_id": workflow_id,
            "entry_point": definition.entry_point,
            "nodes": [
                {
                    "name": node.name,
                    "type": node.type.value,
                    "config": node.config
                }
                for node in definition.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "condition": edge.condition
                }
                for edge in definition.edges
            ],
            "state_fields": {
                field_name: {
                    "type": field_schema.type,
                    "description": field_schema.description,
                    "default": field_schema.default
                }
                for field_name, field_schema in definition.state_schema.items()
            }
        }
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """
        删除工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            删除结果
        """
        if not self.registry.has_workflow(workflow_id):
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        self.registry.unregister_workflow(workflow_id)
        return {
            "status": "success",
            "message": f"工作流 '{workflow_id}' 已删除",
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== 工作流执行 ====================
    
    def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            input_data: 输入数据
            
        Returns:
            执行结果
        """
        if not self.registry.has_workflow(workflow_id):
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        result = self.registry.execute_workflow(workflow_id, input_data)
        
        return {
            "status": "success",
            "workflow_id": workflow_id,
            "message": "工作流执行完成",
            "result": dict(result),
            "timestamp": datetime.now().isoformat()
        }
    
    # ==================== 工作流日志 ====================
    
    def get_workflow_logs(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流的完整日志
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            完整日志
        """
        definition = self.registry.get_workflow_definition(workflow_id)
        if not definition:
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        # 获取操作符日志
        op_logs = self.registry.get_operator_logs(workflow_id)
        operator_logs = {
            node_name: {
                "input_schema": {
                    field_name: {
                        "type": field_schema.type,
                        "description": field_schema.description
                    }
                    for field_name, field_schema in op_log.input_schema.items()
                },
                "output_schema": {
                    field_name: {
                        "type": field_schema.type,
                        "description": field_schema.description
                    }
                    for field_name, field_schema in op_log.output_schema.items()
                }
            }
            for node_name, op_log in op_logs.items()
        }
        
        # 获取执行历史
        exec_history = self.registry.get_execution_history(workflow_id)
        execution_logs = [
            {
                "node_name": log.node_name,
                "node_type": log.node_type.value,
                "timestamp": log.timestamp.isoformat(),
                "execution_time_ms": log.execution_time_ms,
                "input_data": log.input_data,
                "output_data": log.output_data,
                "error": log.error
            }
            for log in exec_history
        ]
        
        return {
            "workflow_id": workflow_id,
            "operator_logs": operator_logs,
            "execution_history": execution_logs,
            "total_executions": len(execution_logs),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_execution_history(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取执行历史
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            执行历史
        """
        if not self.registry.has_workflow(workflow_id):
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        exec_history = self.registry.get_execution_history(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "total_logs": len(exec_history),
            "logs": [
                {
                    "node_name": log.node_name,
                    "node_type": log.node_type.value,
                    "timestamp": log.timestamp.isoformat(),
                    "execution_time_ms": log.execution_time_ms,
                    "input_data": log.input_data,
                    "output_data": log.output_data,
                    "error": log.error
                }
                for log in exec_history
            ]
        }
    
    def get_operator_logs(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取操作符日志
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            操作符日志
        """
        if not self.registry.has_workflow(workflow_id):
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        op_logs = self.registry.get_operator_logs(workflow_id)
        
        return {
            "workflow_id": workflow_id,
            "total_nodes": len(op_logs),
            "operator_logs": {
                node_name: {
                    "input_schema": {
                        field_name: {
                            "type": field_schema.type,
                            "description": field_schema.description
                        }
                        for field_name, field_schema in op_log.input_schema.items()
                    },
                    "output_schema": {
                        field_name: {
                            "type": field_schema.type,
                            "description": field_schema.description
                        }
                        for field_name, field_schema in op_log.output_schema.items()
                    }
                }
                for node_name, op_log in op_logs.items()
            }
        }
    
    def get_node_execution_history(self, workflow_id: str, node_name: str) -> Dict[str, Any]:
        """
        获取节点执行历史
        
        Args:
            workflow_id: 工作流ID
            node_name: 节点名称
            
        Returns:
            节点执行历史
        """
        if not self.registry.has_workflow(workflow_id):
            raise ValueError(f"工作流 '{workflow_id}' 不存在")
        
        node_history = self.registry.get_node_execution_history(workflow_id, node_name)
        
        return {
            "workflow_id": workflow_id,
            "node_name": node_name,
            "total_logs": len(node_history),
            "logs": [
                {
                    "node_name": log.node_name,
                    "node_type": log.node_type.value,
                    "timestamp": log.timestamp.isoformat(),
                    "execution_time_ms": log.execution_time_ms,
                    "input_data": log.input_data,
                    "output_data": log.output_data,
                    "error": log.error
                }
                for log in node_history
            ]
        }


# 全局服务实例
workflow_service = WorkflowService()
