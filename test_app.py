import yaml


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

# test_app.py
import uvicorn
from fastapi import FastAPI
from src.service.api import router

app = FastAPI(title="Video AI Service", version="1.0")
app.include_router(router)

if __name__ == "__main__":
    print('1232131232312')
    print('1232131232312')
    print('1232131232312')
    uvicorn.run(app, host="0.0.0.0", port=13212)
