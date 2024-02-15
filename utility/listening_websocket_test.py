from WebSocket_Client import WebSocket_Client
import asyncio
import json

async def ab():
    webSocket_client_A = WebSocket_Client({"inputurl":"testchannelid","role":"listening"})
    await webSocket_client_A.connect()
    # 直接使用你已经定义好的 `connected` 属性来检查连接状态
    if webSocket_client_A.connected:
        print("WebSocket 已成功连接")
    else:
        print("WebSocket 连接失败")
    # ({"to_listening":"fastappi_to_message"})
    while True:
        data = await webSocket_client_A.receive_message()
        print("listening received:",data)
        await webSocket_client_A.send_message(json.dumps({"to_gather":"listening_resend_fastappi_data_to_gather"}))

asyncio.run(ab())
