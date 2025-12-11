"""
动态工作流编排系统使用示例
展示如何定义、构建、注册和执行复杂的工作流
"""

from workflow import (
    NodeType,
    WorkerSubType,
    NodeDefinition,
    EdgeDefinition,
    StateFieldSchema,
    OperatorLog,
    WorkflowDefinition,
    WorkflowRegistry,
)


def example_1_simple_planner_workflow():
    """示例1：简单的 Planner 工作流"""
    print("\n" + "="*60)
    print("示例1：简单 Planner 工作流")
    print("="*60)
    
    registry = WorkflowRegistry()
    
    # 定义一个简单的规划工作流
    workflow_def = WorkflowDefinition(
        workflow_id="simple_planner_v1",
        nodes=[
            NodeDefinition(
                name="planner",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "knowledge_graph",
                    "event_name": "task_start"
                }
            )
        ],
        edges=[
            EdgeDefinition(source="planner", target="END")
        ],
        entry_point="planner",
        state_schema={
            "task": StateFieldSchema(type="str", default="", description="任务描述"),
            "plan": StateFieldSchema(type="str", default="", description="执行计划")
        },
        operator_logs={
            "planner": OperatorLog(
                node_name="planner",
                input_schema={
                    "task": StateFieldSchema(type="str", default="", description="输入任务")
                },
                output_schema={
                    "plan": StateFieldSchema(type="str", default="", description="输出计划")
                }
            )
        }
    )
    
    # 注册工作流
    registry.register_workflow(workflow_def)
    
    # 执行工作流
    result = registry.execute_workflow("simple_planner_v1", {
        "task": "分析用户行为数据"
    })
    
    print(f"执行结果: {result}")
    print(f"注册表状态: {registry.get_registry_stats()}")
    print(registry.print_workflow_logs("simple_planner_v1"))



def example_2_multi_worker_workflow():
    """示例2：多个 Worker 的工作流（MCP + RAG）"""
    print("\n" + "="*60)
    print("示例2：多 Worker 工作流（MCP + RAG）")
    print("="*60)
    
    registry = WorkflowRegistry()
    
    # 定义一个复杂的工作流：Planner -> MCP Worker -> RAG Worker -> Reflection
    workflow_def = WorkflowDefinition(
        workflow_id="multi_worker_pipeline_v1",
        nodes=[
            NodeDefinition(
                name="planner",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "workflow_kb",
                    "event_name": "pipeline_start"
                }
            ),
            NodeDefinition(
                name="mcp_executor",
                type=NodeType.Worker,
                config={
                    "sub_type": "mcp",
                    "mcp_config": {
                        "server": "localhost:8080",
                        "timeout": 30
                    }
                }
            ),
            NodeDefinition(
                name="rag_analyzer",
                type=NodeType.Worker,
                config={
                    "sub_type": "rag",
                    "rag_config": {
                        "model": "gpt-4",
                        "retriever": "pinecone",
                        "kb_id": "kb_production"
                    }
                }
            ),
            NodeDefinition(
                name="reflection",
                type=NodeType.Reflection,
                config={
                    "rag_config": {
                        "kb_id": "kb_reflection"
                    }
                }
            )
        ],
        edges=[
            EdgeDefinition(source="planner", target="mcp_executor"),
            EdgeDefinition(source="mcp_executor", target="rag_analyzer"),
            EdgeDefinition(source="rag_analyzer", target="reflection"),
            EdgeDefinition(source="reflection", target="END")
        ],
        entry_point="planner",
        state_schema={
            "input": StateFieldSchema(type="str", default="", description="用户输入"),
            "plan": StateFieldSchema(type="str", default="", description="执行计划"),
            "mcp_result": StateFieldSchema(type="str", default="", description="MCP执行结果"),
            "rag_analysis": StateFieldSchema(type="str", default="", description="RAG分析结果"),
            "final_output": StateFieldSchema(type="str", default="", description="最终输出")
        }
    )
    
    # 注册工作流
    registry.register_workflow(workflow_def)
    
    # 执行工作流
    result = registry.execute_workflow("multi_worker_pipeline_v1", {
        "input": "分析这个客户数据集的特征"
    })
    
    print(f"执行结果: {result}")
    print(registry.get_registry_stats())
    print(registry.print_workflow_logs("multi_worker_pipeline_v1"))


def example_3_conditional_routing():
    """示例3：条件路由工作流"""
    print("\n" + "="*60)
    print("示例3：条件路由工作流")
    print("="*60)
    
    registry = WorkflowRegistry()
    
    # 定义一个工作流，支持条件分支
    workflow_def = WorkflowDefinition(
        workflow_id="conditional_router_v1",
        nodes=[
            NodeDefinition(
                name="classifier",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "classifiers",
                    "event_name": "classify"
                }
            ),
            NodeDefinition(
                name="path_a_worker",
                type=NodeType.Worker,
                config={
                    "sub_type": "rag",
                    "rag_config": {"model": "gpt-4"}
                }
            ),
            NodeDefinition(
                name="path_b_worker",
                type=NodeType.Worker,
                config={
                    "sub_type": "mcp",
                    "mcp_config": {"server": "localhost"}
                }
            ),
            NodeDefinition(
                name="merger",
                type=NodeType.Reflection,
                config={
                    "rag_config": {"kb_id": "kb_merge"}
                }
            )
        ],
        edges=[
            EdgeDefinition(source="classifier", target="path_a_worker"),
            EdgeDefinition(source="classifier", target="path_b_worker"),
            EdgeDefinition(source="path_a_worker", target="merger"),
            EdgeDefinition(source="path_b_worker", target="merger"),
            EdgeDefinition(source="merger", target="END")
        ],
        entry_point="classifier",
        state_schema={
            "data": StateFieldSchema(type="str", default="", description="输入数据"),
            "route": StateFieldSchema(type="str", default="", description="路由决策"),
            "result_a": StateFieldSchema(type="str", default="", description="路径A结果"),
            "result_b": StateFieldSchema(type="str", default="", description="路径B结果"),
            "final_result": StateFieldSchema(type="str", default="", description="最终结果")
        }
    )
    
    # 注册工作流
    registry.register_workflow(workflow_def)
    
    # 执行工作流
    result = registry.execute_workflow("conditional_router_v1", {
        "data": "这是一条待分类的数据",
        "route": "path_a_worker"
    })
    
    print(f"执行结果: {result}")


def example_4_nested_agent_workflow():
    """示例4：嵌套的 Agent 工作流（动态编排）"""
    print("\n" + "="*60)
    print("示例4：嵌套 Agent 工作流（动态编排）")
    print("="*60)
    
    registry = WorkflowRegistry()
    
    # 首先定义一个基础工作流
    base_workflow_def = WorkflowDefinition(
        workflow_id="base_workflow_v1",
        nodes=[
            NodeDefinition(
                name="worker",
                type=NodeType.Worker,
                config={
                    "sub_type": "rag",
                    "rag_config": {"model": "gpt-3.5"}
                }
            )
        ],
        edges=[
            EdgeDefinition(source="worker", target="END")
        ],
        entry_point="worker",
        state_schema={
            "query": StateFieldSchema(type="str", default="", description="查询"),
            "response": StateFieldSchema(type="str", default="", description="响应")
        }
    )
    
    # 注册基础工作流
    registry.register_workflow(base_workflow_def)
    
    # 定义一个主工作流，其中包含一个 Agent 节点引用基础工作流
    main_workflow_def = WorkflowDefinition(
        workflow_id="main_workflow_v1",
        nodes=[
            NodeDefinition(
                name="dispatcher",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "dispatcher_kb",
                    "event_name": "dispatch"
                }
            ),
            NodeDefinition(
                name="sub_agent",
                type=NodeType.Agent,
                config={
                    "workflow_id": "base_workflow_v1"  # 引用已注册的工作流
                }
            )
        ],
        edges=[
            EdgeDefinition(source="dispatcher", target="sub_agent"),
            EdgeDefinition(source="sub_agent", target="END")
        ],
        entry_point="dispatcher",
        state_schema={
            "query": StateFieldSchema(type="str", default="", description="用户查询"),
            "plan": StateFieldSchema(type="str", default="", description="分派计划"),
            "final_result": StateFieldSchema(type="str", default="", description="最终结果")
        }
    )
    
    # 注册主工作流
    registry.register_workflow(main_workflow_def)
    
    # 执行主工作流
    result = registry.execute_workflow("main_workflow_v1", {
        "query": "如何使用这个系统？"
    })
    
    print(f"执行结果: {result}")
    print(f"注册表状态: {registry.get_registry_stats()}")


def example_5_workflow_with_logging():
    """示例5：带完整日志跟踪的工作流"""
    print("\n" + "="*60)
    print("示例5：带完整日志跟踪的工作流")
    print("="*60)
    
    registry = WorkflowRegistry()
    
    # 定义一个带详细操作符日志的工作流
    workflow_def = WorkflowDefinition(
        workflow_id="logged_workflow_v1",
        nodes=[
            NodeDefinition(
                name="planner",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "kb",
                    "event_name": "start"
                }
            ),
            NodeDefinition(
                name="executor",
                type=NodeType.Worker,
                config={
                    "sub_type": "rag",
                    "rag_config": {"model": "gpt-4"}
                }
            )
        ],
        edges=[
            EdgeDefinition(source="planner", target="executor"),
            EdgeDefinition(source="executor", target="END")
        ],
        entry_point="planner",
        state_schema={
            "task": StateFieldSchema(type="str", default="", description="任务"),
            "result": StateFieldSchema(type="str", default="", description="结果")
        },
        operator_logs={
            "planner": OperatorLog(
                node_name="planner",
                input_schema={
                    "task": StateFieldSchema(type="str", default="", description="输入任务")
                },
                output_schema={
                    "plan": StateFieldSchema(type="str", default="", description="输出计划")
                }
            ),
            "executor": OperatorLog(
                node_name="executor",
                input_schema={
                    "plan": StateFieldSchema(type="str", default="", description="执行计划")
                },
                output_schema={
                    "result": StateFieldSchema(type="str", default="", description="执行结果")
                }
            )
        }
    )
    
    # 注册工作流
    registry.register_workflow(workflow_def)
    
    # 执行工作流
    result = registry.execute_workflow("logged_workflow_v1", {
        "task": "完成报告分析"
    })
    
    print(f"执行结果: {result}")
    print(f"\n注册表统计:")
    print(f"  总工作流数: {registry.get_registry_stats()['total_workflows']}")
    print(f"  工作流ID列表: {registry.get_registry_stats()['workflow_ids']}")


if __name__ == "__main__":
    print("="*60)
    print("动态工作流编排系统 - 使用示例")
    print("="*60)
    
    try:
        example_1_simple_planner_workflow()
        example_2_multi_worker_workflow()
        example_3_conditional_routing()
        example_4_nested_agent_workflow()
        example_5_workflow_with_logging()
        
        print("\n" + "="*60)
        print("所有示例执行完成！")
        print("="*60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
