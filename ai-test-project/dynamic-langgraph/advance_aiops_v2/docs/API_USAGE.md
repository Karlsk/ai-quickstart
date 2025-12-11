# FastAPI 工作流管理 API 使用指南

这是一个基于 FastAPI 的完整工作流管理系统，提供 RESTful API 来创建、配置、执行和监控动态工作流。

## 快速开始

### 1. 启动 FastAPI 服务器

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/dynamic-langgraph/advance_aiops_v2

# 使用 uvicorn 启动服务器
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务器启动后，你可以访问：
- **API 文档**: http://localhost:8000/docs (Swagger UI)
- **API 文档**: http://localhost:8000/redoc (ReDoc)
- **根路由**: http://localhost:8000/ (API 信息)

### 2. 在另一个终端运行示例客户端

```bash
python api_client_example.py
```

## API 端点详解

### 工作流管理

#### 创建工作流
```
POST /workflows
```

**请求体示例**：
```json
{
    "workflow_id": "my_workflow",
    "entry_point": "planner",
    "state_schema": {
        "input": {
            "type": "str",
            "description": "输入查询"
        },
        "planner_result": {
            "type": "dict",
            "default": null
        }
    },
    "nodes": [
        {
            "name": "planner",
            "type": "planner",
            "config": {
                "graph_db_name": "knowledge_graph",
                "event_name": "plan_event"
            }
        },
        {
            "name": "executor",
            "type": "worker",
            "config": {
                "sub_type": "rag",
                "rag_config": {
                    "model": "gpt-4"
                }
            }
        }
    ],
    "edges": [
        {
            "source": "planner",
            "target": "executor"
        },
        {
            "source": "executor",
            "target": "END"
        }
    ]
}
```

**响应示例**：
```json
{
    "workflow_id": "my_workflow",
    "status": "success",
    "message": "工作流 'my_workflow' 创建成功",
    "data": {
        "nodes_count": 2,
        "edges_count": 2,
        "entry_point": "planner"
    }
}
```

#### 列出所有工作流
```
GET /workflows
```

**响应示例**：
```json
{
    "total": 2,
    "workflows": ["workflow_1", "workflow_2"],
    "timestamp": "2025-12-11T17:00:00"
}
```

#### 获取工作流详情
```
GET /workflows/{workflow_id}
```

#### 删除工作流
```
DELETE /workflows/{workflow_id}
```

### 工作流执行

#### 执行工作流
```
POST /workflows/{workflow_id}/execute
```

**请求体示例**：
```json
{
    "workflow_id": "my_workflow",
    "input_data": {
        "input": "这是一个测试查询"
    }
}
```

**响应示例**：
```json
{
    "status": "success",
    "workflow_id": "my_workflow",
    "message": "工作流执行完成",
    "result": {
        "input": "这是一个测试查询",
        "planner_result": {...},
        "executor_result": {...}
    },
    "timestamp": "2025-12-11T17:00:00"
}
```

### 工作流日志

#### 获取完整日志
```
GET /workflows/{workflow_id}/logs
```

返回包含 OperatorLog 和 ExecutionLog 的完整日志。

#### 获取执行历史
```
GET /workflows/{workflow_id}/execution-history
```

获取所有节点的执行记录。

#### 获取操作符日志
```
GET /workflows/{workflow_id}/operator-logs
```

获取每个节点的输入输出 Schema 定义。

#### 获取节点执行历史
```
GET /workflows/{workflow_id}/node/{node_name}/execution-history
```

获取特定节点的执行记录。

## 使用示例

### Python 客户端示例

使用提供的 `WorkflowAPIClient` 类：

```python
from api_client_example import WorkflowAPIClient

# 创建客户端
client = WorkflowAPIClient("http://localhost:8000")

# 创建工作流
workflow_config = {
    "workflow_id": "my_workflow",
    "entry_point": "planner",
    "state_schema": {...},
    "nodes": [...],
    "edges": [...]
}
result = client.create_workflow(workflow_config)

# 执行工作流
exec_result = client.execute_workflow(
    "my_workflow",
    {"input": "测试数据"}
)

# 获取日志
logs = client.get_workflow_logs("my_workflow")
```

### cURL 示例

#### 创建工作流
```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test_workflow",
    "entry_point": "planner",
    "state_schema": {
        "input": {"type": "str", "description": "输入"}
    },
    "nodes": [
        {
            "name": "planner",
            "type": "planner",
            "config": {
                "graph_db_name": "kb",
                "event_name": "start"
            }
        }
    ],
    "edges": [
        {
            "source": "planner",
            "target": "END"
        }
    ]
  }'
```

#### 执行工作流
```bash
curl -X POST "http://localhost:8000/workflows/test_workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test_workflow",
    "input_data": {
        "input": "这是一个测试"
    }
  }'
```

#### 获取工作流日志
```bash
curl "http://localhost:8000/workflows/test_workflow/logs"
```

## 节点类型

支持的节点类型有：

- **planner**: 规划节点，用于执行规划逻辑
- **worker**: 执行节点，支持 MCP 和 RAG 两种子类型
- **reflection**: 反思节点，用于执行反思逻辑
- **agent**: Agent 节点，用于运行动态编译的子工作流

## 状态字段类型

支持的状态字段类型有：

- `str`: 字符串
- `int`: 整数
- `float`: 浮点数
- `bool`: 布尔值
- `dict`: 字典（任意结构）
- `list`: 列表

## 自动 Schema 生成

系统会自动为没有显式定义 OperatorLog 的节点生成合理的默认 Schema：

- **Planner**: 输入 `input` (str)，输出 `plan` (str) 和 `status` (str)
- **Worker**: 输入 `plan` (str)，输出 `result` (str)
- **Reflection**: 输入 `result` (str)，输出 `reflection` (str) 和 `status` (str)
- **Agent**: 输入 `input` (str)，输出 `output` (str)

## 故障排除

### 工作流不存在错误
```
HTTPException: 404 - 工作流 'xxx' 不存在
```
解决方案：确保先创建工作流再执行或查询。

### 执行工作流失败
如果工作流执行失败，检查：
1. 输入数据是否符合 `state_schema` 定义
2. 节点配置是否正确
3. 查看错误信息中的详细信息

### API 响应慢
- 确保 FastAPI 服务器运行在合适的环境中
- 考虑使用 `gunicorn` 以获得更好的性能：
  ```bash
  gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
  ```

## 生产部署

### 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 300
```

### 使用 Docker

创建 `Dockerfile`：

```dockerfile
FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：

```bash
docker build -t workflow-api .
docker run -p 8000:8000 workflow-api
```

## API 版本

- 当前版本: 1.0.0
- 基于: FastAPI 0.100+, Pydantic 2.0+

## 许可证

MIT
