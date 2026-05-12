import time
import threading

from typing import List, Tuple, Dict, Any
from ..stream.pull_stream import SPullStream
from ..stream.push_stream import SPushStream
from ..process.pipline import PPipeline



class TaskManager:
    def __init__(self):
        # task_id -> {"thread": Thread, "pipeline": PPipeline, "status": str, "info": dict}
        self.tasks: Dict[str, Dict[str, Any]] = {}

    def start_task(self, tool_package_snumber, version, pull_cfg, models_cfg, push_cfg, output_type="stream"):
        task_id = f"{tool_package_snumber}-{int(time.time())}"

        # 拼接 url
        if not push_cfg.get("url"):
            addr = push_cfg.get("srs_addr", "localhost")
            port = push_cfg.get("srs_port", 1935)
            key = push_cfg.get("stream_key", "detected")
            push_cfg["url"] = f"rtmp://{addr}:{port}/live/{key}"

        pull_stream = SPullStream(pull_cfg)

        if output_type == "stream":
            push_stream = SPushStream(push_cfg)
            pipeline = PPipeline(models_cfg, pull_stream, push_stream)

            def run_pipeline():
                try:
                    pipeline.start()
                    # 如果 pipeline.start 正常返回，说明任务完成
                    self.tasks[task_id]["status"] = "finished"
                except Exception as e:
                    # 捕获异常，标记错误
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
            return task_id, {"output_url": push_cfg["url"]}

        elif output_type == "json":
            self.tasks[task_id] = {
                "tool_package_snumber": tool_package_snumber,
                "version": version,
                "status": "finished",
                "thread": None,
                "pipeline": None,
                "info": {"result_api": f"/get_result/{task_id}"}
            }
            return task_id, {"result_api": f"/get_result/{task_id}"}

        elif output_type == "mysql":
            self.tasks[task_id] = {
                "tool_package_snumber": tool_package_snumber,
                "version": version,
                "status": "finished",
                "thread": None,
                "pipeline": None,
                "info": {"mysql_table": task_id}
            }
            return task_id, {"mysql_table": task_id}
        else:
            return task_id, None

    def get_result(self, task_id: str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "task not found"}
        return {"status": task["status"], **task["info"]}

    def list_tasks(self) -> List[Dict[str, Any]]:
        """查看所有任务"""
        return [
            {"task_id": tid, "status": t["status"], **t["info"]}
            for tid, t in self.tasks.items()
        ]

    def stop_task(self, task_id: str) -> Dict[str, Any]:
        """结束任务"""
        task = self.tasks.get(task_id)
        if not task:
            return {"error": "task not found"}

        pipeline = task.get("pipeline")
        if pipeline and hasattr(pipeline, "stop"):
            pipeline.stop()  # 需要你在 PPipeline 里实现 stop() 方法
        task["status"] = "stopped"
        self.tasks.pop(task_id)
        return {"task_id": task_id, "status": "stopped"}

    def get_stream_url(self,task_id:str) -> Dict[str, Any]:
        task = self.tasks.get(task_id)
        task.get()