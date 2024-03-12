# fastapi 提供路由等功能，而Uvicorn 提供接收 http请求,二者一起才能提供完整的功能

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager
from swap.uniswap.uniswap import uniswap   #用main方法对应的路径
from swap.sushi.sushi import sushi
from swap.curve.curve import curve
from swap.pancake.pancake  import pancake        
import asyncio


#整体设计思路：各个采集class实例时先实例一个浏览器。在收到vue请求后建立实时的websocket，再返回，会在采集完后加上close功能
#这个是fastapi特定的，一打开就运行了
swap_instances = []
@asynccontextmanager
async def app_startup(app):
    global swap_instances    #python函数内修改全局量的参数，用global显式声明对方是全局量
    #swaps_classes =[uniswap,curve,sushi,pancake ]       
    swaps_classes =[uniswap,pancake,curve,sushi]   # pancake,uniswap,sushi,,sushi
    for swap in swaps_classes:
        swap_instance = swap()
        await swap_instance.start_up()
        swap_instances.append(swap_instance)
    '''
    yield是python的用法, 常和StreamingResponse 一起使用，达到类似return一样的返回。但它和return又不同
    它能多次分批返回。对应的vue要建立 EventSource 事件机制。这个机制与websocket类同，但websocket复杂，
    但可以双向，yied只能是单向，但简单。这个用于分批发送材料给vue，适合于本项目。属于二期项目

    但本处中的yield 没有返回的用法，它是与FASTAPI中，与@asynccontextmanager配合使用时用于让服务器
    '''
    yield  # 必须在这里加上 yield，表示生命周期的分割点


app = FastAPI(lifespan=app_startup)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #allow_origins=["https://onesitebit.com"] 可限制特定网站才可转发
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
  
class swapdata(BaseModel):
    coina: str = ''
    coinb: str = ''
    amount: str = ''

# 默认已是并行运算
@app.post("/process_swap")
async def process_data(data: swapdata):
    try:
        data = dict(data)  #收到的是ScrapyData(BaseModel)型数据，要dict变成字典
        results =[]
        for swap_instance in swap_instances:
            result = asyncio.create_task(run_swap(swap_instance,data))
            results.append(result)
        results = await asyncio.gather(*results)    
        
        print("主线程收到:",results)
        return results
                
    except Exception as e:
        error_message = f"主程序fastapi发生错误: {e}"
        print(error_message)
        return {"message": error_message}
        
async def run_swap(swap_instance, data):
    result  = await swap_instance.start_gather(data)
    return result


    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    

