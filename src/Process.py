from fastapi import FastAPI
from fastapi.testclient import TestClient
from .service.api import router

class CProcessor(object):
    '''

    '''

    def __init__(self, node_cfg):
        super(CProcessor, self).__init__()
        # 节点配置
        self.node_cfg = node_cfg

        # 初始化 FastAPI 应用并挂载 router
        app = FastAPI()
        app.include_router(router)
        self.client = TestClient(app)

    def ProcessTask(self, param):
        pass

    def ProcessAPI(self, apitype, apimodule, apiclass, apimethod, param):
        try:
            if apimethod == "start_task":
                return self.client.post("/start_task", json=param).json()
            elif apimethod == "get_result":
                return self.client.post("/get_result" , json=param).json()
            elif apimethod == "list_tasks":
                return self.client.post("/list_tasks").json()
            elif apimethod == "stop_task":
                return self.client.post("/stop_task" , json=param).json()
            else:
                return {"code": -1, "msg": f"Unknown method {apimethod}", "data": {}}
        except Exception as e:
            return {"code": -1, "msg": f"Exception {str(e)}", "data": {}}

    def onClose(self):
        # print(f'{self.node_cfg["tool_package_snumber"]}工具退出')
        pass
