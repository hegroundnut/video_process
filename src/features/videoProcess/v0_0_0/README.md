# Video Process Feature v0.0.0

## 模块说明
本模块负责视频流的拉取、AI 算法处理（如 YOLO 目标检测）以及处理后视频流的推送或结果存储。

## 目录结构
- `videoProcess.py`: 工具入口类 `CvideoProcess`
- `main.py`: FastAPI 服务入口，提供统一的 API 路由
- `core/`: 核心业务逻辑
  - `manager.py`: 任务管理器 `VideoProcessManager`
- `config/`: 配置文件
- `models/`: 模型相关
- `utils/`: 工具函数

## API 说明

### 统一入口
`POST /api/videoProcess/CvideoProcess/{subfunc}`

### 子功能列表

| subfunc | 说明 | 参数示例 |
| :--- | :--- | :--- |
| `start_task` | 启动视频处理任务 | `{"pull_source": "local", "pull_url": "...", "models_cfg": [...], "output_type": "stream"}` |
| `get_result` | 获取任务状态及结果 | `{"task_id": "..."}` |
| `list_tasks` | 列出所有正在运行或已完成的任务 | `{}` |
| `stop_task` | 停止并删除指定任务 | `{"task_id": "..."}` |
| `get_stream_url` | 获取任务的输出流地址 | `{"task_id": "..."}` |

## 参数详细说明

### start_task
- `tool_package_snumber`: 工具包编号
- `version`: 版本号
- `pull_source`: 输入源类型 (`local`, `uva`)
- `pull_url`: 输入流地址
- `pull_type`: 输入流协议类型
- `models_cfg`: 模型配置列表，包含 `model_folder`, `model_name`, `type`
- `output_type`: 输出类型 (`stream`, `json`, `mysql`)
- `stream_push_mode`: 推流模式
- `stream_push_url`: 推流地址
