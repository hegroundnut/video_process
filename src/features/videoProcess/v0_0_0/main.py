import json
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from videoProcess import CvideoProcess

app = FastAPI(title="Video Process Service")

def mock_progress_callback(progress="", message="", status=""):
    pass

# 实例化 CvideoProcess
cvideo_instance = CvideoProcess(
    node_cfg={},
    process_comm=None,
    proc_modules_obj=None,
    progress_callback=mock_progress_callback
)

@app.post("/api/videoProcess/CvideoProcess/{subfunc}")
async def handle_request(subfunc: str, request: Request):
    """
    统一转发逻辑：根据 URL 中的 subfunc 调用 CvideoProcess 类中对应的方法
    """

    # 1. 检查方法是否存在
    if not hasattr(cvideo_instance, subfunc):
        raise HTTPException(status_code=404, detail=f"Subfunc '{subfunc}' not found in CvideoProcess")

    method = getattr(cvideo_instance, subfunc)

    # 2. 检查是否为可调用的公开方法
    if not callable(method) or subfunc.startswith("_"):
        raise HTTPException(status_code=403, detail="Access to private methods is forbidden")

    # 3. 解析请求体中的 params
    try:
        params = await request.json()
    except Exception:
        params = {}

    # 4. 执行逻辑并返回结果
    try:
        result = method(params)
        return result
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"code": -1, "msg": f"Missing required parameter: {str(e)}", "data": {}}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": -1, "msg": f"Internal Error: {str(e)}", "data": {}}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=13212)
