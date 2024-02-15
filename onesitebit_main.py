

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
from swap.uniswap import uniswap




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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)