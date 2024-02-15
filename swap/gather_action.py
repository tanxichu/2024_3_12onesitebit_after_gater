from playwright.async_api import async_playwright    #注 async是异步式的，还有一个是sync是同步的
import asyncio
import sys
import os
import json
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utility.WebSocket_Client import WebSocket_Client



class gather_action:
    def __init__(self):
        self.pages_pool = []
        self.check_currency_valid = True
        self.playwright = None
        self.browser = None
        self.context = None
        self.detailed_url_get_data = None
        self.channelid = None
        self.networks = None
        self.webSocket_client_send_to_fastapi = None
        
    # await self.gather_instance.gather_start_up(self.networks,self.channelid,self.detailed_url_get_data)
    # 以下的参数是全局量参数的，对于整个uniswap来说，不管发出多个采集命令，他都只是通过websocket通道接收吧了，
    # 与以下的全局量参数设定没有关系
    async def gather_start_up(self,networks,channelid,detailed_url_get_data):
        self.detailed_url_get_data = detailed_url_get_data
        self.channelid = channelid
        self.networks = networks
        self.playwright = await async_playwright().start()    #启动了一个异步的playwright
        self.browser = await self.playwright.chromium.launch(headless=False)
        #new_context()即打开一个新的浏览器实例上下文
        self.context = await self.browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        # 设置请求拦截器来禁用图片加载，lambda是匿名函数
        await self.context.route("**/*", lambda route: asyncio.create_task(self.handle_route(route)))
        await self.create_page(batch_amount=1)    #打开二批浏览器
        #可以不用await，毕竟，它是独立的，在监听到信息后再建立一个采集方法，并传回相关的内容就可以了
        #以下二个是独立的协程，即互不影响即可。
        self.webSocket_client_send_result_to_fastapi = WebSocket_Client({"inputurl":self.channelid,"role":"send_result_to_fastapi"})
        await self.webSocket_client_send_result_to_fastapi.connect()
        asyncio.create_task(self.listening())
        asyncio.create_task(self.get_data())

    
    # 设置请求拦截器来禁用图片加载，lambda是匿名函数
    async def handle_route(self, route):
        try:
            if route.request.resource_type == "image":
                await route.abort()
            else:
                await route.continue_()
        except Exception as e:
            print(f"Error handling route: {e}")




    # 生成一样的实例：[[{mainnet:page，others:page，...}, {mainnet:page，others:page，...}]]
    async def create_page(self, batch_amount):
        for _ in range(batch_amount):
            opening_pages = []    #注，这个要放在此处，不能放在全局量处，因他每次都是全新的列表
            for network_dict in self.networks:
                #network_dict:::  {'Ethereum':"https://app.uniswap.org/swap?chain=mainnet"}
                network_name = list(network_dict.keys())[0]
                network_url = list(network_dict.values())[0]
                page = await self.context.new_page()   #注意：这个page是一个实例
                await page.goto(network_url)
                opening_pages.append({"network_name":network_name, "network_url":network_url,"page":page})
            self.pages_pool.append(opening_pages) 
            

    #await self.gather_instance.listening_start_up(channelid, self.detailed_url_get_data) 
    async def listening(self):
        self.webSocket_client_listening = WebSocket_Client({"inputurl":self.channelid,"role":"listening"})
        await self.webSocket_client_listening.connect()
        while True:
            print("gather_action: i am waiting data")
            # json.dumps({"to_listening": {"request_ID":"request_ID" ,"data":{"coina":"WBTC","coinb":"WETH","amount":"1"}}})
            original_data_from_websocket = await self.webSocket_client_listening.receive_message()
            #json.loads() 将 JSON 字符串转换成 Python 字典
            original_data_from_websocket = json.loads(original_data_from_websocket)
            print("listening got data::::", original_data_from_websocket)
            await self.webSocket_client_listening.send_message(json.dumps({"to_gather" : original_data_from_websocket}))
            print("I have sent to to_gather")

    
    '''
    get_data 只接收listening过来的必要信息，即 {"request_ID":"request_ID" ,"data":{"coina":"WBTC","coinb":"WETH","amount":"1"}}
    具体如何采集，用什么来pages来采集的，由它自己调用上下文的有关参数即可
    所以他的第一步是要建立一个websocket通道，由它来触发有关的代码
    '''
    async def get_data(self):
        #以下代码只在gather_start_up调用了一次，即只会对每个uniswap或其它采集软件只产生一次。
        self.webSocket_client_gather = WebSocket_Client({"inputurl":self.channelid,"role":"gather"})
        await self.webSocket_client_gather.connect()

        #以下是每次采集命令都要运行的，所以下面定义的变量不能用self
        while True:
            data = await self.webSocket_client_gather.receive_message()
            data =  json.loads(data)
            print("gather received:",data)
            request_ID = data["request_ID"]   #这个 request_ID每次请求都不同，所以不能用全局量
            data_to_detailed_url_get = data["data"]
            opening_pages = None
            opening_page_and_gathered_results = []  #此处不能用self，否则会导致新请求也旧请求重复
            #默认会用start_up产生的二个中的一个，直到没有时再临时加一个pages，这个临时加的到时要删除
            if len(self.pages_pool)>0 :
                opening_pages = self.pages_pool.pop()
            else:
                #初始化时会产生二个，现在是后期的执行期间，
                await self.create_page(1)  #任何async方法都一定要await，否则报错
                opening_pages = self.pages_pool.pop()
        
            #opening_pages.append({"network_name":network_name, "network_url":network_url,"page":page})
            for opening_page in opening_pages:
                #建立协程并发办法，asyncio.create_task后只能跟一个动作------只有这个办法。
                # 用它后后部的下面的方法全是并发的。
                #以下会以并发方式用各page进行采集，
     

                # def detailed_url_get_data(self, data_from_websocket,opening_page)
                # opening_pages.append({"network_name":network_name, "network_url":network_url,"page":page})
                # 注意，此处不能只传入opening_page["page"],因虽然后者只用了opening_page["page"]的属性，但也要整个传回，
                # 因为下面的asyncio.gather 要对结果进行for 并用当时的page进行相当的操作
                # 要求传回来的结果是 {"data":result, "opening_page":opening_page }
                opening_page_and_gathered_result = asyncio.create_task(self.detailed_url_get_data(data_to_detailed_url_get,opening_page))

                #将各个任务加入任务列表中。这样做的目的是等pages采集回来后，再统一返回给fastapi
                opening_page_and_gathered_results.append(opening_page_and_gathered_result)
            #因要并级运算，但await asyncio.gather(*tasks) 有一个await，会block，要对它加一个协程
            asyncio.create_task(self.send_to_fastapi(request_ID,opening_page_and_gathered_results))
            
    async def send_to_fastapi(self,request_ID,opening_page_and_gathered_results): 
        #*是解构，asyncio.gather会按原来results的加入顺序，以list方式返回给results，
        # asyncio.gather，它多了一个功能，就是等全部task运行完毕，有结果时才返回
        # 对于detailed_url_get_data来说，传入的数据是  (data_to_detailed_url_get,opening_page["page"])
        # 它返回的结果要求是：{"opening_page":opening_page，"result": result  } 即将整个原始传入的opening_page返回

        opening_page_and_gathered_results = await asyncio.gather(*opening_page_and_gathered_results) 
        results = []
        print("original_results:::",opening_page_and_gathered_results) 

        # 得到是 {"data":result, "opening_page":opening_page }
        # 上面的opening_page：：opening_pages.append({"network_name":network_name, "network_url":network_url,"page":page})
        for opening_page_and_gathered_result in opening_page_and_gathered_results:
            opening_page = opening_page_and_gathered_result["opening_page"]
            result={}
            result[opening_page["network_name"]] = opening_page_and_gathered_result["data"]
            results.append(result)
        print("获取各个ulr后得到的数据:",results)
        to_fastapi_result = {}
        to_fastapi_result[request_ID] = results
        await self.webSocket_client_send_result_to_fastapi.send_message(json.dumps({"to_fastapi":to_fastapi_result}))

        only_once= True
        for opening_page_and_gathered_result in opening_page_and_gathered_results:
             
            opening_page = opening_page_and_gathered_result["opening_page"]
            url = opening_page["network_url"]
            page = opening_page["page"]

            if only_once:    #只第一次要等，其它不用等
                await asyncio.sleep(10)     #此处要加时间，否则报错，会提示没处理完毕。原因不明
            only_once = False
            try:
                await page.goto(url)
            except Exception as e:
                # 处理异常，可以记录日志或采取其他措施
                print(e)



        

        

























































    async def process_page(self, page_dict,data_from_websocket):
        try: 
            print(9999999)   
            network_name = page_dict[0]
            network_url = page_dict[1]
            page = page_dict[2]
         
            element= None
            if (network_name == "Ethereum" or  "arbitrum" or "optimism" or "base"):
                print("i am hereeee!!!!!!!!!!!!")
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")
            if (network_name == "polygon" ):
                #MATIC
                element = await page.query_selector("xpath=//*[contains(text(), 'MATIC')]")
            if (network_name == "bnb" ):
                #BNB
                element = await page.query_selector("xpath=//*[contains(text(), 'BNB')]")
            if (network_name == "avalanche" ):
                #AVAX
                element = await page.query_selector("xpath=//*[contains(text(), 'AVAX')]")
            if (network_name == "celo" ):
                #celo   
                element = await page.query_selector("xpath=//*[contains(text(), 'celo')]")
            await element.click()

            print(network_name,55555555555)

            # 等待输入字段可见
            await page.wait_for_selector('input[placeholder="Search name or paste address"]')
            print("Search name or paste address")

            # 在输入字段中输入文本
            await page.type('input[placeholder="Search name or paste address"]', data_from_websocket["coina"])
            print(network_name, '66666')

            
            await self.enter_action(page)
            
            if self.check_currency_valid == True:
                select_token_button = await page.wait_for_selector('text=Select token')
                await select_token_button.click()
                print(network_name, '7777')

                await page.wait_for_selector('input[placeholder="Search name or paste address"]', state="visible")
                await page.type('input[placeholder="Search name or paste address"]', data_from_websocket["coinb"])
                print(network_name, '8888')

    
                await self.enter_action(page)

                await page.wait_for_selector('.token-amount-input', state="visible")
                await page.type('.token-amount-input', data_from_websocket["amount"])
                print(network_name, '9999')

                checkprice = True
                while checkprice:
                    price = await page.evaluate('(selector) => document.querySelectorAll(selector)[1].value', '.token-amount-input')
                    if price and price.strip():  # 检查price是否非空且非None
                        checkprice = False
                    await asyncio.sleep(0.5)

                max_slippage = await self.get_text(page,'Max. slippage')

                Fee = await self.get_text(page,'Fee')

                Network_cost = await self.get_text(page,'Network cost')

                Order_routing = await self.get_text(page,'Order routing')

                result = [{"price":price},{"max_slippage":max_slippage},{"Fee":Fee}, {"Network_cost":Network_cost},{"Order_routing":Order_routing} ]

                network_url = page_dict[1]
                page = page_dict[2]
                return(network_name,result,network_url,page)
                


            else: 
                print(network_name, "::::::::Can not find this Currency")

        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            print(f"An error occurred: {e}")
                

    async def get_text(self, page, search_text):
        # 构建有效的 XPath 表达式
        xpath_expression = f"//div[contains(text(), '{search_text}')]/following-sibling::div"
        await page.wait_for_selector(f"xpath={xpath_expression}", state="visible")
        while True:
            # 获取文本并处理
            text = await page.text_content(f"xpath={xpath_expression}")
            if text and text.strip():  # 检查text是否非空且非None
                text = text.strip()
                if '\n' in text:
                    text = text.split('\n')[0]
                return text
            else:
                await asyncio.sleep(0.1)  # 等待一段时间后再尝试

    async def enter_action(self, page):
        count = 0
        need_click = True
        while count <20 :
            if need_click:
                await page.evaluate('''() => {
                    const inputElement = document.querySelector('input[placeholder="Search name or paste address"]');
                    if (inputElement) {
                        const event = new KeyboardEvent("keydown", {
                            key: "Enter",
                            code: "Enter",
                            bubbles: true,
                            cancelable: true
                        });
                        inputElement.dispatchEvent(event);
                    } else {
                        console.error("Input element not found.");
                    }
                }''');
            
            # 检查页面中是否存在特定元素,找不到就退出
            if not await page.locator('input[placeholder="Search name or paste address"]').count():
                return
            await asyncio.sleep(0.1)   

            
            count = count + 1
        self.check_currency_valid = False

    async def reduce_page(self, page_dicts):
        print("reduce_page:::::::::",page_dicts)
        await asyncio.sleep(10)  # 等待30秒
        '''async with self.lock:  # 获取锁
            print(111111111111122222222222)
            if len(self.pages_pool) > 1:
                for page_info in self.pages_pool:
                    if page_info[2] == target_page:  
                        self.pages_pool.remove(page_info)
                        print("我要关其中一个")'''