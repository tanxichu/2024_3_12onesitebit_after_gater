import asyncio
import websockets
import time
import json

'''
本websocket的特色是，在实例时传一个对象，其中，这个对象有一个url，另一个是role，后者给connect时
可以调用进行注册。同时connect还要检测是不是三个客户端全在线时才算是正常连接成功。'''
class WebSocket_Client:

    def __init__(self, data):
        # 各实例格式：WebSocket_Client({"inputurl":"testchannelid","role":"fastapi"})
        self.inputurl = "ws://localhost:8001/" + data["inputurl"] + "/" +  data["role"] #实例时传入
        self.websocket = None
        self.connected = False 


    async def connect(self):
        start_time = time.time()
        #当他连接后会修改self.connected = True，在此再次检测，同时for不超60秒
        while not self.connected and time.time() - start_time < 60:  
            try:
                self.websocket = await websockets.connect(self.uri)
                
                
            except Exception as e:
                #返回while
                await asyncio.sleep(1)  # 等待1秒再重试
        print("connect方法运行完了")
                
                


    async def connect(self):
        print("i will connect")
        start_time = time.time()
        #当他连接后会修改self.connected = True，在此再次检测，同时for不超60秒
        while not self.connected and time.time() - start_time < 60:  
            try:
                # 此时，server处只是运行到 async for message in websocket_client_instanat 前的数据 
                # async for message in websocket_client_instanat: 这条不运行，因他并没有in到数据
                self.websocket = await websockets.connect(self.inputurl)
                self.connected = True
                print("WebSocket 连接成功")
                break

            except Exception as e:
                # await websockets.connect(self.inputurl)  若服务器不在线时，这里会报错
                # 这里通过故意捕捉上面的报错，让代码返回while，然后达到断线自动重新连接功能。
                await asyncio.sleep(1)  # 等待1秒再重试
        print("connect方法运行完了，注意,若上面没出现WebSocket 连接成功，意味它是60秒超时退出，没成功连接")

    async def send_message(self, message):
        # self,指的就是这个class的实例。
        # connected 这个比较特殊，是websockets实例后自带的属性，表示连接与否的一个状态。不用声明
        if not self.connected:            
            print("WebSocket 未连接")
            await self.connect()

        else : 
            try:
                print("websocket_client1111_receive_message:",message)
                #发前检测对方是否在线时再发,统一用json.dumps处理，然后，Server统一用loads处理
                # 服务器的 async for message in websocket_client_instanat 前的代码不执行
                # 但服务器的async for message in websocket_client_instanat 及其后面的代码会执行
                print("self.websocket77777::::::::",self.websocket)
                await self.websocket.send(json.dumps({"data":"CAN_I_SEND"}))
                print("self.websocket88888::::::::",self.websocket)
                respond = await self.websocket.recv()
                print("clinet,现在的respond状态是:",respond)
                if respond == "cansend":
                    await self.websocket.send(message)

            #以下是防向scrapy发送时，刚开始是通的，因此 connected = ture，但后来断开了，connected = ture还是不变
            #但后来不知为何断了，现在再次连接多一次。此处是利用了 await self.websocket.send("CAN_I_SEND")
            # 若服务器断开了，会报错的特性，人为的实现重新连接的功能。send连接不上会有TCP握手错误
            # 总结：断线自动连接的，全部功能实现是在client实现的，服务器只做中心管理及转发功能。
            except websockets.ConnectionClosed as e:
                print(f"连接断开，send_message: {e}")
                self.connected = False
                await self.connect()
                print("已连接上了")
                print("已接上，现在要发的数据是：", message)
                #再调本地的方法，相当于一个for
                if self.connected:        # 一定要加这个，否则会出错，原因不明
                    message = await self.send_message(message)
                    print("断开后现在重新发送的消息:"+message)

    async def receive_message(self):
        if not self.connected :
            print("WebSocket 未连接")
            await self.connect()

        else:
            try:
                #这里也是利用了rec的报错实现自动重连功能。recv的报错与send的报错不同，websocket在
                # 触发recv时，他没有握手功能，它只是被动等服务器发响应。这时有二个情况，若服务器是正常退出的
                #包括 CTRL+C,包括其它退出功能，服务器在关闭前都会向全部客户端发一个断开连接的通知。
                # 这时recv会收到这个通知后触发异常。还有一种情况，如突然断电，硬关机，人为硬关程序，
                #这时，recv不会报错。所以为了能一定能实现报错，最后加上ping pong功能。
                print("self.websocket99999::::::::",self.websocket)
                message = await self.websocket.recv()
                print("接收到消息:", message)
                return message
            except websockets.ConnectionClosed as e:
                print(f"连接断开，正在尝试重新连接... 错误详情: {e}")
                self.connected = False
                await self.connect()
                if self.connected:        # 一定要加这个，否则会出错，原因不明
                    print("我是断开后接收数据的部份")
                    message = await self.receive_message()   #重新接收
                    print("断开后现在重新接收到消息:"+message)
                    return message
                
    async def close(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None  # 将websocket对象设置为None，避免重复关闭
                
async def main():
    webSocket_client_A = WebSocket_Client({"inputurl":"testchannelid","role":"fastapi"})
    await webSocket_client_A.connect()
    # 直接使用你已经定义好的 `connected` 属性来检查连接状态
    if webSocket_client_A.connected:
        print("WebSocket 已成功连接")
    else:
        print("WebSocket 连接失败")
    # {“to_fastapi":data}
    await webSocket_client_A.send_message({"to_listening":"fastappi_to_message"})
    data_from_websocket = await webSocket_client_A.receive_message()
    print(data_from_websocket)
    await webSocket_client_A.close()  # 关闭WebSocket连接


                
if __name__ == "__main__":
    asyncio.run(main())
    
