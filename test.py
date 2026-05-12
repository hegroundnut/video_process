import yaml

from src.stream.pull_stream import SPullStream
from src.stream.push_stream import SPushStream
from src.process.pipline import PPipeline

def load_config(path="toolconfig.yml"):
    """加载 YAML 配置，并修正url"""
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    push_cfg = cfg.get("push_stream_cfg")
    if push_cfg and push_cfg.get("type") == "rtmp":
        addr = push_cfg.get("srs_addr", "localhost")
        port = push_cfg.get("srs_port", 1935)
        stream_key = push_cfg.get("stream_key", "live")
        # 修正url
        push_cfg["url"] = f"rtmp://{addr}:{port}/live/{stream_key}"

    return cfg

if __name__ == "__main__":

    # 读取 YAML 配置
    with open("toolconfig.yml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # 获得输入流
    pull_stream = SPullStream(config.get("pull_stream_cfg",""))

    # 创建输出流
    push_stream = SPushStream(config.get("push_stream_cfg",""))

    # 模型管道
    pipeline = PPipeline(config.get("models_cfg",[]),
                        pull_stream,push_stream)
    pipeline.start()






