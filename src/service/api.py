from fastapi import APIRouter
from .task_manager import TaskManager


router = APIRouter()
task_manager = TaskManager()


@router.post("/start_task")
def start_task(param:dict):
    # 组装 models_cfg 数组
    models_cfg = []
    i = 0
    while f"model_folder_{i}" in param:
        models_cfg.append({
            "model_folder":   param.get(f"model_folder_{i}"),
            "model_name":     param.get(f"model_name_{i}"),
            "type":           param.get(f"model_type_{i}"),
        })
        i += 1

    pull_cfg = {"source": param.get('pull_source',''),
                "url": param.get('pull_url',''),
                "type": param.get('pull_type','')}
    push_cfg = {}
    if param.get('output_type') == 'stream':
        push_cfg = {
            "mode":        param.get('stream_push_mode'),
            "type":        param.get('stream_push_type'),
            "srs_addr":    param.get('stream_push_srs_addr'),
            "srs_port":    param.get('stream_push_srs_port'),
            "stream_key":  param.get('stream_push_stream_key'),
            "url":         param.get('stream_push_url')
        }
    else:
        pass
    task_id, output = task_manager.start_task(
        param.get('tool_package_snumber'), param.get('version'), pull_cfg, models_cfg, push_cfg, param.get('output_type')
    )
    return {"code": 200,
            "msg": "任务开始成功",
            "data": {"task_id": task_id, **output}}

@router.post("/get_result")
def get_result(param:dict):
    return { "code": 200,
             "msg": "结果查询成功",
             "data": task_manager.get_result(param.get('task_id'))}

@router.post("/list_tasks")
def list_tasks():
    return { "code": 200,
             "msg": "任务列表查询成功",
             "data": task_manager.list_tasks()}

@router.post("/stop_task")
def stop_task(param:dict):
    return { "code": 200,
             "msg": "任务结束并删除成功",
             "data": task_manager.stop_task(param.get('task_id'))}

@router.post("/get_stream_url")
def get_stream(param:dict):
    return { "code": 200,
             "msg": "任务结束并删除成功",
             "data": task_manager.get_stream_url(param.get('task_id'))}