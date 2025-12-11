"""
集成测试：验证动态工作流编排系统的核心功能
"""

import pytest
from workflow import (
    NodeType,
    WorkerSubType,
    NodeDefinition,
    EdgeDefinition,
    StateFieldSchema,
    PlannerConfig,
    WorkerConfig,
    ReflectionConfig,
    AgentConfig,
    OperatorLog,
    WorkflowDefinition,
    WorkflowRegistry,
)


class TestNodeDefinition:
    """测试节点定义"""
    
    def test_planner_node_definition(self):
        """测试 Planner 节点定义"""
        node = NodeDefinition(
            name="planner",
            type=NodeType.Planner,
            config={
                "graph_db_name": "test_db",
                "event_name": "test_event"
            }
        )
        assert node.name == "planner"
        assert node.type == NodeType.Planner
    
    def test_worker_mcp_node_definition(self):
        """测试 MCP Worker 节点定义"""
        node = NodeDefinition(
            name="mcp_worker",
            type=NodeType.Worker,
            config={
                "sub_type": "mcp",
                "mcp_config": {"server": "localhost", "port": 8000}
            }
        )
        assert node.name == "mcp_worker"
        assert node.type == NodeType.Worker
    
    def test_worker_rag_node_definition(self):
        """测试 RAG Worker 节点定义"""
        node = NodeDefinition(
            name="rag_worker",
            type=NodeType.Worker,
            config={
                "sub_type": "rag",
                "rag_config": {"model": "gpt-4", "retriever": "vector_db"}
            }
        )
        assert node.name == "rag_worker"
        assert node.type == NodeType.Worker
    
    def test_reflection_node_definition(self):
        """测试 Reflection 节点定义"""
        node = NodeDefinition(
            name="reflection",
            type=NodeType.Reflection,
            config={
                "rag_config": {"kb_id": "kb_123"}
            }
        )
        assert node.name == "reflection"
        assert node.type == NodeType.Reflection
    
    def test_agent_node_definition(self):
        """测试 Agent 节点定义"""
        node = NodeDefinition(
            name="sub_agent",
            type=NodeType.Agent,
            config={
                "workflow_id": "workflow_v2"
            }
        )
        assert node.name == "sub_agent"
        assert node.type == NodeType.Agent


class TestEdgeDefinition:
    """测试边定义"""
    
    def test_normal_edge(self):
        """测试普通边"""
        edge = EdgeDefinition(
            source="node1",
            target="node2"
        )
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.condition is None
    
    def test_conditional_edge(self):
        """测试条件边"""
        edge = EdgeDefinition(
            source="route_node",
            target="next_node",
            condition="route_type"
        )
        assert edge.source == "route_node"
        assert edge.target == "next_node"
        assert edge.condition == "route_type"


class TestStateFieldSchema:
    """测试状态字段定义"""
    
    def test_string_field(self):
        """测试字符串字段"""
        field = StateFieldSchema(
            type="str",
            default="",
            description="Input text"
        )
        assert field.type == "str"
        assert field.default == ""
    
    def test_list_field(self):
        """测试列表字段"""
        field = StateFieldSchema(
            type="List[str]",
            default=None,
            description="List of items"
        )
        assert field.type == "List[str]"


class TestWorkflowRegistry:
    """测试工作流注册表"""
    
    def test_simple_workflow_registration(self):
        """测试简单工作流的注册"""
        registry = WorkflowRegistry()
        
        # 定义工作流
        workflow_def = WorkflowDefinition(
            workflow_id="simple_workflow",
            nodes=[
                NodeDefinition(
                    name="start",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "test_db",
                        "event_name": "start"
                    }
                ),
                NodeDefinition(
                    name="end",
                    type=NodeType.Reflection,
                    config={}
                )
            ],
            edges=[
                EdgeDefinition(source="start", target="end"),
                EdgeDefinition(source="end", target="END")
            ],
            entry_point="start",
            state_schema={
                "input": StateFieldSchema(type="str", default="", description="Input"),
                "output": StateFieldSchema(type="str", default="", description="Output")
            }
        )
        
        # 注册工作流
        wf_id = registry.register_workflow(workflow_def)
        assert wf_id == "simple_workflow"
        assert registry.has_workflow("simple_workflow")
    
    def test_workflow_execution(self):
        """测试工作流执行"""
        registry = WorkflowRegistry()
        
        # 定义工作流
        workflow_def = WorkflowDefinition(
            workflow_id="exec_workflow",
            nodes=[
                NodeDefinition(
                    name="planner",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "test_db",
                        "event_name": "plan"
                    }
                ),
                NodeDefinition(
                    name="worker",
                    type=NodeType.Worker,
                    config={
                        "sub_type": "rag",
                        "rag_config": {"model": "test"}
                    }
                )
            ],
            edges=[
                EdgeDefinition(source="planner", target="worker"),
                EdgeDefinition(source="worker", target="END")
            ],
            entry_point="planner",
            state_schema={
                "query": StateFieldSchema(type="str", default="", description="Query"),
                "plan": StateFieldSchema(type="str", default="", description="Plan")
            }
        )
        
        # 注册工作流
        registry.register_workflow(workflow_def)
        
        # 执行工作流
        result = registry.execute_workflow("exec_workflow", {"query": "test query"})
        assert result is not None
    
    def test_workflow_list(self):
        """测试工作流列表"""
        registry = WorkflowRegistry()
        
        # 创建多个工作流
        for i in range(3):
            workflow_def = WorkflowDefinition(
                workflow_id=f"workflow_{i}",
                nodes=[
                    NodeDefinition(
                        name="node",
                        type=NodeType.Planner,
                        config={
                            "graph_db_name": f"db_{i}",
                            "event_name": f"event_{i}"
                        }
                    )
                ],
                edges=[],
                entry_point="node",
                state_schema={
                    "data": StateFieldSchema(type="str", default="", description="Data")
                }
            )
            registry.register_workflow(workflow_def)
        
        # 列出所有工作流
        workflows = registry.list_workflows()
        assert len(workflows) == 3
        assert f"workflow_0" in workflows
        assert f"workflow_1" in workflows
        assert f"workflow_2" in workflows
    
    def test_workflow_unregister(self):
        """测试工作流注销"""
        registry = WorkflowRegistry()
        
        workflow_def = WorkflowDefinition(
            workflow_id="temp_workflow",
            nodes=[
                NodeDefinition(
                    name="node",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "db",
                        "event_name": "event"
                    }
                )
            ],
            edges=[],
            entry_point="node",
            state_schema={
                "data": StateFieldSchema(type="str", default="", description="Data")
            }
        )
        
        registry.register_workflow(workflow_def)
        assert registry.has_workflow("temp_workflow")
        
        registry.unregister_workflow("temp_workflow")
        assert not registry.has_workflow("temp_workflow")
    
    def test_registry_stats(self):
        """测试注册表统计"""
        registry = WorkflowRegistry()
        
        # 初始状态
        stats = registry.get_registry_stats()
        assert stats["total_workflows"] == 0
        
        # 添加工作流
        workflow_def = WorkflowDefinition(
            workflow_id="stat_workflow",
            nodes=[
                NodeDefinition(
                    name="node",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "db",
                        "event_name": "event"
                    }
                )
            ],
            edges=[],
            entry_point="node",
            state_schema={
                "data": StateFieldSchema(type="str", default="", description="Data")
            }
        )
        registry.register_workflow(workflow_def)
        
        # 验证统计
        stats = registry.get_registry_stats()
        assert stats["total_workflows"] == 1
        assert "stat_workflow" in stats["workflow_ids"]


class TestComplexWorkflow:
    """测试复杂工作流场景"""
    
    def test_multi_node_workflow(self):
        """测试多节点工作流"""
        registry = WorkflowRegistry()
        
        workflow_def = WorkflowDefinition(
            workflow_id="complex_workflow",
            nodes=[
                NodeDefinition(
                    name="planner",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "graph_db",
                        "event_name": "start"
                    }
                ),
                NodeDefinition(
                    name="mcp_worker",
                    type=NodeType.Worker,
                    config={
                        "sub_type": "mcp",
                        "mcp_config": {"server": "localhost"}
                    }
                ),
                NodeDefinition(
                    name="rag_worker",
                    type=NodeType.Worker,
                    config={
                        "sub_type": "rag",
                        "rag_config": {"model": "gpt-4"}
                    }
                ),
                NodeDefinition(
                    name="reflection",
                    type=NodeType.Reflection,
                    config={
                        "rag_config": {"kb_id": "kb_001"}
                    }
                )
            ],
            edges=[
                EdgeDefinition(source="planner", target="mcp_worker"),
                EdgeDefinition(source="mcp_worker", target="rag_worker"),
                EdgeDefinition(source="rag_worker", target="reflection"),
                EdgeDefinition(source="reflection", target="END")
            ],
            entry_point="planner",
            state_schema={
                "query": StateFieldSchema(type="str", default="", description="User query"),
                "plan": StateFieldSchema(type="str", default="", description="Execution plan"),
                "result": StateFieldSchema(type="str", default="", description="Final result")
            }
        )
        
        # 注册和执行
        registry.register_workflow(workflow_def)
        result = registry.execute_workflow("complex_workflow", {"query": "test"})
        assert result is not None
    
    def test_operator_log_tracking(self):
        """测试操作符日志跟踪"""
        workflow_def = WorkflowDefinition(
            workflow_id="logged_workflow",
            nodes=[
                NodeDefinition(
                    name="node1",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "db",
                        "event_name": "event"
                    }
                )
            ],
            edges=[],
            entry_point="node1",
            state_schema={
                "data": StateFieldSchema(type="str", default="", description="Data")
            },
            operator_logs={
                "node1": OperatorLog(
                    node_name="node1",
                    input_schema={
                        "data": StateFieldSchema(type="str", default="", description="Input data")
                    },
                    output_schema={
                        "result": StateFieldSchema(type="str", default="", description="Output result")
                    }
                )
            }
        )
        
        # 验证操作符日志
        assert "node1" in workflow_def.operator_logs
        log = workflow_def.operator_logs["node1"]
        assert "data" in log.input_schema
        assert "result" in log.output_schema


class TestInvalidDefinitions:
    """测试无效的工作流定义"""
    
    def test_missing_entry_point(self):
        """测试缺少入口点的定义"""
        registry = WorkflowRegistry()
        
        workflow_def = WorkflowDefinition(
            workflow_id="invalid_workflow",
            nodes=[
                NodeDefinition(
                    name="node",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "db",
                        "event_name": "event"
                    }
                )
            ],
            edges=[],
            entry_point="nonexistent",  # 不存在的节点
            state_schema={
                "data": StateFieldSchema(type="str", default="", description="Data")
            }
        )
        
        with pytest.raises(ValueError):
            registry.register_workflow(workflow_def)
    
    def test_invalid_edge_source(self):
        """测试无效的边源节点"""
        registry = WorkflowRegistry()
        
        workflow_def = WorkflowDefinition(
            workflow_id="invalid_edge_workflow",
            nodes=[
                NodeDefinition(
                    name="node1",
                    type=NodeType.Planner,
                    config={
                        "graph_db_name": "db",
                        "event_name": "event"
                    }
                )
            ],
            edges=[
                EdgeDefinition(source="nonexistent", target="node1")
            ],
            entry_point="node1",
            state_schema={
                "data": StateFieldSchema(type="str", default="", description="Data")
            }
        )
        
        with pytest.raises(ValueError):
            registry.register_workflow(workflow_def)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
