"""
ARCHITECTURE.md

动态工作流编排系统架构设计
基于 LangGraph，支持运行时动态编排（类似 Dify）
"""

# 动态工作流编排系统架构

## 概述

这是一个工业级的动态工作流编排系统，基于 LangGraph，支持在运行时动态编排复杂的工作流。系统设计参考了 Dify 等工作流平台的架构思想，但做到了最小化客户端改动。

## 核心特性

### 1. 节点系统（Node System）
支持 5 种节点类型，每种都有明确的语义和配置方式：

#### Planner 节点
- **用途**: 规划工作流执行路径
- **配置**: 图数据库名称、事件名称
- **实现**: 基于 LangGraph 的工作流
- **输出**: 返回规划结果

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

#### Worker 节点（MCP / RAG 两种子类型）

**MCP Worker**: Model Context Protocol
- 用于调用外部 MCP 服务
- 配置 MCP 服务器信息

**RAG Worker**: Retrieval-Augmented Generation
- 用于调用 RAG 系统
- 配置模型、检索器、知识库等

```python
# MCP Worker
NodeDefinition(
    name="mcp_worker",
    type=NodeType.Worker,
    config={
        "sub_type": "mcp",
        "mcp_config": {"server": "localhost:8080"}
    }
)

# RAG Worker
NodeDefinition(
    name="rag_worker",
    type=NodeType.Worker,
    config={
        "sub_type": "rag",
        "rag_config": {"model": "gpt-4", "kb_id": "kb_001"}
    }
)
```

#### Reflection 节点
- **用途**: 对结果进行反思和优化
- **配置**: 可选的 RAG 配置
- **使用场景**: 结果质量评估、优化建议

```python
NodeDefinition(
    name="reflection",
    type=NodeType.Reflection,
    config={
        "rag_config": {"kb_id": "kb_reflection"}
    }
)
```

#### Agent 节点
- **用途**: 运行时动态引入已注册的工作流
- **配置**: 引用的工作流 ID
- **特点**: 支持工作流嵌套，实现模块化编排

```python
NodeDefinition(
    name="sub_agent",
    type=NodeType.Agent,
    config={
        "workflow_id": "base_workflow_v1"
    }
)
```

#### LLM 和 Tool 节点
- **当前状态**: 预留接口，暂未实现

### 2. 边系统（Edge System）
支持两种边类型：

#### 普通边（Normal Edges）
- 直接连接两个节点
- 无条件分支

#### 条件边（Conditional Edges）
- 根据状态中的条件键进行路由
- 支持动态分支控制

```python
# 普通边
EdgeDefinition(source="node1", target="node2")

# 条件边
EdgeDefinition(
    source="classifier",
    target="path_a",
    condition="route_type"  # 根据 state.route_type 的值确定目标
)
```

### 3. 统一节点接口（Unified Node Interface）

所有节点继承自 `BaseNode` 抽象基类，实现统一的接口：

```python
class BaseNode(ABC):
    def __init__(self, name, node_type, config, operator_log=None)
    def build_runnable(self) -> Runnable  # 构建可执行对象
    def validate_config(self) -> bool     # 验证配置
    def log_execution(log: ExecutionLog)  # 记录执行日志
    def get_execution_history() -> List   # 获取执行历史
```

### 4. 工业级功能

#### 操作符日志（Operator Logging）
- 记录每个节点的输入输出 schema
- 记录执行时间、错误信息
- 支持完整的执行追踪

```python
ExecutionLog(
    node_name="planner",
    node_type=NodeType.Planner,
    timestamp=datetime.now(),
    input_data={...},
    output_data={...},
    execution_time_ms=123.45,
    error=None  # 如果有错误
)
```

#### 动态状态管理
- 根据工作流定义动态创建 Pydantic 模型
- 自动处理状态字段类型转换
- 支持任意字段扩展

#### 工作流注册表（Workflow Registry）
- 编译后的工作流缓存
- 支持工作流的生命周期管理（注册、查询、执行、删除）
- 类型安全的工作流引用

## 工作流定义结构

```python
WorkflowDefinition(
    workflow_id="my_workflow",
    nodes=[...],        # 节点列表
    edges=[...],        # 边列表
    entry_point="node1", # 入口节点名称
    state_schema={      # 状态字段定义
        "query": StateFieldSchema(type="str", default=""),
        "result": StateFieldSchema(type="str", default="")
    },
    operator_logs={     # 操作符日志
        "node1": OperatorLog(...)
    },
    execution_history=[]  # 执行历史
)
```

## 架构设计亮点

### 1. 最小化客户端改动
- 工作流定义完全基于 Pydantic 模型，JSON 序列化友好
- 无需修改现有客户端代码即可支持新的节点类型
- 通过工厂函数统一创建节点

### 2. 工业级代码质量
- 完整的错误处理和验证
- 详细的日志记录
- 类型提示覆盖所有公开 API
- 单元测试和集成测试覆盖

### 3. 灵活的扩展性
- 易于添加新的节点类型（继承 BaseNode）
- 支持自定义路由逻辑
- 支持工作流嵌套和模块化

### 4. 可追踪性
- 执行日志记录输入输出数据
- 执行时间统计
- 错误信息捕获
- 支持完整的审计追踪

## 项目结构

```
workflow/
├── __init__.py          # 模块导出
├── models.py            # 数据模型定义
├── base_node.py         # 节点基类和实现
├── graph_builder.py     # 图构建器和注册表
└── test_workflow.py     # 单元测试
```

## 使用示例

### 示例 1: 简单工作流
```python
registry = WorkflowRegistry()

workflow_def = WorkflowDefinition(
    workflow_id="simple_workflow",
    nodes=[
        NodeDefinition(
            name="planner",
            type=NodeType.Planner,
            config={"graph_db_name": "db", "event_name": "start"}
        )
    ],
    edges=[EdgeDefinition(source="planner", target="END")],
    entry_point="planner",
    state_schema={"task": StateFieldSchema(type="str", ...)}
)

registry.register_workflow(workflow_def)
result = registry.execute_workflow("simple_workflow", {"task": "..."})
```

### 示例 2: 复杂多节点工作流
```python
# Planner -> MCP Worker -> RAG Worker -> Reflection -> END
workflow_def = WorkflowDefinition(
    workflow_id="pipeline",
    nodes=[
        NodeDefinition(name="planner", type=NodeType.Planner, ...),
        NodeDefinition(name="mcp_worker", type=NodeType.Worker, ...),
        NodeDefinition(name="rag_worker", type=NodeType.Worker, ...),
        NodeDefinition(name="reflection", type=NodeType.Reflection, ...)
    ],
    edges=[
        EdgeDefinition(source="planner", target="mcp_worker"),
        EdgeDefinition(source="mcp_worker", target="rag_worker"),
        EdgeDefinition(source="rag_worker", target="reflection"),
        EdgeDefinition(source="reflection", target="END")
    ],
    entry_point="planner",
    state_schema={...}
)
```

### 示例 3: 动态工作流（Agent 嵌套）
```python
# 首先注册基础工作流
base_workflow = WorkflowDefinition(...)
registry.register_workflow(base_workflow)

# 然后在主工作流中引用
main_workflow = WorkflowDefinition(
    workflow_id="main",
    nodes=[
        ...,
        NodeDefinition(
            name="sub_agent",
            type=NodeType.Agent,
            config={"workflow_id": "base_workflow"}
        )
    ],
    ...
)
registry.register_workflow(main_workflow)
```

## 下一步实现方向

### 第二步：动态编排功能
- [ ] API 层实现（FastAPI）
- [ ] 工作流编辑器 API
- [ ] 工作流版本管理
- [ ] 持久化存储（数据库）

### 第三步：高级功能
- [ ] 条件分支的复杂表达式支持
- [ ] 循环和并行处理
- [ ] 中断和恢复机制
- [ ] 性能优化（并发执行）

### 第四步：监控和调试
- [ ] 可视化调试界面
- [ ] 实时执行监控
- [ ] 性能分析工具
- [ ] 日志导出和分析

## 测试覆盖

- ✅ 节点定义测试
- ✅ 边定义测试
- ✅ 工作流注册和执行
- ✅ 复杂多节点工作流
- ✅ 操作符日志跟踪
- ✅ 错误处理和验证
- ✅ 工作流注册表管理

## 性能考虑

- 工作流编译一次，多次执行
- 支持并发执行多个工作流实例
- 节点执行时间自动记录
- 可扩展的日志系统

## 安全考虑

- 工作流定义验证
- 节点配置验证
- 错误信息安全处理
- 执行历史记录
