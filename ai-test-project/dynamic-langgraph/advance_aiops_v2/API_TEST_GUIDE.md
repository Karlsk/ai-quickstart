# API 测试指南

本文档提供所有 API 端点的详细测试示例，包括 cURL、Python、JavaScript 等多种方式。

## 📋 目录

1. [环境准备](#环境准备)
2. [基础 API](#基础-api)
3. [工作流管理 API](#工作流管理-api)
4. [工作流执行 API](#工作流执行-api)
5. [工作流日志 API](#工作流日志-api)
6. [自动化测试](#自动化测试)

---

## 环境准备

### 启动服务器

```bash
cd /Users/gaorj/PycharmProjects/Learning/ai-quickstart/ai-test-project/dynamic-langgraph/advance_aiops_v2

# 启动 FastAPI 服务器
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**输出示例**：
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

### 验证服务器运行

```bash
curl -s http://localhost:8000/ | python -m json.tool
```

---

## 基础 API

### 1. 获取 API 信息

**端点**: `GET /`

**说明**: 获取 API 的基本信息和所有可用端点

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

response = requests.get("http://localhost:8000/")
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "name": "Dynamic Workflow Management API",
  "version": "1.0.0",
  "description": "Support creating, configuring, executing and monitoring LangGraph workflows",
  "endpoints": {
    "Workflow Management": [
      "POST /workflows - Create workflow",
      "GET /workflows - List all workflows",
      "GET /workflows/{workflow_id} - View workflow details",
      "DELETE /workflows/{workflow_id} - Delete workflow"
    ],
    "Workflow Execution": [
      "POST /workflows/{workflow_id}/execute - Execute workflow"
    ],
    "Workflow Logs": [
      "GET /workflows/{workflow_id}/logs - View complete logs",
      "GET /workflows/{workflow_id}/execution-history - View execution history",
      "GET /workflows/{workflow_id}/operator-logs - View operator logs",
      "GET /workflows/{workflow_id}/node/{node_name}/execution-history - View node execution history"
    ]
  }
}
```

---

## 工作流管理 API

### 1. 创建工作流

**端点**: `POST /workflows`

**说明**: 创建和注册一个新工作流

#### cURL 测试

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "test_workflow_001",
    "entry_point": "planner",
    "state_schema": {
      "input": {
        "type": "str",
        "description": "User input query",
        "default": null
      },
      "planner_result": {
        "type": "dict",
        "description": "Result from planner node",
        "default": null
      },
      "executor_result": {
        "type": "dict",
        "description": "Result from executor node",
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
            "model": "gpt-4",
            "retriever": "pinecone"
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
  }'
```

#### Python 测试

```python
import requests
import json

url = "http://localhost:8000/workflows"

payload = {
    "workflow_id": "test_workflow_001",
    "entry_point": "planner",
    "state_schema": {
        "input": {
            "type": "str",
            "description": "User input query"
        },
        "planner_result": {
            "type": "dict",
            "description": "Result from planner node"
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
                "rag_config": {"model": "gpt-4"}
            }
        }
    ],
    "edges": [
        {"source": "planner", "target": "executor"},
        {"source": "executor", "target": "END"}
    ]
}

response = requests.post(url, json=payload)
print(json.dumps(response.json(), indent=2))
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "test_workflow_001",
  "status": "success",
  "message": "Workflow 'test_workflow_001' created successfully",
  "data": {
    "nodes_count": 2,
    "edges_count": 2,
    "entry_point": "planner"
  }
}
```

### 2. 列出所有工作流

**端点**: `GET /workflows`

**说明**: 获取所有已注册工作流的列表

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

response = requests.get("http://localhost:8000/workflows")
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "total": 1,
  "workflows": [
    "test_workflow_001"
  ],
  "timestamp": "2025-12-11T17:00:00.123456"
}
```

### 3. 获取工作流详情

**端点**: `GET /workflows/{workflow_id}`

**说明**: 获取指定工作流的详细信息

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows/test_workflow_001" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "test_workflow_001"
response = requests.get(f"http://localhost:8000/workflows/{workflow_id}")
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "test_workflow_001",
  "entry_point": "planner",
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
          "model": "gpt-4",
          "retriever": "pinecone"
        }
      }
    }
  ],
  "edges": [
    {
      "source": "planner",
      "target": "executor",
      "condition": null
    },
    {
      "source": "executor",
      "target": "END",
      "condition": null
    }
  ],
  "state_fields": {
    "input": {
      "type": "str",
      "description": "User input query",
      "default": null
    },
    "planner_result": {
      "type": "dict",
      "description": "Result from planner node",
      "default": null
    }
  }
}
```

### 4. 删除工作流

**端点**: `DELETE /workflows/{workflow_id}`

**说明**: 删除指定的工作流

#### cURL 测试

```bash
curl -X DELETE "http://localhost:8000/workflows/test_workflow_001" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "test_workflow_001"
response = requests.delete(f"http://localhost:8000/workflows/{workflow_id}")
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "status": "success",
  "message": "Workflow 'test_workflow_001' deleted",
  "timestamp": "2025-12-11T17:00:00.123456"
}
```

**错误响应** (404 Not Found):

```json
{
  "detail": "Workflow 'nonexistent' does not exist"
}
```

---

## 工作流执行 API

### 1. 执行工作流

**端点**: `POST /workflows/{workflow_id}/execute`

**说明**: 执行指定的工作流

#### 前置条件

首先创建一个工作流：

```bash
# 创建工作流
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "exec_test_001",
    "entry_point": "planner",
    "state_schema": {
      "input": {"type": "str", "description": "Input"}
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
  }'
```

#### cURL 测试

```bash
curl -X POST "http://localhost:8000/workflows/exec_test_001/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "exec_test_001",
    "input_data": {
      "input": "Analyze this dataset for patterns"
    }
  }'
```

#### Python 测试

```python
import requests

workflow_id = "exec_test_001"
url = f"http://localhost:8000/workflows/{workflow_id}/execute"

payload = {
    "workflow_id": workflow_id,
    "input_data": {
        "input": "Analyze this dataset for patterns"
    }
}

response = requests.post(url, json=payload)
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "status": "success",
  "workflow_id": "exec_test_001",
  "message": "Workflow execution completed",
  "result": {
    "input": "Analyze this dataset for patterns",
    "planner_result": {
      "plan": "Plan from planner using graph_db=kb, event=start",
      "status": "planned"
    }
  },
  "timestamp": "2025-12-11T17:00:00.123456"
}
```

---

## 工作流日志 API

### 1. 获取完整日志

**端点**: `GET /workflows/{workflow_id}/logs`

**说明**: 获取工作流的完整日志（包含操作符日志和执行历史）

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows/exec_test_001/logs" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "exec_test_001"
response = requests.get(f"http://localhost:8000/workflows/{workflow_id}/logs")
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "exec_test_001",
  "operator_logs": {
    "planner": {
      "input_schema": {
        "input": {
          "type": "str",
          "description": "Input query"
        }
      },
      "output_schema": {
        "plan": {
          "type": "str",
          "description": "Planning result"
        },
        "status": {
          "type": "str",
          "description": "Status"
        }
      }
    }
  },
  "execution_history": [
    {
      "node_name": "planner",
      "node_type": "planner",
      "timestamp": "2025-12-11T17:00:00.123456",
      "execution_time_ms": 5.23,
      "input_data": {
        "input": "Analyze this dataset"
      },
      "output_data": {
        "plan": "Plan from planner",
        "status": "planned"
      },
      "error": null
    }
  ],
  "total_executions": 1,
  "timestamp": "2025-12-11T17:00:00.123456"
}
```

### 2. 获取执行历史

**端点**: `GET /workflows/{workflow_id}/execution-history`

**说明**: 获取工作流的执行历史日志

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows/exec_test_001/execution-history" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "exec_test_001"
response = requests.get(
    f"http://localhost:8000/workflows/{workflow_id}/execution-history"
)
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "exec_test_001",
  "total_logs": 1,
  "logs": [
    {
      "node_name": "planner",
      "node_type": "planner",
      "timestamp": "2025-12-11T17:00:00.123456",
      "execution_time_ms": 5.23,
      "input_data": {
        "input": "Analyze this dataset"
      },
      "output_data": {
        "plan": "Plan from planner",
        "status": "planned"
      },
      "error": null
    }
  ]
}
```

### 3. 获取操作符日志

**端点**: `GET /workflows/{workflow_id}/operator-logs`

**说明**: 获取工作流中各节点的操作符日志（Schema 定义）

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows/exec_test_001/operator-logs" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "exec_test_001"
response = requests.get(
    f"http://localhost:8000/workflows/{workflow_id}/operator-logs"
)
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "exec_test_001",
  "total_nodes": 1,
  "operator_logs": {
    "planner": {
      "input_schema": {
        "input": {
          "type": "str",
          "description": "Input query"
        }
      },
      "output_schema": {
        "plan": {
          "type": "str",
          "description": "Planning result"
        },
        "status": {
          "type": "str",
          "description": "Status"
        }
      }
    }
  }
}
```

### 4. 获取节点执行历史

**端点**: `GET /workflows/{workflow_id}/node/{node_name}/execution-history`

**说明**: 获取指定节点的执行历史

#### cURL 测试

```bash
curl -X GET "http://localhost:8000/workflows/exec_test_001/node/planner/execution-history" \
  -H "Content-Type: application/json"
```

#### Python 测试

```python
import requests

workflow_id = "exec_test_001"
node_name = "planner"
response = requests.get(
    f"http://localhost:8000/workflows/{workflow_id}/node/{node_name}/execution-history"
)
print(response.json())
```

**预期响应** (200 OK):

```json
{
  "workflow_id": "exec_test_001",
  "node_name": "planner",
  "total_logs": 1,
  "logs": [
    {
      "timestamp": "2025-12-11T17:00:00.123456",
      "execution_time_ms": 5.23,
      "input_data": {
        "input": "Analyze this dataset"
      },
      "output_data": {
        "plan": "Plan from planner",
        "status": "planned"
      },
      "error": null
    }
  ]
}
```

---

## 自动化测试

### 使用 Postman

#### 1. 导入 API 集合

创建 `postman_collection.json`:

```json
{
  "info": {
    "name": "Workflow API Tests",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "Create Workflow",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\"workflow_id\": \"test_001\", \"entry_point\": \"planner\", ...}"
        },
        "url": {
          "raw": "http://localhost:8000/workflows",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["workflows"]
        }
      }
    }
  ]
}
```

### 使用 Python 测试脚本

创建 `test_api.py`:

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

class APITester:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_create_workflow(self):
        """测试创建工作流"""
        print("\n[Test 1] Creating workflow...")
        
        payload = {
            "workflow_id": f"test_{int(time.time())}",
            "entry_point": "planner",
            "state_schema": {
                "input": {"type": "str", "description": "Input"}
            },
            "nodes": [
                {
                    "name": "planner",
                    "type": "planner",
                    "config": {"graph_db_name": "kb", "event_name": "start"}
                }
            ],
            "edges": [{"source": "planner", "target": "END"}]
        }
        
        response = self.session.post(f"{self.base_url}/workflows", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "success"
        print(f"✅ Workflow created: {data['workflow_id']}")
        return data["workflow_id"]
    
    def test_list_workflows(self):
        """测试列出工作流"""
        print("\n[Test 2] Listing workflows...")
        
        response = self.session.get(f"{self.base_url}/workflows")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Total workflows: {data['total']}")
        return data
    
    def test_get_workflow(self, workflow_id):
        """测试获取工作流详情"""
        print(f"\n[Test 3] Getting workflow details: {workflow_id}")
        
        response = self.session.get(f"{self.base_url}/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Workflow loaded: {data['workflow_id']}")
        return data
    
    def test_execute_workflow(self, workflow_id):
        """测试执行工作流"""
        print(f"\n[Test 4] Executing workflow: {workflow_id}")
        
        payload = {
            "workflow_id": workflow_id,
            "input_data": {"input": "Test query"}
        }
        
        response = self.session.post(
            f"{self.base_url}/workflows/{workflow_id}/execute",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Workflow executed successfully")
        return data
    
    def test_get_logs(self, workflow_id):
        """测试获取日志"""
        print(f"\n[Test 5] Getting logs: {workflow_id}")
        
        response = self.session.get(f"{self.base_url}/workflows/{workflow_id}/logs")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Logs retrieved, executions: {data['total_executions']}")
        return data
    
    def test_delete_workflow(self, workflow_id):
        """测试删除工作流"""
        print(f"\n[Test 6] Deleting workflow: {workflow_id}")
        
        response = self.session.delete(f"{self.base_url}/workflows/{workflow_id}")
        assert response.status_code == 200
        data = response.json()
        print(f"✅ Workflow deleted")
        return data
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("API 自动化测试")
        print("=" * 50)
        
        try:
            # 创建工作流
            workflow_id = self.test_create_workflow()
            
            # 列出工作流
            self.test_list_workflows()
            
            # 获取工作流详情
            self.test_get_workflow(workflow_id)
            
            # 执行工作流
            self.test_execute_workflow(workflow_id)
            
            # 获取日志
            self.test_get_logs(workflow_id)
            
            # 删除工作流
            self.test_delete_workflow(workflow_id)
            
            print("\n" + "=" * 50)
            print("✅ 所有测试通过！")
            print("=" * 50)
        
        except AssertionError as e:
            print(f"\n❌ 测试失败: {e}")
        except Exception as e:
            print(f"\n❌ 错误: {e}")

if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
```

运行测试：

```bash
python test_api.py
```

### 使用 pytest

创建 `test_api_pytest.py`:

```python
import pytest
import requests

BASE_URL = "http://localhost:8000"

@pytest.fixture
def api_client():
    return requests.Session()

@pytest.fixture
def workflow_id():
    """创建测试工作流"""
    payload = {
        "workflow_id": "pytest_test_001",
        "entry_point": "planner",
        "state_schema": {
            "input": {"type": "str", "description": "Input"}
        },
        "nodes": [
            {
                "name": "planner",
                "type": "planner",
                "config": {"graph_db_name": "kb", "event_name": "start"}
            }
        ],
        "edges": [{"source": "planner", "target": "END"}]
    }
    
    response = requests.post(f"{BASE_URL}/workflows", json=payload)
    yield response.json()["workflow_id"]
    
    # 清理
    requests.delete(f"{BASE_URL}/workflows/pytest_test_001")

def test_get_api_info(api_client):
    """测试获取 API 信息"""
    response = api_client.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert "name" in response.json()

def test_list_workflows(api_client):
    """测试列出工作流"""
    response = api_client.get(f"{BASE_URL}/workflows")
    assert response.status_code == 200
    assert "total" in response.json()

def test_get_workflow(api_client, workflow_id):
    """测试获取工作流详情"""
    response = api_client.get(f"{BASE_URL}/workflows/{workflow_id}")
    assert response.status_code == 200
    assert response.json()["workflow_id"] == workflow_id

def test_execute_workflow(api_client, workflow_id):
    """测试执行工作流"""
    payload = {
        "workflow_id": workflow_id,
        "input_data": {"input": "Test"}
    }
    response = api_client.post(
        f"{BASE_URL}/workflows/{workflow_id}/execute",
        json=payload
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

def test_get_logs(api_client, workflow_id):
    """测试获取日志"""
    response = api_client.get(f"{BASE_URL}/workflows/{workflow_id}/logs")
    assert response.status_code == 200
    assert "operator_logs" in response.json()
```

运行 pytest：

```bash
pytest test_api_pytest.py -v
```

---

## 常见错误和解决方案

### 错误 1: 连接被拒绝

```
ConnectionRefusedError: [Errno 111] Connection refused
```

**解决方案**:
- 确保服务器已启动：`python main.py`
- 检查端口 8000 是否可用

### 错误 2: 工作流不存在

```json
{
  "detail": "Workflow 'nonexistent' does not exist"
}
```

**解决方案**:
- 检查工作流 ID 是否正确
- 先创建工作流再执行或查询

### 错误 3: 请求体格式错误

```json
{
  "detail": [
    {
      "loc": ["body", "workflow_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**解决方案**:
- 确保请求体包含所有必需字段
- 检查数据类型是否正确

### 错误 4: 状态字段类型不匹配

```
string_type validation error
```

**解决方案**:
- 确保 state_schema 中的字段类型定义正确
- 如果需要传递复杂对象，使用 `"dict"` 类型

---

## 性能测试

### 使用 Apache Bench (ab)

```bash
# 测试 100 个并发请求
ab -n 100 -c 10 http://localhost:8000/

# 输出示例
# Requests per second:    250 [#/sec] (mean)
# Time per request:       40 [ms] (mean)
```

### 使用 wrk

```bash
# 测试 30 秒，4 个线程，10 个连接
wrk -t4 -c10 -d30s http://localhost:8000/

# 输出示例
# Requests/sec: 1234.56
# Transfer/sec: 567.89KB
```

---

## 调试技巧

### 启用详细日志

```bash
python -m uvicorn main:app --reload --log-level debug
```

### 使用 curl 的 verbose 模式

```bash
curl -v http://localhost:8000/workflows
```

### 查看响应头

```bash
curl -i http://localhost:8000/workflows
```

### 保存响应到文件

```bash
curl http://localhost:8000/workflows > response.json
```

---

## 总结

本文档提供了所有 API 端点的完整测试方案，包括：

- ✅ cURL 命令示例
- ✅ Python 测试脚本
- ✅ Postman 集合
- ✅ pytest 单元测试
- ✅ 自动化测试框架
- ✅ 性能测试方案
- ✅ 调试技巧

根据需要选择合适的测试方式！
