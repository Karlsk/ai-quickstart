from fastapi import FastAPI, HTTPException
from pydantic import BaseModel as PydanticBaseModel
from typing import Dict, Any
from pydantic import Field

from dynamic_graph import WorkflowDefinition, WORKFLOW_REGISTRY, build_and_register_workflow, load_and_run_workflow

# 假设所有的核心逻辑 (build_and_register_workflow, load_and_run_workflow)
# 都在上面的一个名为 graph_builder.py 的文件中

app = FastAPI(title="Dynamic LangGraph Workflow API")


# --- 辅助模型 ---
class ExecuteInput(PydanticBaseModel):
    input_data: Dict[str, Any] = Field(..., description="工作流的初始输入数据")


# --- API 路由 ---

@app.post("/workflows", status_code=201)
async def create_or_update_workflow(definition: WorkflowDefinition):
    """
    创建或更新一个动态工作流。
    工作流定义将被编译并存储在注册表中。
    """
    try:
        workflow_id = build_and_register_workflow(definition)
        return {"message": f"Workflow '{workflow_id}' created/updated successfully.", "workflow_id": workflow_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create workflow: {e}")


@app.get("/workflows/{workflow_id}")
async def get_workflow_definition(workflow_id: str):
    """
    获取已注册工作流的定义。
    """
    if workflow_id in WORKFLOW_REGISTRY:
        # 返回工作流的基本信息
        return {"workflow_id": workflow_id, "status": "Registered", "message": "Workflow is compiled and ready to execute"}

    raise HTTPException(status_code=404, detail=f"Workflow ID '{workflow_id}' not found.")


@app.post("/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, execution_input: ExecuteInput):
    """
    执行一个已注册的工作流。
    """
    try:
        result = load_and_run_workflow(workflow_id, execution_input.input_data)
        return {"workflow_id": workflow_id, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # 更详细的错误处理，例如 LangChain 运行时的错误
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {e}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
