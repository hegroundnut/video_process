import time

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from ultralytics import YOLO
import json
import os
from datetime import datetime
from minio import Minio
from minio.error import S3Error
from src.Util import *
from io import BytesIO

class CApp:
    def __init__(self):
        """
        初始化视频处理服务：提取有效图片（分类检测）

        参数:
            minio_endpoint: MinIO服务器地址 (e.g. "116.62.238.72:9000")
            minio_access_key: MinIO访问密钥
            minio_secret_key: MinIO秘密密钥
            bucket_name: 目标存储桶名称
            secure: 是否使用HTTPS (默认False)
            input_path: minio存储地址
            out_path: minio输出地址
        """
        self.minio_endpoint = None
        self.minio_access_key = None
        self.minio_secret_key = None
        self.bucket_name = None
        self.input_path = None
        self.out_path = None
        self.model_path =None
        self.deal_percent = 0 # 进度, 一定存在
        self.groups_id = None # 查询当前应该创建到哪个group-xxx
        self.group_num = 0 # 当前group-xxx下有多少个数据
        self.deal_time = None # 处理时间, 不一定存在
        self.deal_msg = None # 处理信息, 不一定存在

    """
    检查groups_id是否存在，不存在则创建
    """
    def check_groups_id(self):
        all_groups = []
        prefix_path = "/AIDataManage/" # 计算要保存到minio的哪里
        all_group_objects = self.minio_client.list_objects(self.bucket_name, prefix=prefix_path)
        for item in all_group_objects:
            all_groups.append(item.object_name)
        groups_id = get_next_group_id(all_groups)
        return groups_id
    
    def check_groups_num(self):
        obj = self.minio_client.list_objects(self.bucket_name, prefix="AIDataManage/ImgObjRecognition/" + self.groups_id + "/src-img/")
        cnt = 0
        for _ in obj:
            cnt += 1
        return cnt

    def Init(self, param):
        """
        param:传入内容
        """
        # 1. 初始化配置
        try:
            # minio_endpoint = param['minio_endpoint'],
            # minio_access_key=param['minio_access_key'],
            # minio_secret_key=param['minio_secret_key'],
            # self.bucket_name=param['bucket_name']
            self.input_path = param['input_path']

        except Exception as e:    
            self.input_path = "src/tools/data/11.mp4"
        finally:
            # 2. 初始化MinIO客户端
            minio_endpoint = "192.168.2.109:9000"
            minio_access_key = "admin"
            minio_secret_key = "Letseatbone874"
            self.bucket_name = "ds-data-ware"
            self.minio_client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False
            )
            # 自用, 外部不可改变
            self.groups_id = self.check_groups_id() # 查询当前应该创建到哪个group-xxx
            self.group_num = self.check_groups_num() # 当前group-xxx下有多少个数据
            self.out_path = "src/tools/out"
            self.cache_path = "src/tools/datacache"
            self.model_predict_path = "src/tools/predict_model/" # 预测模型的地址, 事先存放好

    def StartTask(self, param):
        
        # 参数解析
        funname = param["dtype"]
        if funname == "vedio-split" :
            self.StartTask_GetImgFromVedioAndRecognition(param)
        elif funname == "label-combine" :
            self.StartTask_LabelCombine(param)
        elif funname == "group-combine" :
            self.StartTask_LabelCombine(param)
        elif funname == "video-people-count" :
            self.StartTask_VideoPeopleCount(param)
        
        print("\nProcessing completed")

    def StartTask_VideoPeopleCount(self,param):
        """
        处理视频流
        从视频流持续的读视频帧，通过yolo处理，并将其保存到本地，推送到输出视频流
        :param stream_source: 视频流来源（摄像头索引/RTSP/HTTP流地址）
        :param output_path: 输出文件路径（可选）
        :param push_stream: 推流地址（可选，如 rtmp://localhost/live/stream）
        """
        stream_source = param.get("stream_source")
        push_stream = param.get("push_stream")
        model = YOLO('{}yolov8n.pt'.format(self.model_predict_path))
        if stream_source is None or stream_source == "":
            return

        cap = cv2.VideoCapture(stream_source)
        if not cap.isOpened():
            raise ConnectionError("无法打开视频流")

        # 获取视频流属性
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        # 初始化推流器（可选）
        # 需要安装额外库如 ffmpeg-python
        if push_stream:
            import subprocess
            ffmpeg_cmd = [
                'ffmpeg',
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'bgr24',
                '-s', f'{frame_width}x{frame_height}',
                '-r', str(fps),
                '-i', '-',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-f', 'flv',
                push_stream
            ]
            ffmpeg_process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

        try:
            while True:
                success, frame = cap.read()
                if not success:
                    for count in range(5):
                        cap.release()
                        cap = cv2.VideoCapture(stream_source)
                        if cap.isOpened():
                            break
                    else:
                        self.deal_time = time.time()
                        self.deal_msg = "视频流中断，无法连接，退出..."
                        break
                    continue

                # YOLO 推理
                results = model(frame)
                # 获取检测结果
                detections = results[0].boxes
                people_count = 0
                # 遍历检测到的物体
                for box in detections:
                    # 获取边框坐标
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # [x1, y1, x2, y2]
                    conf = box.conf[0]  # 置信度
                    cls = int(box.cls[0])  # 类别索引

                    # 过滤出人类检测（YOLO类索引0通常代表人）
                    if cls == 0:  # 可调整置信度阈值
                        people_count += 1
                        # 在图像上绘制边框
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, "Person", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 显示当前计数
                cv2.putText(frame, f'Count: {people_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                # 推流到服务器
                if push_stream:
                    ffmpeg_process.stdin.write(frame.tobytes())

        finally:
            cap.release()
            if push_stream:
                ffmpeg_process.stdin.close()
                ffmpeg_process.wait()
            cv2.destroyAllWindows()

    def StartTask_GetImgFromVedioAndRecognition(self,param):
        """
        param:传入内容
        """
        # 加载模型
        cls_model = YOLO('{}yolov8x-cls.pt'.format(self.model_predict_path))
        det_model = YOLO('{}yolov8n.pt'.format(self.model_predict_path))
        threshold = 0.8

        # 打开视频文件
        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            raise ValueError("Error opening video file")

        # 初始化对照帧
        ret, prev_frame = cap.read()
        if not ret:
            raise ValueError("Error reading initial frame")

        frame_count = 0

        while True:
            ret, current_frame = cap.read()
            if not ret:
                break

            frame_count += 1
            if frame_count % 24 != 0:  # 每24帧处理一次
                continue
            print(f"\nProcessing frame {frame_count}")

            # 步骤1：帧相似度比较
            similarity = self.calculate_frame_similarity(prev_frame, current_frame)
            print(f"SSIM similarity: {similarity:.4f}")

            if similarity < threshold:
                try:
                    # 步骤2：图像分类
                    class_name = self.classify_image(current_frame, cls_model)
                    print(f"Classification result: {class_name}")

                    # 步骤3：目标检测
                    detection_result = self.detect_objects(current_frame, det_model)
                    
                    # 保存结果
                    self.save_results(
                        current_frame, 
                        detection_result["has_detections"],
                        detection_result["detections"],
                        class_name,
                        self.out_path,
                        det_model)
                    self.group_num += 1 # 这个分组当前的格式数+1
                    # 更新对照帧
                    prev_frame = current_frame.copy()

                except Exception as e:
                    print(f"Processing error: {str(e)}")
            else:
                print("Frame skipped (similarity above threshold)")

        cap.release()

    def StartTask_LabelCombine(self,param):
        print("")
    
    def StartTask_GroupCombine(self,param):
        print("")


    def GetNodeInfo(self):
       """
       @param: None 你这个工具能力的一个描述
       """
       return """
       我可以执行Dlib人脸关键点检测模型的训练
       
       dtype == video-people-count:
       从视频流持续的读视频帧，通过yolo处理检测人流量，推送到输出视频流
        :param stream_source: 视频流来源（摄像头索引/RTSP/HTTP流地址）
        :param push_stream: 推流地址（可选，如 rtmp://localhost/live/stream）
       """
    
    def GetTaskExecInfo(self):
        """
        @param: None 这里是要返回的执行进度等其他信息
        """
        return {
            "taskProcessingVal": self.deal_percent,
            "deal_time": self.deal_time,
            "deal_msg": self.deal_msg
        }

    def Cleanup(self):
        """
        @param: None 你保存的第三方处理过程
        """
        print("清理任务")
    
    def calculate_frame_similarity(self, frame1, frame2):
        """计算两帧之间的结构相似性指数（SSIM）"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        score, _ = ssim(gray1, gray2, full=True)
        return score

    def classify_image(self, frame, model):
        """使用YOLO分类模型进行图像分类"""
        results = model(frame)
        class_id = results[0].probs.top1
        return results[0].names[class_id]

    def detect_objects(self, frame, model):
        """使用YOLO检测模型进行目标检测"""
        results = model(frame)
        boxes = results[0].boxes
        # 判断是否存在有效检测
        has_detections = len(boxes.cls) > 0  # 通过类别ID的数量判断

        return {
            "annotated_frame": results[0].plot(),
            "detections": boxes,
            "has_detections": has_detections
        }

    def _upload_to_minio(self, object_name, image_data):
        """上传图片数据到MinIO桶"""
        try:
            image_stream = BytesIO(image_data)
            self.minio_client.put_object(
                self.bucket_name,
                object_name,
                image_stream,
                length=len(image_data),
                content_type='image/jpeg'
            )
            return True
        except S3Error as e:
            print(f"上传到MinIO失败: {e}")
            return False
    
    def results_uploadminio(self,frame):
        self._upload_to_minio()
        
    def save_results(self, frame, has_detections, detections, class_name, output_dir, det_model):
        """保存处理结果（图片+JSON），按类别分文件夹存储
        
        目录结构：
        output_dir/
        ├── images/
        │   ├── class1/
        │   │   ├── class1_20230512103000_001.jpg
        │   │   └── ...
        │   ├── class2/
        │   │   └── ...
        │   └── ...
        └── labels/
            ├── class1/
            │   ├── class1_20230512103000_001.json
            │   └── ...
            ├── class2/
            │   └── ...
            └── ...
        """
        # 创建基础目录结构
        images_dir = os.path.join(output_dir, "images")
        labels_dir = os.path.join(output_dir, "labels")

        # 检查并创建目录（如果不存在）
        for dir_path in [images_dir, labels_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created directory: {dir_path}")   

        # 创建类别子目录
        class_images_dir = os.path.join(images_dir, class_name)
        class_labels_dir = os.path.join(labels_dir, class_name)

        # 检查并创建类别子目录（如果不存在）
        for dir_path in [class_images_dir, class_labels_dir]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                print(f"Created class directories for: {class_name}")

        # 生成统一文件名（不含扩展名）
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S") # 时间戳
        base_name = f"{class_name}_{timestamp}" # 处理的文件名称
        
        self.deal_msg = base_name
        self.deal_time = timestamp
        if self.group_num > 999:
            self.groups_id = auto_incre_group(self.groups_id)
            self.group_num = 0

        # 1. 保存图片到类别目录
        img_path = os.path.join(class_images_dir, f"{base_name}.jpg")
        cv2.imwrite(img_path, frame)
        local_file_jpg = img_path # 本地图片路径
        remote_file_jpg = "AIDataManage/ImgObjRecognition/" + self.groups_id + "/src-img/" + f"{base_name}.jpg" # 远程存储路径
        width = frame.shape[1]
        height = frame.shape[0]
        # 2. 准备JSON数据    
        if has_detections:
            json_data = []
            for box in detections:
                # 获取坐标、置信度和类别ID
                xyxy = box.xyxy.cpu().tolist()[0]  # 转换为列表格式
                cls_id = box.cls.item()             # 类别ID
                cls_name = det_model.names[int(cls_id)] # 类别名称

                xywh = xyxy_to_xywh(xyxy)
                json_data.append({
                    "original_width": width, 
                    "original_height": height, 
                    "image_rotation": 0, 
                    "value": {
                        "x": xywh[0] / width * 100, 
                        "y": xywh[1] / height * 100, 
                        "width": xywh[2] / width * 100, 
                        "height": xywh[3] / height * 100, 
                        "rotation": 0, 
                        "rectanglelabels": [
                            cls_name
                        ]
                    }, 
                    "id": "WjCgZ2_TNw", 
                    "from_name": "label", 
                    "to_name": "img-1", 
                    "type": "rectanglelabels", 
                    "origin": "manual"
                })

            final_format = {
                "data": 
                { 
                    "img": "s3://ds-data-ware/AIDataManage/{}/{}/{}/{}".format("ImgObjRecognition", self.groups_id, "src-img", base_name+".jpg")},
                "annotations": [],
                "predictions": 
                [
                    {
                        "result": json_data
                    }
                ]
            }

            # 保存JSON到对应的labels类别目录（与图片同名）
            json_path = os.path.join(class_labels_dir, f"{base_name}.json")
            with open(json_path, 'w') as f:
                json.dump(final_format, f, indent=2)


            # 3. 获取group-xxx的这个xxx, 然后建立xxx
            local_file_json = json_path  # 本地json路径
            remote_file_json = "AIDataManage/ImgObjRecognition/" + self.groups_id + "/src-label/" + f"{base_name}.json" # 远程json路径

            # 4. 上传到minio
            """
            -----group-001
            |--src-img
            |--src-label
            |--dst-label
            -----group-002
            |--src-img
            |--src-label
            |--ds
            """
            self.minio_client.fput_object(self.bucket_name, remote_file_jpg, local_file_jpg)
            self.minio_client.fput_object(self.bucket_name, remote_file_json, local_file_json)

            # 5. 删除jpg和json
            os.remove(local_file_jpg)
            os.remove(local_file_json)
