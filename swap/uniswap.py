# netstat -aon | findstr :8001
# taskkill /F /PID 7208
 
import asyncio
import sys
import os
import json
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utility.WebSocket_Client import WebSocket_Client
from utility.WebSocket_Server import WebSocket_Server
from gather_action import gather_action 
import multiprocessing


class uniswap():
    def __init__(self,channelid):
        self.networks = [{'Ethereum':"https://app.uniswap.org/swap?chain=mainnet"},
                         #{"optimism":"https://app.uniswap.org/swap?chain=optimism"},
                         #{"polygon":"https://app.uniswap.org/swap?chain=polygon"},
                         #{"base":"https://app.uniswap.org/swap?chain=base"},
                         #{"bnb":"https://app.uniswap.org/swap?chain=bnb"}, 
                         #{"arbitrum": "https://app.uniswap.org/swap?chain=arbitrum"},
                         #{"avalanche":"https://app.uniswap.org/swap?chain=avalanche"},
                        ]
        self.check_currency_valid = True
        self.channelid = channelid
    
    async def start_up(self):
        self.gather_instance = gather_action()
        # 本项目中，一次性将 gather_action 要用到的参数一次性传入，然后做一个永远手挂起的动作即可
        # async def gather_start_up(self,networks,channelid,detailed_url_get_data):
        await self.gather_instance.gather_start_up(self.networks,self.channelid,self.detailed_url_get_data)
        # await self.gather_instance.listening() 
        #await self.gather_instance.get_data(self.process_page)
        # 这将永远挂起，直到Future对象被取消或异常发生。这个会在unswap实例时即一调用就不停机
        # 对应的本处的实例应在fa
        # stapi中，也是在start_up时就实例化，不要在接收到数据时才实例化
        await asyncio.Future()  
   
    # 只在此处声明，但调用是在action处。opening_page_dict_from_action 就是已打开的page实例
    # result = asyncio.create_task(self.detailed_url_get_data(data_to_detailed_url_get,opening_page["page"]))
    # opening_page_dict_from_action::::  就是要处理的page实例，到时将result返回即可
    # 注意，此处不能只传入opening_page["page"],因虽然后者只用了opening_page["page"]的属性，但也要整个传回，
    # 因为下面的asyncio.gather 要对结果进行for 并用当时的page进行相当的操作
    # orignal_result = asyncio.create_task(self.detailed_url_get_data(data_to_detailed_url_get,opening_page))
    # 要求传回来的结果是 {"data":result, "opening_page":opening_page } 即opening_page 是原路返回。
        
    async def detailed_url_get_data(self, data_from_websocket,opening_page):
        try: 
            print(9999999) 
            # data_from_websocket {'coina': 'WBTC', 'coinb': 'WETH', 'amount': '1'}
            print("unitswap_got_data_from_websocket",data_from_websocket)
              
            network_name = opening_page["network_name"]
            page = opening_page["page"]
 
            element= None
            # "polygon" 点击及直接打开时的界面不一样
            if (network_name == "Ethereum" or  "arbitrum" or "optimism" or "base" or "polygon"):
                # 等待元素变得可见,即在加载，"attached" 的基础上，没有任何东西挡住。
                await page.wait_for_selector("xpath=//*[contains(text(), 'ETH')]", state="visible")
                # 然后选择该元素，*是任何CSS之意
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")

            if (network_name == "bnb" ):
                await page.wait_for_selector("xpath=//*[contains(text(), 'BNB')]", state="visible")
                element = await page.query_selector("xpath=//*[contains(text(), 'BNB')]")
            elif (network_name == "bnb" ):
                await page.wait_for_selector("xpath=//*[contains(text(), 'ETH')]", state="visible")
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")
            if (network_name == "avalanche" ):
                await page.wait_for_selector("xpath=//*[contains(text(), 'AVAX')]", state="visible")
                element = await page.query_selector("xpath=//*[contains(text(), 'AVAX')]")
            elif (network_name == "avalanche" ):
                await page.wait_for_selector("xpath=//*[contains(text(), 'ETH')]", state="visible")
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")

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
                print(max_slippage)

                '''Fee = await self.get_text(page,'Fee')
                print(Fee)'''

                Network_cost = await self.get_text(page,'Network cost')
                print("Network_cost::::",Network_cost)

                Order_routing = await self.get_text(page,'Order routing')

                #data = {"price":price,"max_slippage":max_slippage,"Fee":Fee, "Network_cost":Network_cost,"Order_routing":Order_routing }
                data = {"price":price,"max_slippage":max_slippage, "Network_cost":Network_cost,"Order_routing":Order_routing }
                
                print(network_name,"已有结果 :",data)
                return {"data":"data", "opening_page":opening_page }
            
            else: 
                return {"data":"Can not find currency", "opening_page":opening_page }
           
        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            return {"data":f"An error occurred: {e}", "opening_page":opening_page }
                

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
        self.check_currency_valid = False    #若它在20内找到了，就不会触发这个，否则会触发

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
    

    

async def uniswap_main():
    #只产生一个brower的实例
    uniswap_instance = uniswap("uniswap_websocket_url")
    '''
    此处的start_up()是个异步的方法，因它内部有一些await，一定要await，
    否则要用asyncio.run  变成顺序执行
    '''
    #要注意，本项目中，每个要采集的网站是一个固定的websocket_url,这个URL是事先定好的
    #本项目中，因gather_action 是公用的，所以这个id要在此作为变量传给gather_action
    #相关的 listening 及 gather 对应的websocket
    await uniswap_instance.start_up()

def uniswap_wrap_main():
    asyncio.run(uniswap_main())

#以下是fastapi的内容
async def fastapi_send_receive_data():
    #要注意，本项目中，每个要采集的网站是一个固定的websocket_url,这个URL是事先定好的
    webSocket_client_A = WebSocket_Client({"inputurl":"uniswap_websocket_url","role":"fastapi"})
    await webSocket_client_A.connect()
    # 直接使用你已经定义好的 `connected` 属性来检查连接状态
    if webSocket_client_A.connected:
        print("WebSocket 已成功连接")
    else:
        print("WebSocket 连接失败")
    # {“to_fastapi":data}
    await webSocket_client_A.send_message(json.dumps({"to_listening": {"request_ID":"request_ID" ,"data":{"coina":"WBTC","coinb":"WETH","amount":"1"}}}))
    data_from_websocket = await webSocket_client_A.receive_message()
    print("主线程收到:",data_from_websocket)

   

async def websocket_sever():
    server = WebSocket_Server()
    await server.start()

def wrap_websocket_sever():
    asyncio.run(websocket_sever())

if __name__ == "__main__":
    # 以下是模仿fastapi中，如何调用unswap代码
    #注意，调入的分进程是个函数，不能加(),同时不能是异步的，若是异步，一定要用asyncio.run变回同步
    uniswap = multiprocessing.Process(target=uniswap_wrap_main)
    # 启动子进程
    uniswap.start()
    websocket_sever = multiprocessing.Process(target=wrap_websocket_sever)
    # 启动子进程
    websocket_sever.start()
    #异步方法的调用不能直接用 main， 一定要用asyncio 关键字,并调用它的run方法才能将它包装成顺序执行
    asyncio.run(fastapi_send_receive_data())


    
   