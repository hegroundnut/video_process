

class SPullLocal:
    def __init__(self, node_cfg):
        self.node_cfg = node_cfg

    def get_stream_url(self):
        """返回本地流地址"""
        return self.node_cfg.get("url", "")