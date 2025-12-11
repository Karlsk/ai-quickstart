# Dify 风格节点输出引用机制指南

## 概述

本系统实现了类似 Dify 的灵活节点输出引用机制，允许后续节点通过统一的模式访问前面节点的执行结果。

## 核心机制

### 输出自动存储模式

每个节点的输出会自动以 `{node_name}_result` 的形式存储到工作流状态中：

```python
# 节点执行后的状态更新示例
planner 节点执行 → state['planner_result'] = {plan: '...', status: '...'}
executor 节点执行 → state['executor_result'] = {result: '...', rag_config: {...}}
reflector 节点执行 → state['reflector_result'] = {reflection: '...', status: '...'}
```

### 兼容性

同时保留原始的逐字段更新，确保旧代码继续工作：

```python
# 直接字段访问（向后兼容）
state['plan'] = '...'
state['result'] = '...'
state['reflection'] = '...'

# 新的聚合访问方式（推荐）
state['planner_result'] = {plan: '...', status: '...'}
state['executor_result'] = {result: '...', ...}
state['reflector_result'] = {reflection: '...', ...}
```

## 使用示例

### 基础工作流定义

```python
from workflow.models import (
    WorkflowDefinition, NodeDefinition, EdgeDefinition, 
    StateFieldSchema, NodeType, WorkerSubType
)
from workflow.graph_builder import WorkflowRegistry

# 创建工作流
workflow = WorkflowDefinition(
    workflow_id="my_workflow",
    entry_point="planner",
    state_schema={
        "input": StateFieldSchema(type="str"),
        "planner_result": StateFieldSchema(type="dict"),
        "executor_result": StateFieldSchema(type="dict"),
        "final_output": StateFieldSchema(type="str"),
    },
    nodes=[
        NodeDefinition(
            name="planner",
            type=NodeType.Planner,
            config={"graph_db_name": "kb", "event_name": "start"}
        ),
        NodeDefinition(
            name="executor",
            type=NodeType.Worker,
            config={
                "sub_type": WorkerSubType.RAG,
                "rag_config": {"model": "gpt-4"}
            }
        ),
    ],
    edges=[
        EdgeDefinition(source="planner", target="executor"),
        EdgeDefinition(source="executor", target="END"),
    ]
)

registry = WorkflowRegistry()
registry.register_workflow(workflow)
result = registry.execute_workflow("my_workflow", {"input": "query"})
```

### 在自定义节点中访问前面节点的输出

```python
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda

# 自定义节点函数
def custom_executor(state: Dict[str, Any]) -> Dict[str, Any]:
    # 访问前面节点（planner）的输出
    planner_result = state.get("planner_result", {})
    plan = planner_result.get("plan", "")
    
    # 基于前面节点的输出执行逻辑
    analysis = analyze_with_plan(plan, state["input"])
    
    # 返回的输出会自动存储为 state["custom_executor_result"]
    return {
        "analysis": analysis,
        "confidence": 0.95
    }

# 使用自定义节点
custom_node = RunnableLambda(custom_executor)
```

### 访问多个前面节点的输出

```python
def reflector(state: Dict[str, Any]) -> Dict[str, Any]:
    # 可以访问任意前面节点的输出
    planner_output = state.get("planner_result", {})
    executor_output = state.get("executor_result", {})
    
    # 综合考虑多个节点的输出进行反思
    reflection = {
        "plan_quality": evaluate_plan(planner_output),
        "execution_quality": evaluate_execution(executor_output),
        "overall_assessment": "good"
    }
    
    return reflection
```

## 状态演变示例

执行一个 3 节点的工作流：planner → executor → reflector

### 初始状态
```python
{
    "input": "分析用户数据",
    "planner_result": None,
    "executor_result": None,
    "reflector_result": None,
}
```

### 执行 planner 后
```python
{
    "input": "分析用户数据",
    "planner_result": {              # ← 自动添加
        "plan": "1. 收集数据 2. 处理 3. 分析",
        "status": "planned"
    },
    "plan": "...",                   # ← 原始字段（兼容性）
    "status": "planned",
    "executor_result": None,
    "reflector_result": None,
}
```

### 执行 executor 后
```python
{
    "input": "分析用户数据",
    "planner_result": {
        "plan": "1. 收集数据 2. 处理 3. 分析",
        "status": "planned"
    },
    "executor_result": {             # ← 自动添加
        "result": "处理完成",
        "metrics": {"records": 1000}
    },
    "result": "处理完成",             # ← 原始字段（兼容性）
    "reflector_result": None,
}
```

### 执行 reflector 后
```python
{
    "input": "分析用户数据",
    "planner_result": {...},
    "executor_result": {...},
    "reflector_result": {            # ← 自动添加
        "reflection": "执行质量良好",
        "recommendations": ["优化性能"]
    },
    "reflection": "执行质量良好",     # ← 原始字段（兼容性）
}
```

## API 参考

### map_output_to_state(node_name, node_output)

将节点输出映射到状态更新。

**参数：**
- `node_name` (str): 节点名称
- `node_output` (Dict): 节点返回的输出

**返回：**
- Dict: 返回给 LangGraph 的状态更新，包含：
  - `{node_name}_result`: 完整的节点输出
  - 所有原始的输出字段（用于向后兼容）

**示例：**
```python
output = {"plan": "...", "status": "..."}
state_update = map_output_to_state("planner", output)
# 返回：
# {
#     "planner_result": {"plan": "...", "status": "..."},
#     "plan": "...",
#     "status": "..."
# }
```

## 最佳实践

### 1. 定义清晰的状态字段

```python
state_schema = {
    # 输入字段
    "input": StateFieldSchema(type="str", description="用户输入"),
    
    # 每个节点的输出字段
    "planner_result": StateFieldSchema(type="dict", description="planner 输出"),
    "executor_result": StateFieldSchema(type="dict", description="executor 输出"),
    "reflector_result": StateFieldSchema(type="dict", description="reflector 输出"),
    
    # 最终输出
    "final_output": StateFieldSchema(type="str", description="最终结果"),
}
```

### 2. 使用一致的输出结构

在节点实现中保持一致的输出结构：

```python
# 推荐：始终返回字典
def worker(state) -> Dict[str, Any]:
    return {
        "result": "...",
        "metadata": {...},
        "status": "success"
    }

# 避免：返回其他类型
def bad_worker(state) -> str:
    return "直接返回字符串"  # ❌ 不好的做法
```

### 3. 安全地访问前面节点的输出

```python
def safe_access(state):
    # 始终使用 .get() 和默认值
    planner_result = state.get("planner_result", {})
    plan = planner_result.get("plan", "default_plan")
    
    # 检查是否存在
    if "executor_result" in state:
        executor_data = state["executor_result"]
    
    return {...}
```

### 4. 充分利用灵活性

```python
# 动态访问任意前面节点
def dynamic_processor(state):
    # 获取所有已执行节点的结果
    results = {
        k: v for k, v in state.items() 
        if k.endswith("_result") and v is not None
    }
    
    # 根据可用的数据进行处理
    for node_name, node_output in results.items():
        process(node_name, node_output)
    
    return {...}
```

## 与 Dify 的对比

| 功能 | Dify | 本系统 | 说明 |
|------|------|--------|------|
| 节点输出存储 | `{{node.output}}` | `state['node_result']` | 语法不同，功能相同 |
| 访问前面节点 | 配置中引用 | 代码中直接访问 | 本系统提供代码级控制 |
| 兼容性 | 不兼容 | 完全兼容 | 新旧模式并存 |
| 动态节点 | 支持 | 支持 | 都支持运行时添加 |
| 条件路由 | 支持 | 支持 | 都支持条件边 |

## 故障排除

### 问题：状态中没有 `{node_name}_result`

**原因：** 节点函数没有使用 `map_output_to_state()` 处理输出。

**解决：** 确保节点的 `build_runnable()` 方法返回 `map_output_to_state(self.name, output)`。

### 问题：无法访问前面节点的输出

**原因：** 可能节点还未执行，或节点名称拼写错误。

**解决：** 使用 `.get()` 方法和默认值，确保键名正确：
```python
result = state.get("planner_result", {})  # 安全访问
```

### 问题：状态中有大量的 None 值

**原因：** 工作流定义的 `state_schema` 中包含了还未赋值的字段。

**解决：** 只在 `state_schema` 中定义实际需要的字段。

## 总结

这个 Dify 风格的机制提供了：

- ✅ **灵活性**：无需硬编码字段名称
- ✅ **清晰性**：每个节点的输出有明确的命名空间
- ✅ **可维护性**：后续节点可轻松访问任意前面节点的数据
- ✅ **兼容性**：新旧代码可并存
- ✅ **可扩展性**：支持动态添加新节点

非常适合构建复杂的工作流编排系统！
