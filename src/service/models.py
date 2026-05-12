from typing import List, Optional
from pydantic import BaseModel

class PullStreamCfg(BaseModel):
    source: str
    url: str
    type: str

class ModelCfg(BaseModel):
    model_folder: str
    model_name: str
    type: str
    description: Optional[str] = ""

class PushStreamCfg(BaseModel):
    mode: str
    type: str
    srs_addr: str
    srs_port: int
    stream_key: str
    url: Optional[str] = None

class StartTaskRequest(BaseModel):
    tool_package_snumber: str
    version: str
    pull_stream_cfg: PullStreamCfg
    models_cfg: List[ModelCfg]
    push_stream_cfg: PushStreamCfg
    output_type: str   # stream/json/mysql