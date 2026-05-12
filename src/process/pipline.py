import queue

from .process_frame import PProcessFrame
import cv2
import logging
import threading
import time

class PPipeline(object):
    def __init__(self, cfg, pull_stream,push_stream):
        self.cfg = cfg
        self.pull_stream = pull_stream
        self.push_stream = push_stream
        self.is_processing = False

        # 使用有界队列防止内存溢出
        self.frame_queue = queue.Queue(maxsize=200)  # 原始帧队列
        self.processed_queue = queue.Queue(maxsize=200)  # 处理后的帧队列

    def frame_reader_thread(self, cap):
        """高速读取帧线程"""
        logging.info("帧读取线程启动")

        while self.is_processing:
            try:
                success, frame = cap.read()
                if not success:
                    time.sleep(0.01)  # 极短等待
                    continue
                self.frame_queue.put(frame)

            except Exception as e:
                logging.error(f"读取帧错误: {e}")
                time.sleep(0.01)

        logging.info("帧读取线程退出")

    def frame_processor_thread(self, process_list):
        """高速处理帧线程"""
        logging.info("帧处理线程启动")

        while self.is_processing:
            try:
                # 获取帧
                try:
                    frame = self.frame_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.01)  # 队列空时短暂睡眠
                    continue

                # 处理帧
                try:
                    processed_frame = frame.copy()
                    for process in process_list:
                        processed_frame = process.process(processed_frame)

                    # 立即放入处理队列
                    self.processed_queue.put(processed_frame)

                except Exception as e:
                    logging.error(f"处理帧时出错: {e}")

                self.frame_queue.task_done()

            except Exception as e:
                logging.error(f"处理线程错误: {e}")
                time.sleep(0.01)

        logging.info("帧处理线程退出")

    def frame_writer_thread(self):
        """高速推送帧线程 - 有帧即推"""
        logging.info("帧推送线程启动")

        while self.is_processing:
            try:
                # 获取处理后的帧
                try:
                    processed_frame = self.processed_queue.get_nowait()
                except queue.Empty:
                    time.sleep(0.01)  # 队列空时短暂睡眠
                    continue
                try:
                    if not self.push_stream.write_frame(processed_frame):
                        time.sleep(1)

                except Exception as e:
                    logging.error(f"推送帧时出错: {e}")

                self.processed_queue.task_done()

            except Exception as e:
                logging.error(f"推送线程错误: {e}")
                time.sleep(0.01)
        logging.info("帧推送线程退出")

    def start(self, ):
        cap = cv2.VideoCapture(self.pull_stream.get_stream_url(),cv2.CAP_FFMPEG)

        if not cap.isOpened():
            raise ConnectionError("无法打开视频流")

        # 获取视频流属性
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 25

        # 格式化流输出
        self.push_stream.set_frame_info(frame_width, frame_height, fps)
        self.push_stream.start()

        self.is_processing = True

        try:
            process_list = [] # 模型列表
            # 根据cfg，将所有模型初始化并加入列表
            for model_cfg in self.cfg:
                process_frame = PProcessFrame(model_cfg)
                process_list.append(process_frame)

            # 启动三个工作线程
            reader_thread = threading.Thread(target=self.frame_reader_thread, args=(cap,))
            processor_thread = threading.Thread(target=self.frame_processor_thread, args=(process_list,))
            writer_thread = threading.Thread(target=self.frame_writer_thread)

            # 设置为守护线程
            reader_thread.daemon = True
            processor_thread.daemon = True
            writer_thread.daemon = True

            # 启动线程
            reader_thread.start()
            processor_thread.start()
            writer_thread.start()

            while self.is_processing and (
                    reader_thread.is_alive()
                    or processor_thread.is_alive()
                    or writer_thread.is_alive()
            ):
                time.sleep(0.5)



        except Exception as e:
            logging.error(f"处理视频流时发生错误: {e}")
        finally:
            self.is_processing = False
            cap.release()
            self.push_stream.stop()
            cv2.destroyAllWindows()
            logging.info("视频流处理已停止")

    def stop(self, ):
        self.is_processing = False

