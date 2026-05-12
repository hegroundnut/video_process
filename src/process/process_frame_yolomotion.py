import cv2
import os

from ultralytics import YOLO


try:
    import torch
    _TORCH_AVAILABLE = True
    _CUDA_AVAILABLE = torch.cuda.is_available()
except Exception:
    _TORCH_AVAILABLE = False
    _CUDA_AVAILABLE = False

class PProcessFrameYOLOMotion(object):
    def __init__(self, cfg, ):
        self.cfg = cfg

        self.model_path = os.path.join(self.cfg.get("model_folder"), self.cfg.get("model_name"))
        self.model = YOLO(self.model_path)
        self.device = "cuda:0" if _CUDA_AVAILABLE else "cpu"
        self.model.to(self.device)


    def process(self, frame):
        people_count = 0

        # YOLO 推理
        results = self.model(frame,verbose=False)
        # 获取检测结果
        detections = results[0].boxes
        # 初始化背景减除
        backSub = cv2.createBackgroundSubtractorMOG2()
        # 进行背景减除
        fg_mask = backSub.apply(frame)
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 遍历检测到的物体
        for box in detections:
            # 获取边框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # [x1, y1, x2, y2]
            conf = box.conf[0]  # 置信度
            cls = int(box.cls[0])  # 类别索引

            # 过滤出人类检测（YOLO类索引0通常代表人）并检查移动
            if cls == 0:  # 可调整置信度阈值
                # 检查每个检测的人是否在移动
                moving = False
                for contour in contours:
                    if cv2.contourArea(contour) > 100:  # 只考虑较大的轮廓
                        if cv2.pointPolygonTest(contour, (x1 + (x2 - x1) // 2, y1 + (y2 - y1) // 2),
                                                False) >= 0:
                            moving = True
                            break

                if moving:
                    people_count += 1
                    # 在图像上绘制边框
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 显示当前计数
        cv2.putText(frame, f'Count: {people_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        return frame