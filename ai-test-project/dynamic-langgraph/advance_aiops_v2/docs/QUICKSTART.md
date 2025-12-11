# 动态工作流编排系统 - 快速开始指南

## 安装依赖

```bash
pip install langgraph langchain pydantic pytest
```

## 最简单的例子（10 行代码）

```python
from workflow import *

# 1. 创建注册表
registry = WorkflowRegistry()

# 2. 定义工作流
workflow = WorkflowDefinition(
    workflow_id="hello_workflow",
    nodes=[
        NodeDefinition(
            name="hello",
            type=NodeType.Planner,
            config={"graph_db_name": "test", "event_name": "start"}
        )
    ],
    edges=[EdgeDefinition(source="hello", target="END")],
    entry_point="hello",
    state_schema={"msg": StateFieldSchema(type="str", default="")}
)

# 3. 注册并执行
registry.register_workflow(workflow)
result = registry.execute_workflow("hello_workflow", {"msg": "Hello"})
print(result)
```

## 节点类型快速参考

### Planner 节点（规划）
```python
NodeDefinition(
    name="planner",
    type=NodeType.Planner,
    config={
        "graph_db_name": "knowledge_graph",
        "event_name": "task_start"
    }
)
```

### Worker 节点 - MCP
```python
NodeDefinition(
    name="mcp_worker",
    type=NodeType.Worker,
    config={
        "sub_type": "mcp",
        "mcp_config": {"server": "localhost:8080"}
    }
)
```

### Worker 节点 - RAG
```python
NodeDefinition(
    name="rag_worker",
    type=NodeType.Worker,
    config={
        "sub_type": "rag",
        "rag_config": {"model": "gpt-4", "kb_id": "kb_001"}
    }
)
```

### Reflection 节点（反思）
```python
NodeDefinition(
    name="reflection",
    type=NodeType.Reflection,
    config={"rag_config": {"kb_id": "kb_reflection"}}
)
```

### Agent 节点（动态编排）
```python
NodeDefinition(
    name="sub_agent",
    type=NodeType.Agent,
    config={"workflow_id": "other_workflow"}
)
```

## 常见工作流模式

### 模式 1: 线性流程
```
Planner -> Worker -> Reflection -> END
```

```python
edges = [
    EdgeDefinition(source="planner", target="worker"),
    EdgeDefinition(source="worker", target="reflection"),
    EdgeDefinition(source="reflection", target="END")
]
```

### 模式 2: 分支流程
```
       -> Worker_A ->
Classifier             -> Merger -> END
       -> Worker_B ->
```

```python
edges = [
    EdgeDefinition(source="classifier", target="worker_a"),
    EdgeDefinition(source="classifier", target="worker_b"),
    EdgeDefinition(source="worker_a", target="merger"),
    EdgeDefinition(source="worker_b", target="merger"),
    EdgeDefinition(source="merger", target="END")
]
```

### 模式 3: 嵌套工作流
```python
# 首先定义和注册基础工作流
base_workflow = WorkflowDefinition(...)
registry.register_workflow(base_workflow)

# 然后在其他工作流中使用 Agent 节点引用它
main_workflow = WorkflowDefinition(
    ...,
    nodes=[
        ...,
        NodeDefinition(
            name="sub_workflow",
            type=NodeType.Agent,
            config={"workflow_id": base_workflow.workflow_id}
        )
    ]
)
registry.register_workflow(main_workflow)
```

## 运行测试

```bash
# 运行所有测试
pytest test_workflow.py -v

# 只运行特定测试
pytest test_workflow.py::TestWorkflowRegistry -v

# 显示详细输出
pytest test_workflow.py -vv -s
```

## 运行示例

```bash
python example_usage.py
```

这会执行 5 个完整示例：
1. 简单 Planner 工作流
2. 多 Worker 工作流（MCP + RAG）
3. 条件路由工作流
4. 嵌套 Agent 工作流
5. 带完整日志的工作流

## 调试工作流

### 查看工作流信息
```python
registry = WorkflowRegistry()

# 列出所有工作流
workflows = registry.list_workflows()
print(f"已注册工作流: {workflows}")

# 获取统计信息
stats = registry.get_registry_stats()
print(f"总工作流数: {stats['total_workflows']}")

# 检查工作流是否存在
if registry.has_workflow("my_workflow"):
    print("工作流已存在")
```

### 查看执行结果
```python
# 执行工作流并查看结果
result = registry.execute_workflow("my_workflow", {"query": "..."})

# result 是一个字典，包含所有状态字段
print(result)  # {'query': '...', 'result': '...', 'history': [...]}
```

## 添加新的节点类型

```python
from workflow.base_node import BaseNode
from langchain_core.runnables import Runnable, RunnableLambda

class CustomNode(BaseNode):
    def validate_config(self) -> bool:
        # 验证配置
        if not self.config.get("required_field"):
            raise ValueError("required_field is required")
        return True
    
    def build_runnable(self) -> Runnable:
        def custom_func(state):
            # 你的逻辑
            return {"result": "..."}
        
        return RunnableLambda(custom_func).with_config(tags=[self.name])
```

## 常见问题

### Q: 如何在 Worker 中调用真实的 MCP/RAG 系统？
A: 在 WorkerNode 的 `_execute_mcp_worker()` 和 `_execute_rag_worker()` 方法中替换模拟实现。

### Q: 能否动态修改已注册的工作流？
A: 可以注销旧工作流，然后注册新版本：
```python
registry.unregister_workflow("old_workflow")
registry.register_workflow(new_workflow_def)
```

### Q: 如何跟踪工作流执行？
A: 每个节点都会记录 ExecutionLog，可以通过 node 的 `get_execution_history()` 方法获取。

### Q: 支持并行执行吗？
A: 当前不支持，但架构允许添加这个功能。

## 下一步

1. 查看 [ARCHITECTURE.md](ARCHITECTURE.md) 了解详细设计
2. 查看 [example_usage.py](example_usage.py) 了解更复杂的示例
3. 阅读 [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) 了解实现细节

## API 文档

### WorkflowRegistry

```python
class WorkflowRegistry:
    def register_workflow(definition: WorkflowDefinition) -> str
    def get_workflow(workflow_id: str) -> Any
    def has_workflow(workflow_id: str) -> bool
    def list_workflows() -> list[str]
    def unregister_workflow(workflow_id: str) -> bool
    def execute_workflow(workflow_id: str, input_data: Dict) -> Any
    def get_registry_stats() -> Dict
```

### 数据模型

```python
# 工作流定义
WorkflowDefinition(
    workflow_id: str
    nodes: List[NodeDefinition]
    edges: List[EdgeDefinition]
    entry_point: str
    state_schema: Dict[str, StateFieldSchema]
    operator_logs: Dict[str, OperatorLog]
    execution_history: List[ExecutionLog]
)

# 节点定义
NodeDefinition(
    name: str
    type: NodeType
    config: Dict[str, Any]
)

# 状态字段
StateFieldSchema(
    type: str  # "str", "int", "List[str]" 等
    default: Any
    description: str
)
```

## 更多资源

- [模型定义](workflow/models.py) - 所有数据模型
- [节点实现](workflow/base_node.py) - 节点类实现
- [图构建器](workflow/graph_builder.py) - 工作流构建逻辑
- [测试用例](test_workflow.py) - 完整的测试示例
