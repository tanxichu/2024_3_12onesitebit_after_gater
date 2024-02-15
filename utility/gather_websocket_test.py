from WebSocket_Client import WebSocket_Client
import asyncio
import json

async def ab():
    webSocket_client_A = WebSocket_Client({"inputurl":"testchannelid","role":"gather"})
    await webSocket_client_A.connect()

    
    while True:
        data = await webSocket_client_A.receive_message()
        print("gather received:",data)
        await webSocket_client_A.send_message(json.dumps({"to_fastapi":"result_from_gahter"}))

asyncio.run(ab())



