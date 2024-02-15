from fastapi import FastAPI
from contextlib import asynccontextmanager
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os
from pydantic import BaseModel
import uuid
import asyncio
import asyncio
import uvicorn
import os
import sys
import threading
from uniswap_可并行运算 import uniswap

# 假设的初始化和清理函数
async def create_all():
    print("执行数据库初始化")

async def drop_all():
    print("执行数据库清理")

# 定义lifespan事件处理函数
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("启动前执行")
    await create_all()  # 调用初始化函数
    yield  # FastAPI应用运行期间保持活动状态
    print("关闭后执行")
    await drop_all()  # 调用清理函数

# 创建FastAPI应用实例，并指定lifespan参数
app = FastAPI(lifespan=lifespan)

# 定义一个示例路由
@app.get("/")
async def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)