import time
import threading
from typing import List, Dict, Any
import sys
import os

# 确保可以导入 src 目录下的模块
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.abspath(os.path.join(_current_dir, "../../../../../"))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from src.stream.pull_stream import SPullStream
from src.stream.push_stream import SPushStream
from src.process.pipline import PPipeline

class VideoProcessManager:
    def __init__(self):
        # task_id -> {"thread": Thread, "pipeline": PPipeline, "status": str, "info": dict}
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def start_task(self, params: Dict[str, Any]):
        tool_package_snumber = params.get("tool_package_snumber", "unknown")
        version = params.get("version", "0.0.0")
        
        # 组装 models_cfg 数组 (兼容旧版 API 传参方式)
        models_cfg = params.get("models_cfg", [])
        if not models_cfg:
            i = 0
            while f"model_folder_{i}" in params:
                models_cfg.append({
                    "model_folder":   params.get(f"model_folder_{i}"),
                    "model_name":     params.get(f"model_name_{i}"),
                    "type":           params.get(f"model_type_{i}"),
                })
                i += 1

        pull_cfg = {
            "source": params.get('pull_source', ''),
            "url": params.get('pull_url', ''),
            "type": params.get('pull_type', '')
        }
        
        push_cfg = {}
        output_type = params.get('output_type', 'stream')
        
        if output_type == 'stream':
            push_cfg = {
                "mode":        params.get('stream_push_mode'),
                "type":        params.get('stream_push_type'),
                "srs_addr":    params.get('stream_push_srs_addr'),
                "srs_port":    params.get('stream_push_srs_port'),
                "stream_key":  params.get('stream_push_stream_key'),
                "url":         params.get('stream_push_url')
            }
            # 拼接 url
            if not push_cfg.get("url"):
                addr = push_cfg.get("srs_addr", "localhost")
                port = push_cfg.get("srs_port", 1935)
                key = push_cfg.get("stream_key", "detected")
                push_cfg["url"] = f"rtmp://{addr}:{port}/live/{key}"

        task_id = f"{tool_package_snumber}-{int(time.time())}"
        pull_stream = SPullStream(pull_cfg)

        if output_type == "stream":
            push_stream = SPushStream(push_cfg)
            pipeline = PPipeline(models_cfg, pull_stream, push_stream)

            def run_pipeline():
                try:
                    pipeline.start()
                    if task_id in self.tasks:
                        self.tasks[task_id]["status"] = "finished"
                except Exception as e:
                    if task_id in self.tasks:
                        self.tasks[task_id]["status"] = "error"
                        self.tasks[task_id]["info"]["error_msg"] = str(e)

            t = threading.Thread(target=run_pipeline, daemon=True)
            t.start()

            self.tasks[task_id] = {
                "tool_package_snumber": tool_package_snumber,
                "version": version,
                "status": "running",
                "thread": t,
                "pipeline": pipeline,
                "info": {
                    "rtmp_input_url": pull_stream.get_stream_url(),
                    "rtmp_output_url": push_cfg["url"],
                }
            }
            return {"code": 0, "msg": "任务开始成功", "data": {"task_id": task_id, "output_url": push_cfg["url"]}}

        elif output_type == "json":
            self.tasks[task_id] = {
                "tool_package_snumber": tool_package_snumber,
                "version": version,
                "status": "finished",
                "thread": None,
                "pipeline": None,
                "info": {"result_api": f"/get_result/{task_id}"}
            }
            return {"code": 0, "msg": "任务开始成功", "data": {"task_id": task_id, "result_api": f"/get_result/{task_id}"}}

        elif output_type == "mysql":
            self.tasks[task_id] = {
                "tool_package_snumber": tool_package_snumber,
                "version": version,
                "status": "finished",
                "thread": None,
                "pipeline": None,
                "info": {"mysql_table": task_id}
            }
            return {"code": 0, "msg": "任务开始成功", "data": {"task_id": task_id, "mysql_table": task_id}}
        else:
            return {"code": -1, "msg": f"不支持的输出类型: {output_type}", "data": {}}

    def get_result(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        task = self.tasks.get(task_id)
        if not task:
            return {"code": -1, "msg": "task not found", "data": {}}
        return {"code": 0, "msg": "success", "data": {"status": task["status"], **task["info"]}}

    def list_tasks(self, params: Dict[str, Any] = None) -> Dict[str, Any]:
        data = [
            {"task_id": tid, "status": t["status"], **t["info"]}
            for tid, t in self.tasks.items()
        ]
        return {"code": 0, "msg": "success", "data": data}

    def stop_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        task = self.tasks.get(task_id)
        if not task:
            return {"code": -1, "msg": "task not found", "data": {}}

        pipeline = task.get("pipeline")
        if pipeline and hasattr(pipeline, "stop"):
            pipeline.stop()
        task["status"] = "stopped"
        self.tasks.pop(task_id)
        return {"code": 0, "msg": "success", "data": {"task_id": task_id, "status": "stopped"}}

    def get_stream_url(self, params: Dict[str, Any]) -> Dict[str, Any]:
        task_id = params.get("task_id")
        task = self.tasks.get(task_id)
        if not task:
            return {"code": -1, "msg": "task not found", "data": {}}
        return {"code": 0, "msg": "success", "data": {"stream_url": task["info"].get("rtmp_output_url")}}
