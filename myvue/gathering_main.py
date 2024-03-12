# fastapi 提供路由等功能，而Uvicorn 提供接收 http请求,二者一起才能提供完整的功能

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import sys
import os
import uuid
from swap.uniswap.uniswap import uniswap
import multiprocessing
import asyncio



from utility.WebSocket_Client import WebSocket_Client
from utility.WebSocket_Server import WebSocket_Server




process_pool = {"swap":[], "futurewebsite":[]}


#这个是fastapi特定的，一打开就运行了
@asynccontextmanager
async def app_startup(app):
    #python 在方法内使用及修改全局常量的，一定要加global process_pool ，否则当是局部量----特殊
    global process_pool   
    #await initialize_processes()
    yield  # 必须在这里加上 yield，表示生命周期的分割点


app = FastAPI(lifespan=app_startup)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #allow_origins=["https://onesitebit.com"] 可限制特定网站才可转发
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

swap_processes=[]
furture_processes=[]
swaps =[uniswap,]    #将import 进来的class组成一个list，可以遍历实例化
futrues =[]

'''async def initialize_processes():
    for swap_target_class in swaps:
        swap_target_instance = swap_target_class()
        channelid = str(uuid.uuid4())
        
        await swap_target_instance.start_up(channelid)
        webSocket_client_instant = webSocket_client(channelid)
        await webSocket_client_instant.connect()
        swap_processes.append({"swap_target_instance": swap_target_instance, "webSocket_client_instant": webSocket_client_instant})

    for futrue_class in futrues:
        pass
'''



async def uniswap_main():
    uniswap_instant = uniswap("uniswap_websocket_url")
    
    '''此处的start_up()是个异步的方法，因它内部有一些await，一定要await，
    否则要用asyncio.run  变成顺序执行'''
  
    #要注意，本项目中，每个要采集的网站是一个固定的websocket_url,这个URL是事先定好的
    #本项目中，因gather_action 是公用的，所以这个id要在此作为变量传给gather_action
    #相关的 listening 及 gather 对应的websocket
    await uniswap_instant.start_up()

def uniswap_wrap_main():
    asyncio.run(uniswap_main())
    
async def websocket_sever():
    server = WebSocket_Server()
    await server.start()

def wrap_websocket_sever():
    asyncio.run(websocket_sever())

fastapi_websockets = {"swap":{"uniswap":None,},"future":{}}
async def fastapi_websocket_send_receive_data():
    #要注意，本项目中，每个要采集的网站是一个固定的websocket_url,这个URL是事先定好的
    webSocket_client_uniswap = WebSocket_Client({"inputurl":"uniswap_websocket_url","role":"fastapi"})
    print("before connect")
    await webSocket_client_uniswap.connect()
    print("aftercorrect")
    fastapi_websockets["swap"]["uniswap"] = webSocket_client_uniswap

def wrap_fastapi_websocket_send_receive_data():
    asyncio.run(fastapi_websocket_send_receive_data())
'''
process_data 可以不用BaseModel来接收数据，但用了会更好。因：
自动数据验证：FastAPI 会自动验证传入的数据是否符合 BaseModel 的结构，包括数据类型和是否存在必填字段。
自动错误处理：如果数据不符合模型，FastAPI 会自动返回一个具有描述性错误的响应。
'''
class swapdata(BaseModel):
    coina: str = ''
    coinb: str = ''
    amount: str = ''

#以下默认已是并级运算的
@app.post("/process_swap") 
async def process_data(data: swapdata):
    print(data)
    try:
        # 同时websocket 不能传字典，只能传json或str，本处再变json,
        json_data = json.dumps(dict(data))
        results = []
        print(1111,fastapi_websockets["swap"])
        for websocket_name, fastapi_swap_websocket in fastapi_websockets["swap"]:
            print(222)
            await fastapi_swap_websocket.send_message(json_data)
            data = await fastapi_swap_websocket.receive_message()
            results[websocket_name] = data
        return results
  
    except Exception as e:
        return f"An error occurred: {e}"
    


if __name__ == "__main__":
    # 以下是模仿fastapi中，如何调用unswap代码
    #注意，调入的分进程是个函数，不能加(),同时不能是异步的，若是异步，一定要用asyncio.run变回同步
    uniswap = multiprocessing.Process(target=uniswap_wrap_main)
    uniswap.start()  # 启动子进程

    websocket_sever = multiprocessing.Process(target=wrap_websocket_sever)
    websocket_sever.start()
    
    wrap_fastapi_websocket_send_receive_data()
 
    uvicorn.run(app, host="127.0.0.1", port=8000)
    

