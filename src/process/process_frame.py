from .process_frame_yolo import PProcessFrameYOLO
from .process_frame_yolomotion import PProcessFrameYOLOMotion

class PProcessFrame(object):
    def __init__(self, cfg,):
        self.cfg = cfg
        self.process_model = None
        self._initialize_process()
    def _initialize_process(self):
        ty = self.cfg.get("type","")

        if ty == "yolo":
            self.process_model = PProcessFrameYOLO(self.cfg)
        elif ty == "yolomotion":
            self.process_model = PProcessFrameYOLOMotion(self.cfg)
        else:
            raise ValueError(f"不支持的操作: {ty}")

    def process(self, frame):
        if self.process_model is None:
            raise RuntimeError("模型实例未初始化")
        return  self.process_model.process(frame)