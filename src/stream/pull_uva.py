import requests


class SPullUVA:
    """
    无人机视频连接类
    负责根据配置调度
    """
    def __init__(self, node_cfg):
        self.node_cfg = node_cfg

    def get_stream_url(self):
        """请求 API 获取无人机流地址"""
        url = self.node_cfg["url"]
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                if self.node_cfg["type"] == "rtmp":
                    return data["data"]["drone_rtmp_url"]
                elif self.node_cfg["type"] == "webrtc":
                    return data["data"]["drone_webrtc_url"]

            else:
                print(f"[ERROR] 请求失败: {data.get('message')}")
        except Exception as e:
            print(f"[ERROR] 请求异常: {e}")
        return None
