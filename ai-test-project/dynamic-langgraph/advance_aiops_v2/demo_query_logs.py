"""
演示如何查询工作流的 OperatorLog 和 ExecutionLog
"""

from workflow import *


def demo_query_logs():
    """演示查询工作流日志的各种方式"""
    
    print("\n" + "="*80)
    print("📚 工作流日志查询演示")
    print("="*80)
    
    # 1. 创建工作流定义
    workflow_def = WorkflowDefinition(
        workflow_id="demo_workflow",
        nodes=[
            NodeDefinition(
                name="planner",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "knowledge_graph",
                    "event_name": "start"
                }
            ),
            NodeDefinition(
                name="worker",
                type=NodeType.Worker,
                config={
                    "sub_type": "rag",
                    "rag_config": {"model": "gpt-4"}
                }
            )
        ],
        edges=[
            EdgeDefinition(source="planner", target="worker"),
            EdgeDefinition(source="worker", target="END")
        ],
        entry_point="planner",
        state_schema={
            "query": StateFieldSchema(type="str", default="", description="用户查询"),
            "result": StateFieldSchema(type="str", default="", description="查询结果")
        },
        # operator_logs={
        #     "planner": OperatorLog(
        #         node_name="planner",
        #         input_schema={
        #             "query": StateFieldSchema(type="str", default="", description="输入查询")
        #         },
        #         output_schema={
        #             "plan": StateFieldSchema(type="str", default="", description="输出计划")
        #         }
        #     ),
        #     "worker": OperatorLog(
        #         node_name="worker",
        #         input_schema={
        #             "plan": StateFieldSchema(type="str", default="", description="执行计划")
        #         },
        #         output_schema={
        #             "result": StateFieldSchema(type="str", default="", description="执行结果")
        #         }
        #     )
        # }
    )
    
    # 2. 创建注册表和注册工作流
    registry = WorkflowRegistry()
    registry.register_workflow(workflow_def)
    
    # 3. 执行工作流
    print("\n\n▶️  执行工作流...")
    result = registry.execute_workflow("demo_workflow", {"query": "如何使用这个系统？"})
    print(f"✅ 执行完成，结果: {result}")
    
    # ============================================================
    # 查询接口演示
    # ============================================================
    
    print("\n\n" + "="*80)
    print("🔍 查询接口演示")
    print("="*80)
    
    # 1. 获取工作流定义
    print("\n\n1️⃣  获取工作流定义:")
    print("-" * 80)
    definition = registry.get_workflow_definition("demo_workflow")
    print(f"工作流 ID: {definition.workflow_id}")
    print(f"节点数: {len(definition.nodes)}")
    print(f"节点列表: {[node.name for node in definition.nodes]}")
    
    # 2. 获取所有 OperatorLog
    print("\n\n2️⃣  获取所有 OperatorLog:")
    print("-" * 80)
    operator_logs = registry.get_operator_logs("demo_workflow")
    print(f"有 {len(operator_logs)} 个节点的 OperatorLog：")
    for node_name, op_log in operator_logs.items():
        print(f"\n  📍 节点: {node_name}")
        print(f"     输入字段: {list(op_log.input_schema.keys())}")
        print(f"     输出字段: {list(op_log.output_schema.keys())}")
    
    # 3. 获取特定节点的 OperatorLog
    print("\n\n3️⃣  获取特定节点的 OperatorLog (planner 节点):")
    print("-" * 80)
    planner_op_log = registry.get_operator_log_by_node("demo_workflow", "planner")
    if planner_op_log:
        print(f"节点 'planner' 的 OperatorLog:")
        print(f"  输入 Schema:")
        for field_name, field_schema in planner_op_log.input_schema.items():
            print(f"    - {field_name}: {field_schema.type}")
        print(f"  输出 Schema:")
        for field_name, field_schema in planner_op_log.output_schema.items():
            print(f"    - {field_name}: {field_schema.type}")
    
    # 4. 获取所有 ExecutionLog
    print("\n\n4️⃣  获取所有 ExecutionLog:")
    print("-" * 80)
    execution_history = registry.get_execution_history("demo_workflow")
    print(f"总共有 {len(execution_history)} 条执行日志：")
    for idx, log in enumerate(execution_history, 1):
        print(f"\n  [{idx}] {log.node_name}:")
        print(f"      类型: {log.node_type.value}")
        print(f"      耗时: {log.execution_time_ms:.2f}ms")
        print(f"      时间: {log.timestamp}")
        if log.error:
            print(f"      ❌ 错误: {log.error}")
        else:
            print(f"      ✅ 成功")
    
    # 5. 获取特定节点的 ExecutionLog
    print("\n\n5️⃣  获取特定节点的 ExecutionLog (worker 节点):")
    print("-" * 80)
    worker_history = registry.get_node_execution_history("demo_workflow", "worker")
    print(f"节点 'worker' 的执行日志数: {len(worker_history)}")
    for idx, log in enumerate(worker_history, 1):
        print(f"\n  [{idx}] 执行详情:")
        print(f"      时间: {log.timestamp}")
        print(f"      耗时: {log.execution_time_ms:.2f}ms")
        print(f"      输入: {log.input_data}")
        print(f"      输出: {log.output_data}")
    
    # 6. 获取节点对象（便于直接调用方法）
    print("\n\n6️⃣  获取节点对象:")
    print("-" * 80)
    planner_node = registry.get_node_by_name("demo_workflow", "planner")
    if planner_node:
        print(f"节点对象: {planner_node}")
        print(f"节点名称: {planner_node.name}")
        print(f"节点类型: {planner_node.node_type.value}")
        # 可以直接调用节点方法
        print(f"节点执行历史: {len(planner_node.get_execution_history())} 条记录")
    
    # 7. 打印完整的工作流日志
    print("\n\n7️⃣  打印完整工作流日志 (格式化输出):")
    print("-" * 80)
    registry.print_workflow_logs("demo_workflow")
    
    # 8. 查询统计信息
    print("\n\n8️⃣  查询注册表统计信息:")
    print("-" * 80)
    stats = registry.get_registry_stats()
    print(f"总工作流数: {stats['total_workflows']}")
    print(f"工作流列表: {stats['workflow_ids']}")
    
    print("\n\n✅ 所有查询演示完成！\n")


if __name__ == "__main__":
    demo_query_logs()
