#只能用这个方法：：：：   uvicorn app:app --host 0.0.0.0 --port 8000
# netstat -ano | findstr :8001
#  taskkill /F /PID 32804     ：：：：：手工关了server。现在只能用这个办法，原因不明
# taskkill /IM firefox.exe /F          ::::::::::: 手工关了firefox


'''Set CORS，fastapi也要跨域，vue要与爬虫软件交互只能通过http，本处由fastapi提供http服务，同时提供多线程管理。scrapy也有多线程，本处统一用fastapi即可
SCRAPY不能将结果主动返回给fastapi，可以用websocket进行通话。也可以用redis进行通讯，但是rediss不能异步，只能用轮询通道。所以本方案用websocket。
websocket要建立一个服务器，先启动。fastapi在启动时就打开一系列的网站，进入到相关的要采集的页面，建立好各自的通道。当fastapi收到请求时通过通道向
scrapy发信息。后者收到信息后即时采集，将采集后的数据通过websocket返回。全部的进程通过proccess_POOL 进行管理。在项目中，可以加上，若线程不够，或只余下5%线程时，会自动增加新的临时进程。
但新的旧时进程发现线程又多了，如不小于10%时，就自动关闭线程。同时还要增加一个功能是：若一分钟内相同的请求的，直接从redis中读取材料返回即可。这个要求增加一个redis功能。在scrapy处做。然后fastapi读取。
还有一个新的功能是，在scrapy处做处理，当采集到的信息不正确时，会有相应的log，或发信息到手机上。
'''


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

'''
因下面的，cwd=os.path.dirname(os.path.abspath(__file__)),会修改
这行代码的作用是设置启动子进程时的当前工作目录。这里的 __file__ 是一个特殊变量，它包含了当前执行文件的完整路径。
os.path.abspath(__file__) 返回当前执行文件的绝对路径。
os.path.dirname() 获取该路径的目录部分，即去掉文件名后的路径。
这条代码相当于在当前目录下建立一个虚拟的环境用于子进程中。所以他会影响
from WebSocket_Client import WebSocketClient，会提示找不到模块。为解决这个问题，
获取当前工作目录并添加到sys.path：：sys.path.append(os.getcwd())
同时还要放在import之前
'''
sys.path.append(os.getcwd())
from WebSocket_Client import WebSocketClient
from websocketserver import WebSocketServer



app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #allow_origins=["https://onesitebit.com"] 可限制特定网站才可转发
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapyProcess:
    def __init__(self,channelid):
        self.process = None
        self.channelid = channelid #实例时传入一个websocket通道名

    async def create_and_start_process(self,websitename):
        #定义scrapy的命令
        scrapy_command = [
            'scrapy', 'crawl', websitename,
            '-a', 'forwardurl=' + self.channelid,  #给scrapy传入通道名
        ]

        #用asyncio建立子线程，并执行相关的scrapy命令，并配置这个子线程是在一个当前目录下运行的
        self.process = await asyncio.create_subprocess_exec(   # 打开默认首页
            *scrapy_command,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        
    #调用客户端的class类建立一个实例，连接，并返回这个实例。
    async def startwebsocket(self):
        newSocketClient = WebSocketClient(self.channelid)      
        await newSocketClient.connect()   # 这个WebSocketClient就是websocket对象 ,已连接好了
        return newSocketClient
    
process_pool = {"swap":[], "futurewebsite":[]}
swapsite ={
    #"swap":['uniswap','sushiswap',"pacakeswap","curvefinance","balance"],  
            "swap":['uniswap'],  
           "future":[] 
           }

async def initialize_processes():
    swapwebsite = swapsite["swap"] 
    futurewebsite = swapsite["future"]
    for swapwebsitename in swapwebsite:
        for i in range(5):
            print(1234567890111111111111111111111)
            channelid = str(uuid.uuid4())   #产生一个唯一值，以此来建立websocket
            process = ScrapyProcess(channelid)          
            await process.create_and_start_process(swapwebsitename)  # 打开一个scrapy爬虫  
            # 打开一个webscocket专用通道对应这个进程，注，它与上面的是二个不同的动作来的
            websocketclient = await process.startwebsocket()   
            process_pool["swap"].append( {channelid:websocketclient} )
    
    for futurewebsitename in futurewebsite:
        for i in range(2):
            channelid = str(uuid.uuid4())   #产生一个唯一值，以此来建立websocket
            process = ScrapyProcess(channelid)          
            await process.create_and_start_process(futurewebsitename)  # 打开一个scrapy爬虫  
            # 打开一个webscocket专用通道对应这个进程，注，它与上面的是二个不同的动作来的
            websocketclient = await process.startwebsocket()   
            process_pool["swap"].append( {channelid:futurewebsitename} )
    

#这个是fastapi特定的，一打开就运行了
@app.on_event("startup")
async def startup_event():
    #python 在方法内使用及修改全局常量的，一定要加global process_pool ，否则当是局部量----特殊
    global process_pool   
    await initialize_processes()

'''
process_data 可以不用BaseModel来接收数据，但用了会更好。因：
自动数据验证：FastAPI 会自动验证传入的数据是否符合 BaseModel 的结构，包括数据类型和是否存在必填字段。
自动错误处理：如果数据不符合模型，FastAPI 会自动返回一个具有描述性错误的响应。
'''
class swapdata(BaseModel):
    coina: str = ''
    coinb: str = ''
    amount: str = ''


@app.post("/process-swap")
async def process_data(data: swapdata):
    try:
        json_data = json.dumps(dict(data))  #注意：收到的是ScrapyData(BaseModel)型数据，所以一定要dict变成字典
        processwebsocket = process_pool["swap"].pop()
        #字典中一次性将 key与 value二个数值一次取出来
        channelid, websocketclient = processwebsocket.popitem() 
        await websocketclient.send_message(json_data)
        data = await websocketclient.receive_message()
        process_pool["swap"].append({channelid:websocketclient})
        return data

                
    except Exception as e:
        error_message = f"An error occurred: {e}"
        return {"message": error_message}




class futruedata(BaseModel):
    type:str=''


@app.post("/process-futrue")
async def process_data(data: futruedata):
    try:
        json_data = json.dumps(dict(data))  #注意：收到的是ScrapyData(BaseModel)型数据，所以一定要dict变成字典
        processwebsocket = process_pool["futrue"].pop()
        #字典中一次性将 key与 value二个数值一次取出来
        channelid, websocketclient = processwebsocket.popitem() 
        await websocketclient.send_message(json_data)
        data = await websocketclient.receive_message()
        process_pool["futrue"].append({channelid:websocketclient})
        return data
                
    except Exception as e:
        error_message = f"An error occurred: {e}"
        return {"message": error_message}

# WebSocket服务器启动函数
def start_websocket_server():
    server = WebSocketServer()
    asyncio.run(server.start("localhost", 8001))

if __name__ == "__main__":
    # 创建并启动WebSocket服务器线程，线程要执行一个方法，所以要先定义方法
    websocket_thread = threading.Thread(target=start_websocket_server)
    websocket_thread.start()

    # 启动FastAPI应用，这个是主线程
    uvicorn.run(app, host="0.0.0.0", port=8000)