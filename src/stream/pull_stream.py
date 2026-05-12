from .pull_uva import SPullUVA
from .pull_local import SPullLocal


'''
从uva拉流过一遍
从local拉流直接返回
'''
class SPullStream:
    def __init__(self, node_cfg):
        self.node_cfg = node_cfg
        self.pull_stream = None
        self._initialize_pull_stream()

    def _initialize_pull_stream(self):
        """根据配置初始化对应的拉流实例"""
        source = self.node_cfg.get("source", "").lower()

        if source == "local":
            self.pull_stream = SPullLocal(self.node_cfg)
        elif source == "uva":
            self.pull_stream = SPullUVA(self.node_cfg)
        else:
            raise ValueError(f"不支持的拉流源类型: {source}")

    def get_stream_url(self):
        """获取流地址"""
        if self.pull_stream is None:
            raise RuntimeError("拉流实例未初始化")
        return self.pull_stream.get_stream_url()