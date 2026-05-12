import os
import sys
import json
import logging

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

from core.manager import VideoProcessManager

class CvideoProcess:
    """
    视频处理工具入口类。
    """

    def __init__(self, node_cfg, process_comm, proc_modules_obj, progress_callback):
        self.node_cfg = node_cfg
        self.process_comm = process_comm
        self.proc_modules_obj = proc_modules_obj
        self.progress_callback = progress_callback

        self._manager = VideoProcessManager()

    def _handle_result(self, func_name, result):
        if result.get("code", -1) == 0:
            self.progress_callback(
                100,
                json.dumps(result, ensure_ascii=False, default=str),
                "ok",
            )
        else:
            self.progress_callback(
                -1,
                json.dumps(result, ensure_ascii=False, default=str),
                "failed",
            )
        return result

    def start_task(self, params):
        """开始视频处理任务"""
        self.progress_callback(10, "正在启动视频处理任务")
        result = self._manager.start_task(params)
        return self._handle_result("start_task", result)

    def get_result(self, params):
        """获取任务结果"""
        self.progress_callback(10, "正在查询任务结果")
        result = self._manager.get_result(params)
        return self._handle_result("get_result", result)

    def list_tasks(self, params):
        """列出所有任务"""
        self.progress_callback(10, "正在查询任务列表")
        result = self._manager.list_tasks(params)
        return self._handle_result("list_tasks", result)

    def stop_task(self, params):
        """停止视频处理任务"""
        self.progress_callback(10, "正在停止任务")
        result = self._manager.stop_task(params)
        return self._handle_result("stop_task", result)

    def get_stream_url(self, params):
        """获取流地址"""
        self.progress_callback(10, "正在获取流地址")
        result = self._manager.get_stream_url(params)
        return self._handle_result("get_stream_url", result)
