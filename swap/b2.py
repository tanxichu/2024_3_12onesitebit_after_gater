import threading
import time
import asyncio

class loop_thread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        while True:
            time.sleep(1000000000)

class ControllerThread(threading.Thread):
    def __init__(self):
        super().__init__()      
        self.worker_thread = loop_thread()  # 在构造函数中实例化 loop_thread
        self.worker_thread.start()  # 启动 worker_thread
        
   
    def aa(self):
        asyncio.create_task(self.bb())

    async def bb(self):
        await asyncio.sleep(1)
        print(1)
        await asyncio.sleep(1)
        print(2)
        await asyncio.sleep(1)
        print(3)
       
if __name__ == "__main__":
    controller_thread = ControllerThread()  # 直接创建 ControllerThread 实例
    controller_thread.aa()
    time.sleep(1)
    controller_thread.aa()
    time.sleep(1)
    controller_thread.aa()
    time.sleep(1)
    controller_thread.aa()
