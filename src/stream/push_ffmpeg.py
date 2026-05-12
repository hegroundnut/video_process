
import logging
import subprocess
import cv2

class FFmpegStreamer:
    def __init__(self, output_url,):
        self.output_url = output_url
        self.frame_width = 0
        self.frame_height = 0
        self.fps = 0
        self.process = None
        self.is_running = False

    def set_frame_info(self, frame_width, frame_height, fps):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.fps = fps

    def start(self):
        """启动FFmpeg进程用于RTMP流输出"""
        command = [
            'ffmpeg',
            '-re',  # 按照输入帧率读取，对于实时流很重要
            '-f', 'rawvideo',
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.frame_width}x{self.frame_height}',
            '-r', str(self.fps),
            '-i', '-',  # 从标准输入读取

            # 编码参数控制
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-preset', 'medium',  # veryfast更好的质量 ultrafast
            '-tune', 'film',  # 零延迟模式为zerolatency
            '-profile:v', 'high',
            '-level', '5.2',


            # 高级码率控制
            '-crf', '20',  # 更高质量
            '-maxrate', '4000k',
            '-bufsize', '8000k',
            '-x264opts', 'keyint=60:min-keyint=60:no-scenecut',  # 高级x264选项

            '-g', '30',  # GOP大小
            '-keyint_min', '30',  # 最小关键帧间隔
            '-f', 'flv',
            self.output_url
        ]

        try:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.is_running = True

        except Exception as e:
            logging.error(f"启动FFmpeg失败: {e}")
            self.is_running = False

    def write_frame(self, frame):
        """向FFmpeg进程写入一帧"""
        if self.is_running and self.process:
            try:
                # 调整帧大小以确保一致性
                if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))

                self.process.stdin.write(frame.tobytes())
                return True
            except Exception as e:
                logging.error(f"写入帧时出错: {e}，尝试重连")
                self.stop()
                self.start()
                return False
        return False

    def stop(self):
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            finally:
                self.process = None
        self.is_running = False
        logging.info("FFmpeg流输出已停止")