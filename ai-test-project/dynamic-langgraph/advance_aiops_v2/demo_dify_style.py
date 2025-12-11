"""
演示 Dify 风格的节点输出引用机制

在这个演示中，我们展示如何：
1. 通过 {node_name}_result 字段访问前面节点的输出
2. 灵活地在后续节点中使用前面节点的数据
3. 类似 Dify 的工作流编排方式
"""

from workflow.models import (
    WorkflowDefinition, NodeDefinition, EdgeDefinition, StateFieldSchema, NodeType, WorkerSubType
)
from workflow.graph_builder import WorkflowRegistry


def main():
    print("\n" + "="*80)
    print("📚 Dify 风格节点输出引用演示")
    print("="*80 + "\n")
    
    # 创建注册表
    registry = WorkflowRegistry()
    
    # 创建工作流定义
    workflow = WorkflowDefinition(
        workflow_id="dify_demo",
        entry_point="planner",
        state_schema={
            "input": StateFieldSchema(type="str", description="输入查询"),
            # 定义节点输出字段 (Dify 风格)
            # 不幸的是 LangGraph 需要提前定义所有会修改的字段
            "planner_result": StateFieldSchema(type="dict", default=None),
            "executor_result": StateFieldSchema(type="dict", default=None),
            "reflector_result": StateFieldSchema(type="dict", default=None),
        },
        nodes=[
            # 节点 1: Planner - 规划
            NodeDefinition(
                name="planner",
                type=NodeType.Planner,
                config={
                    "graph_db_name": "knowledge_graph",
                    "event_name": "plan_event"
                }
            ),
            # 节点 2: Worker - 执行
            # 注意：这个节点可以通过 state["planner_result"] 访问 planner 的输出
            NodeDefinition(
                name="executor",
                type=NodeType.Worker,
                config={
                    "sub_type": WorkerSubType.RAG,
                    "rag_config": {
                        "model": "gpt-4",
                        "retriever": "pinecone",
                        "kb_id": "kb_main"
                    }
                }
            ),
            # 节点 3: Reflector - 反思
            # 注意：这个节点可以通过 state["executor_result"] 访问 executor 的输出
            NodeDefinition(
                name="reflector",
                type=NodeType.Reflection,
                config={
                    "rag_config": {
                        "model": "gpt-4",
                        "retriever": "pinecone",
                        "kb_id": "kb_main"
                    }
                }
            ),
        ],
        edges=[
            # planner -> executor
            EdgeDefinition(
                source="planner",
                target="executor",
                condition=None
            ),
            # executor -> reflector
            EdgeDefinition(
                source="executor",
                target="reflector",
                condition=None
            ),
            # reflector -> END
            EdgeDefinition(
                source="reflector",
                target="END",
                condition=None
            ),
        ]
    )
    
    # 注册工作流
    registry.register_workflow(workflow)
    print("✅ 工作流注册成功: dify_demo\n")
    
    # 执行工作流
    print("▶️  执行工作流...\n")
    result = registry.execute_workflow("dify_demo", {
        "input": "分析这个特定的用户行为数据"
    })
    
    print("\n📊 执行结果:")
    print(f"  输入: {result.get('input')}")
    print(f"  Planner 输出: {result.get('planner_result', {})}")
    print(f"  Executor 输出: {result.get('executor_result', {})}")
    print(f"  Reflector 输出: {result.get('reflector_result', {})}")
    print()
    
    # 展示可以灵活访问的方式
    print("\n" + "="*80)
    print("💡 关键特性：灵活的节点输出引用")
    print("="*80 + "\n")
    
    print("✨ Dify 风格设计优势:\n")
    print("  1️⃣  输出自动存储:")
    print("     • planner 节点的输出 → state['planner_result']")
    print("     • executor 节点的输出 → state['executor_result']")
    print("     • reflector 节点的输出 → state['reflector_result']\n")
    
    print("  2️⃣  后续节点可灵活访问:")
    print("     • Worker 节点可通过 state['planner_result'] 获取 planner 的数据")
    print("     • Reflector 节点可通过 state['executor_result'] 获取 executor 的数据")
    print("     • 任意节点都可访问任意前面节点的输出\n")
    
    print("  3️⃣  无需硬编码字段名称:")
    print("     • 不需要预先定义 mcp_result、rag_analysis 等字段")
    print("     • 支持动态添加新节点而无需修改现有节点的状态定义\n")
    
    print("  4️⃣  类似 Dify 的编排体验:")
    print("     • 每个节点的输出自动命名为 {node_name}_result")
    print("     • 后续节点可以在配置中引用 {{node_name.result}}")
    print("     • 提供统一的数据传递机制\n")
    
    # 展示状态演变
    print("="*80)
    print("📈 状态演变过程")
    print("="*80 + "\n")
    
    print("执行前:")
    print("  state = {'input': '分析这个特定的用户行为数据'}\n")
    
    print("执行 planner 后:")
    print("  state = {")
    print("    'input': '...',")
    print("    'planner_result': {'plan': '...', 'status': 'planned'},  ← 新增")
    print("    'plan': '...',  ← 原始字段（兼容性）")
    print("    'status': 'planned'")
    print("  }\n")
    
    print("执行 executor 后:")
    print("  state = {")
    print("    'input': '...',")
    print("    'planner_result': {'plan': '...', 'status': 'planned'},")
    print("    'executor_result': {'result': '...', 'rag_config': {...}},  ← 新增")
    print("    'result': '...',  ← 原始字段（兼容性）")
    print("    'rag_config': {...}")
    print("  }\n")
    
    print("执行 reflector 后:")
    print("  state = {")
    print("    'input': '...',")
    print("    'planner_result': {'plan': '...', 'status': 'planned'},")
    print("    'executor_result': {'result': '...', 'rag_config': {...}},")
    print("    'reflector_result': {'reflection': '...', 'status': 'reflected'},  ← 新增")
    print("    'reflection': '...',  ← 原始字段（兼容性）")
    print("    'status': 'reflected'")
    print("  }\n")
    
    # 获取和显示工作流日志
    print("="*80)
    print("🔍 完整工作流日志")
    print("="*80 + "\n")
    registry.print_workflow_logs("dify_demo")
    
    print("\n✅ 演示完成！")
    print("\n关键代码示例：\n")
    print("""
    # 在自定义节点中访问前面节点的输出
    def custom_worker_func(state: Dict[str, Any]) -> Dict[str, Any]:
        # 从 state 中获取前面 planner 节点的输出
        planner_result = state.get("planner_result", {})
        plan = planner_result.get("plan", "")
        
        # 使用 plan 数据执行当前节点逻辑
        output = {
            "result": f"Based on plan: {plan}, executed...",
            "analysis": "..."
        }
        
        # 返回的输出会自动存储为 state["current_node_result"]
        return output
    """)


if __name__ == "__main__":
    main()
