# 项目架构文档

## 📁 项目结构

```
advance_aiops_v2/
├── main.py                          # FastAPI 应用入口
│   ├── 创建 FastAPI 实例
│   ├── 注册中间件（CORS）
│   ├── 注册路由
│   └── 定义生命周期事件
│
├── app/                             # API 应用包
│   ├── __init__.py                 # 包初始化，导出公共接口
│   ├── api_schema.py               # API 数据模型（请求/响应）
│   ├── service.py                  # 业务逻辑层
│   └── routes.py                   # API 路由定义
│
├── workflow/                        # 工作流核心模块
│   ├── models.py                   # 工作流数据模型
│   ├── base_node.py               # 节点基类和工厂函数
│   └── graph_builder.py           # 工作流图构建器
│
├── demo_dify_style.py             # Dify 风格演示
├── demo_query_logs.py             # 日志查询演示
├── api_client_example.py          # API 客户端示例
├── test_workflow.py               # 单元测试
└── README.md, API_USAGE.md        # 文档
```

## 🏗️ 分层架构

### 1. **表示层 (main.py)**
负责：
- FastAPI 应用配置
- 中间件设置
- 路由注册
- 生命周期管理

```
HTTP 请求 → FastAPI App → 路由分发 → 业务逻辑
```

### 2. **路由层 (app/routes.py)**
负责：
- 定义所有 API 端点
- 请求验证和响应格式
- 调用服务层处理业务逻辑
- 异常处理和错误响应

```
@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    return await service.get_workflow(workflow_id)
```

### 3. **服务层 (app/service.py)**
负责：
- 业务逻辑实现
- 调用工作流注册表
- 数据转换和处理
- 错误处理

```python
class WorkflowService:
    def create_workflow(self, request: WorkflowCreateRequest):
        # 构建模型 → 调用注册表 → 返回结果
```

### 4. **模型层 (app/api_schema.py)**
负责：
- API 请求模型定义
- API 响应模型定义
- 数据验证和序列化

```python
class WorkflowCreateRequest(BaseModel):
    workflow_id: str
    nodes: List[NodeDefinitionRequest]
    ...
```

### 5. **工作流核心层 (workflow/)**
负责：
- 工作流定义和模型
- 节点创建和管理
- 图构建和执行

## 🔄 数据流

```
HTTP 请求
    ↓
main.py (路由分发)
    ↓
app/routes.py (端点处理)
    ↓
app/service.py (业务逻辑)
    ↓
workflow/ (工作流核心)
    ↓
HTTP 响应
```

## 📝 关键文件说明

### main.py
```python
# FastAPI 应用创建
app = FastAPI(...)

# 注册路由
app.include_router(router)

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动代码
    yield
    # 关闭代码
```

### app/routes.py
```python
router = APIRouter()

@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    # 调用服务
    return workflow_service.create_workflow(request)
```

### app/service.py
```python
class WorkflowService:
    def __init__(self):
        self.registry = WorkflowRegistry()
    
    def create_workflow(self, request):
        # 构建模型
        # 调用注册表
        # 返回结果
```

### app/api_schema.py
```python
class WorkflowCreateRequest(BaseModel):
    """API 请求模型"""
    workflow_id: str
    nodes: List[NodeDefinitionRequest]
    
class WorkflowResponse(BaseModel):
    """API 响应模型"""
    status: str
    message: str
```

## ✨ 架构优势

### 1. **解耦性好**
- 路由层只负责 HTTP 处理
- 服务层只负责业务逻辑
- 易于单独测试和修改

### 2. **易于维护**
- 代码职责清晰
- 修改业务逻辑不影响路由
- 修改 API 格式不影响业务逻辑

### 3. **高度可扩展**
- 容易添加新的端点
- 容易添加新的中间件
- 容易添加身份验证等功能

### 4. **便于测试**
- 服务层可以独立测试
- 路由层可以独立测试
- 支持 mock 和 stub

## 🚀 使用示例

### 启动服务器
```bash
cd advance_aiops_v2
python main.py
# 或
python -m uvicorn main:app --reload
```

### 调用 API
```bash
# 创建工作流
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{...}'

# 获取工作流详情
curl http://localhost:8000/workflows/{workflow_id}

# 执行工作流
curl -X POST http://localhost:8000/workflows/{workflow_id}/execute \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 使用 Python 客户端
```python
from app import WorkflowService

service = WorkflowService()
result = service.create_workflow(request)
```

## 📊 类图

```
main.py
  │
  ├── FastAPI (app)
  │    └── include_router(router)
  │
app/
  ├── routes.py
  │    └── @router.post("/workflows")
  │         └── calls → service
  │
  ├── service.py
  │    └── WorkflowService
  │         └── uses → WorkflowRegistry
  │
  └── api_schema.py
       ├── WorkflowCreateRequest
       └── WorkflowResponse

workflow/
  ├── models.py (数据定义)
  ├── base_node.py (节点实现)
  └── graph_builder.py (图构建)
```

## 🔌 扩展点

### 添加新的 API 端点
1. 在 `app/routes.py` 添加新的路由
2. 在 `app/service.py` 添加业务逻辑
3. 在 `app/api_schema.py` 添加数据模型

### 添加身份验证
```python
# 在 app/routes.py 中添加依赖
from fastapi import Depends

async def verify_token(token: str = Header(...)):
    # 验证逻辑
    return token

@router.get("/workflows")
async def list_workflows(token: str = Depends(verify_token)):
    ...
```

### 添加数据库支持
```python
# 在 app/service.py 中添加数据库操作
class WorkflowService:
    def __init__(self, db):
        self.db = db
    
    def save_workflow(self, workflow):
        self.db.save(workflow)
```

## 🧪 测试建议

### 单元测试
```python
# 测试服务层
def test_create_workflow():
    service = WorkflowService()
    result = service.create_workflow(request)
    assert result["status"] == "success"
```

### 集成测试
```python
# 测试 API 端点
from fastapi.testclient import TestClient

client = TestClient(app)
response = client.post("/workflows", json={...})
assert response.status_code == 200
```

## 📚 相关文档
- API_USAGE.md - API 详细文档
- README.md - 项目说明
- workflow/ - 工作流核心模块文档
