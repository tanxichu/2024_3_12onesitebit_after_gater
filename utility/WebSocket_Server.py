import asyncio
import websockets
import json


# 其实websocket的服务器很简单，他只有一个start的回调函数，用于处理处部的中转服务器。
# 即websocket的服务器只有一个功熥，就是做数据的中转，只有一核心函数。
# 与他相对应的客户端有收与发二个功能。 
class WebSocket_Server:
    def __init__(self):
        self.connections = {}  #这个是核心部件
        

    '''服务器启动先启动这个，它是实例后显示调用的。用server方法建立一个服务器，同时永久等待
    with是python的用法，能让系统不用显示处理关闭事项。和tensorflow一样。
    websockets.serve是固定写法，启动websocket服务器。self.handler 是指定为处理 WebSocket 连接的回调函数。
    当有客户端连接到由 websockets.serve 创建的 WebSocket 服务器时，由这个self.handler进行处理。
    '''
    #这个相当于注册后的记录数据库。是自己定义的。本处简单的value就一个数值，requested_url。
    # 也可以复杂点，将active状态，是否管理人员，等信息加上去。
    async def start(self):
        async with websockets.serve(self.handler, "localhost", 8001):
            await asyncio.Future()

    # 客户端传入这个：self.uri = "ws://localhost:8001/" + data["inputurl"] + "/" +  data["role"]" 
    #，这个的path会接收 "/" + data["inputurl"] + "/" +  data["role"]"  
    # websocket 就是 websocket.serve 传入的实例连接对象。即传入的websocket的客户端，是唯一的，websocket
    #由它来识别及控制各个客户端。
    async def handler(self, websocket_client_instanat, path):
        print(111112222233334444)
        #self.inputurl = "ws://localhost:8001/" + data["inputurl"] + "/" +  data["role"] #实例时传入
        requested_url_and_role = path.split("/")
        # 注意：因第个"/"号前是空的，所以列表的第一个元素是空字符串，所以我们从索引1开始取
        requested_url = requested_url_and_role[1]
        role = requested_url_and_role[2]

        # 以下是字典套字典的用法，不能用 A={{}}做法。
        # 检查"requested_url"键是否存在，不存在则创建一个空字典
        if requested_url not in self.connections.keys():
            self.connections[requested_url] = {}

        # 现在可以安全地为"requested_url"下的"role"键赋值
        self.connections[requested_url][role] = websocket_client_instanat
        print(self.connections)
        

        try:
            '''以下是监听的信息。connect过来时，是没有信息的，所有的信息全是通过客户端的send发过来的
            async for message in websocket: 这行代码使用的 in 关键字并不是表示“包含于”这种关系的操作符，
            此处的in并不是遍历的作用。它是 Python 异步迭代协议的一部分。在这个上下文中，in 关键字用于异步迭
            代一个异步可迭代对象。这意味着你的代码在等待（监听）并异步地从 WebSocket 连接中接收消息。
            可以理解 in 是一个websocket的一个特定的方法，用于监听这个实例，并将得到的信息给message'''

            '''还有一个特殊的地方, websocket 在客户端connect时，规定传入一个path，同时有一个是连接的实例。
            这个path及连接的实例是在connect产生后一直存在于实例的上下文的。所以即时后面 客户端 send 信息
            过来时，虽然没有运行过下面的 in 之前的代码，但是 in 前的参数能在in 方法中能找到。有点类似class
            的 __init__ 及 类函数的调用----函数内可以调用类成员变量。
            '''
            async for message in websocket_client_instanat: 
                print("server receiving message::::",message)
                message = json.loads(message)
                
                # 要求客户端的信息是 （"CAN_I_SEND"）   
                if "CAN_I_SEND" in message.values():    #由客户端发来，可以保证二个终端都上线时才发信息
                    print("我是服务器，我收到了client发过来的CAN_I_SEND")
                    can_send = await self.checkcansend(requested_url)  #等到三个全上线才下一步
                    await websocket_client_instanat.send(can_send)
                    print("server has sent'cansend'")
                #要求 message格式类似是{"to_fastapi":data}
                else:     #这个是平常的信息，要给通道的另一方发送的
                    print("我是服务器，我收到了client发过来的:::",message,"这是我的url：",requested_url)
                    for url, roles in self.connections.items():
                        if url == requested_url:
                            for role in roles:
                                #print("list(message.keys())[0]:::",list(message.keys())[0],"role:::",role)
                                if list(message.keys())[0] == "to_fastapi" and role == "fastapi":
                                    print("i will send to fastapi")
                                    await roles["fastapi"].send(json.dumps(list(message.values())[0]))
                                    print("i have sent to fastapi")
                                if list(message.keys())[0] == "to_listening" and role == "listening":
                                    print("i will send to listening")
                                    await roles["listening"].send(json.dumps(list(message.values())[0]))
                                    print("i have sent to listening")
                                if list(message.keys())[0] == "to_gather" and role == "gather":
                                    print("i will send to gather")
                                    await roles["gather"].send(json.dumps(list(message.values())[0]))
                                    print("i have sent to gather")
        except Exception as e:
            print("服务器处出现错误，错误产生的role是:",role)
            print(e)


    async def checkcansend(self, targeturl):
        while True :
            #统计同一个url即通道的客户端个数 
            print("targeturl:",targeturl)
            print("self.connections::::",self.connections)
            if targeturl in self.connections.keys():
                targeturl_instants = self.connections[targeturl]
                targeturl_instants_len = len(targeturl_instants)
                
            print("服务器现在有连接数量是：",targeturl_instants_len)
            if targeturl_instants_len >= 4:
                print("找到四个相同的 requested_url")
                return "cansend" # 找到了三个后就退出while

            await asyncio.sleep(2)  # 短暂等待后再次检查

async def main():
    server = WebSocket_Server()
    await server.start()
         
if __name__ == "__main__":
    asyncio.run(main())
    

