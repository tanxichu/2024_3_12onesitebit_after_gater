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
from uniswap import uniswap

# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utility.webSocket_client import webSocket_client


import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
import sys
import os
import uuid
from uniswap import uniswap

# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utility.webSocket_client import webSocket_client


process_pool = {"swap":[], "futurewebsite":[]}


#这个是fastapi特定的，一打开就运行了
@asynccontextmanager
async def app_startup(app):
    #python 在方法内使用及修改全局常量的，一定要加global process_pool ，否则当是局部量----特殊
    global process_pool   
    await initialize_processes()
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

async def initialize_processes():
    for swap_target_class in swaps:
        swap_target_instance = swap_target_class()
        channelid = str(uuid.uuid4())
        
        await swap_target_instance.start_up(channelid)
        webSocket_client_instant = webSocket_client(channelid)
        await webSocket_client_instant.connect()
        swap_processes.append({"swap_target_instance": swap_target_instance, "webSocket_client_instant": webSocket_client_instant})

    for futrue_class in futrues:
        pass

class swapdata(BaseModel):
    type: str= ''
    coina: str = ''
    coinb: str = ''
    amount: str = ''


@app.post("/process_swap")
async def process_data(data: swapdata):
    print(data)
    try:
        #注意：收到的是ScrapyData(BaseModel)型数据，所以一定要dict变成字典,
        # 同时websocket 不能传字典，只能传json或str，本处再变json,
        json_data = json.dumps(dict(data))  
        if data.type == "swap":    #直接取data读即可
            for swap_process in swap_processes:
                await swap_process["webSocket_client_instant"].send_message(json_data)
                data = await swap_process["webSocket_client_instant"].receive_message()
                return data
        if data.type == "future":
            pass

                
    except Exception as e:
        error_message = f"An error occurred: {e}"
        return {"message": error_message}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)