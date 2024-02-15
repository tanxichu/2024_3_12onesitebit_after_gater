
from WebSocket_Client import WebSocket_Client
import asyncio
import json

async def main():
    webSocket_client_A = WebSocket_Client({"inputurl":"testchannelid","role":"fastapi"})
    await webSocket_client_A.connect()
    # 直接使用你已经定义好的 `connected` 属性来检查连接状态
    if webSocket_client_A.connected:
        print("WebSocket 已成功连接")
    else:
        print("WebSocket 连接失败")
    # {“to_fastapi":data}
    await webSocket_client_A.send_message(json.dumps({"to_listening":"fastappi_to_message"}))
    data_from_websocket = await webSocket_client_A.receive_message()
    print(data_from_websocket)
    await webSocket_client_A.close()  # 关闭WebSocket连接


                
if __name__ == "__main__":
    asyncio.run(main())