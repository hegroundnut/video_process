
from .push_ffmpeg import FFmpegStreamer

class SPushStream:
    def __init__(self, node_cfg):
        self.node_cfg = node_cfg
        self.push_stream = None
        self._initialize_push_stream()

    def _initialize_push_stream(self):

        forward = self.node_cfg.get("mode", "").lower()

        if forward == "ffmpeg":
            self.push_stream = FFmpegStreamer(self.node_cfg.get("url", ""))
        else:
            raise ValueError(f"不支持的推流源类型: {forward}")


    def start(self):
        if self.push_stream is None:
            raise RuntimeError("推流实例未初始化")
        self.push_stream.start()

    def write_frame(self, frame):
        if self.push_stream is None:
            raise RuntimeError("推流实例未初始化")
        self.push_stream.write_frame(frame)

    def stop(self):
        if self.push_stream is None:
            raise RuntimeError("推流实例未初始化")
        self.push_stream.stop()

    def set_frame_info(self, frame_width, frame_height, fps):
        if self.push_stream is None:
            raise RuntimeError("推流实例未初始化")
        self.push_stream.set_frame_info(frame_width, frame_height, fps)
