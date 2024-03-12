# netstat -aon | findstr :8001
# taskkill /F /PID 7208
 
import asyncio
import sys
import os
import json
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from swap.gather_action import gather_action
from swap.uniswap.uniswap_currency import uniswap_currencies


class uniswap():
    def __init__(self):
        self.networks = [{'ethereum':"https://app.uniswap.org/swap?chain=mainnet"},
                         {"arbitrum":"https://app.uniswap.org/swap?chain=arbitrum"},
                         {"optimism":"https://app.uniswap.org/swap?chain=optimism"},
                         {"polygon":"https://app.uniswap.org/swap?chain=polygon"},
                         {"base":"https://app.uniswap.org/swap?chain=base"},
                         {"bnb":"https://app.uniswap.org/swap?chain=bnb"},
                         {"avalanche":"https://app.uniswap.org/swap?chain=avalanche"},
                         {"celo":"https://app.uniswap.org/swap?chain=celo"},
                        ]
        self.check_currency_valid = True
 
    async def start_up(self):
        self.gather_instance = gather_action()
        await self.gather_instance.gather_start_up("unisawp",self.networks,self.detailed_url_get_data)
      

    async def start_gather(self,data):
        to_fastapi_result = await self.gather_instance.start_gather(data)
        return to_fastapi_result
        
    async def detailed_url_get_data(self, data_from_websocket,opening_page):
        input_coina = data_from_websocket["coina"]
        input_coinb = data_from_websocket["coinb"]
        for key in list(uniswap_currencies.keys()):
            if key  ==  opening_page["network_name"]:
                uniswap_currency = uniswap_currencies[key]
        input_tokens = [input_coina, input_coinb]
        input_tokens_verified = self.gather_instance.check_token_match(input_tokens, uniswap_currency)
        if input_tokens_verified == False:
            return {"data":{"error":f"Can not find currency:{input_coina} or {input_coinb} "}, "opening_page":opening_page }
        coina = input_tokens_verified[0]
        coinb = input_tokens_verified[1]
        
        try: 
            print("unitswap_got_data:::",data_from_websocket)
              
            network_name = opening_page["network_name"]
            page = opening_page["page"]
 
            element= None
            # "polygon" 点击及直接打开时的界面不一样
            if (network_name == "Ethereum" or  "arbitrum" or "optimism" or "base" or "polygon"):
                # 等待元素变得可见,即在加载，"attached" 的基础上，没有任何东西挡住。
                await page.wait_for_selector("xpath=//*[contains(text(), 'ETH')]", state="visible")
                # 然后选择该元素，*是任何CSS之意
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")

            await element.click()

            print(network_name,55555555555)
        
         
            # 等待输入字段可见
            await page.wait_for_selector('input[placeholder="Search name or paste address"]')
            print("Search name or paste address")

            # 在输入字段中输入文本
            await page.type('input[placeholder="Search name or paste address"]', coina)
            print(network_name, '66666')

            
            await self.enter_action(page)
            
            if self.check_currency_valid == True:
                select_token_button = await page.wait_for_selector('text=Select token')
                await select_token_button.click()
                print(network_name, '7777')


                await page.wait_for_selector('input[placeholder="Search name or paste address"]', state="visible")
                await page.type('input[placeholder="Search name or paste address"]', coinb)
                print(network_name, '8888')

    
                await self.enter_action(page)

                await page.wait_for_selector('.token-amount-input', state="visible")
                await page.type('.token-amount-input', data_from_websocket["amount"])
                print(network_name, '9999')

                checkprice = True
                time = 0
                while checkprice and time < 20:
                    price = await page.evaluate('(selector) => document.querySelectorAll(selector)[1].value', '.token-amount-input')
                    if price and price.strip():  # 检查price是否非空且非None
                        checkprice = False
                    await asyncio.sleep(0.5)
                    time= time+1


                # Price impact   这个不能加，因它有时有，有时没有的
                await page.wait_for_selector('xpath=//*[contains(text(), "Network cost")]')
            
                max_slippage = await self.get_text(page,'Max. slippage')
                print(network_name,"max_slippage:::::",max_slippage)


                Network_cost = await self.get_text(page,'Network cost')
                print(network_name,"Network_cost::::",Network_cost)

                Order_routing = await self.get_text(page,'Order routing')
                print(network_name,"Order_routing:::",Order_routing)

             #Fee很奇特，有些是没有的
                Fee = await self.get_text(page,'Fee')
                print(network_name,"Fee",Fee)

                data = {"price":price,"max_slippage":max_slippage,"Fee":Fee, "Network_cost":Network_cost,"Order_routing":Order_routing }
                
                
                print(network_name,"已有结果 :",data)
                return {"data":data, "opening_page":opening_page }
            
            else: 
                return {"data":{"error":f"Can not find currency:{data_from_websocket["coina"]} or {data_from_websocket["coinb"]} "}, "opening_page":opening_page }
                        
           
        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            return {"data":{"error":f"{opening_page}+{e}"}, "opening_page":opening_page }
                

    async def get_text(self, page, search_text):
        count = 0
        text = ""
        while count < 20:
            # 担心Fee可能是有多种情况不同，所以要一个contains,同时有些network是没有FEE的

            # playwright 找元素的是用query_selector，它分二个，一个是text内容的要用xpath，   
            # 另一个是是找css的，await page.wait_for_selector('.class')  后者是直接找
            containing_text_element = await page.query_selector(f'xpath=//*[contains(text(), "{search_text}")]')
            if  not containing_text_element:
                return 0
        
            parent_div = await containing_text_element.query_selector("xpath=./..")
            #以下方法很好，用js 获取当前元素的div内容，-------------要常用
            '''text = await parent_div.evaluate("element => element.outerHTML")
            print("outer:",text)'''
            #注意这个div的索引是1开头的
            target_div = await parent_div.query_selector("xpath=./div[2]")
            '''text = await target_div.evaluate("element => element.outerHTML")
            print("outer2:",text)'''

            # 获取文本并处理
            text = await target_div.inner_text()
            if text and text.strip():  # 检查text是否非空且非None
                text = text.strip()
                return text
            else:
                await asyncio.sleep(0.1)  # 等待一段时间后再尝试
                count = count+1

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


    

        

    





'''#######################################################################################
###########################################################################################
上面是闷UNISWAP的内容，以下是放在fastapi中的内容，可用于做局部测试'''
import asyncio
from playwright.async_api import async_playwright
import time



async def self_check_get_currency( page):
    await page.wait_for_selector("xpath=//*[contains(text(), 'ETH')]", state="visible")
    element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")
    await element.click()
    await page.wait_for_selector("xpath=//*[contains(text(), 'Popular tokens')]", state="visible")
    
    all_tokens = {}
    arrive_end = False
    while not arrive_end:
        token_elements = await page.query_selector_all(".CurrencyList__CurrencyName-sc-1dd0cc7b-1")
        
        arrive_end = True
        # 提取并打印所有代币的名称
        for token_element in token_elements:
            print("触发了for")
            full_name_text = await token_element.text_content()
            print(11111,full_name_text)

            # 使用正确的xpath语法向上查找父级元素
            parent_div = await token_element.query_selector("xpath=./../..")
            # 在父级元素下查找简称元素
            short_name_element = await parent_div.query_selector(".css-1m0dqmt")
            short_name_text = await short_name_element.text_content()
            print(2222,short_name_text)

            # 检查是否已经存在于字典中
            if short_name_text not in all_tokens:
                all_tokens[short_name_text] = full_name_text    #注意：是简称排前，整个网站一样
                print("我加入了：",short_name_text)
                arrive_end = False

        #以像素为单位滚动页面，其中0是水平，100是向下移,注意一定要是弹窗的最顶的一个容器，因只有它才有滑动条
        # playwright没有直接控制滑动的功能，只能借用js的功能
        # 定位这个滑条是最难的：首先第一步是找到这个拉动的块。注意是只找到能拉动的部份。用“检查”，
        # 然后搜索最先第一个text，用手式方式向上移动，找到第一块能选中全部币的部份，但要注意连接滑动条也包括了。
        # 将有关的代码copy出来，放在vs中，然后查找他的特征：
        """
        要准确地找到用于滑动的 `div` 并确定其选择器，通常需要考虑以下几个步骤：
        1. 特别是那些具有 `overflow`,`position` 属性或其他可能影响滑动行为的样式属性的元素。这些元素往往是滑动交互的候选目标。
        2. **寻找具有滚动行为的元素**：
            - 对于垂直滑动，查找 `overflow-y: scroll;` 或 `overflow-y: auto;`（如果希望仅在内容超出容器时出现滚动条）的元素。
            - 对于水平滑动，相应地查找 `overflow-x: scroll;` 或 `overflow-x: auto;`。
            - 检查这些元素的类名（class）或ID（id），这将是你在JavaScript中引用它们的方式。
        3. **构造选择器**: 因playwright不能直接使用滑动,只能用js. js代码如下:
            - 如果元素有ID，使用 `#yourElementId` 作为选择器。
            - 如果元素通过类名标识，使用 `.yourClassName` 作为选择器。注意，如果一个类名不是唯一的，`document.querySelector` 
              会选择第一个匹配的元素。
            - 也可以使用更复杂的CSS选择器，如子选择器 `>`，属性选择器 `[]`，或兄弟选择器 `+`, `~` 来精确定位元素。
        4. **测试选择器**：
            - 用 `document.querySelector('yourSelector').scrollBy(0, 100)` 来看是否能够触发滑动。

        # 对于curve来说，上面的方法又不可行。原因不明。当时的chatgpt的描述是：
        其实对于js来说，他是不分是否有overflow的，任何元素其实都有移动功能，如curve的getcurrency，它就基于li与ul采用同一个class来定位的，
        定位后找到第一个然后移动他，就实现不用overflow就可以实现移动了。overflow是基于显式的移动的css的，没有的，就用刚才的方法
        """

        await page.evaluate("document.querySelector('.sc-55063ecc-1.jQgCBv').scrollBy(0, 100)");

        print("移动了一次")

        await page.wait_for_timeout(100)  # 等待时间可能需要调整
        
    print(all_tokens)
    print(len([*list(all_tokens.values())]))
    a = []
   
    for key in all_tokens:
        if key not in [*list(uniswap_currencies["celo"].keys())]:
            a.append(key)

    print("有些key是没有的：",a) 
  
    c= []
    for key in all_tokens:
        if all_tokens[key] != uniswap_currencies["celo"][key]:
            c.append(all_tokens[key])
    print("value不对的:",c)

  

async def main(): 
    async with async_playwright() as p:
        # 启动浏览器，headless参数为False意味着浏览器会有界面显示
        browser = await p.chromium.launch(headless=False)
        # 打开一个新页面
        page = await browser.new_page()
        
        # 导航到指定的URL   https://app.uniswap.org/swap?chain=mainnet       https://app.uniswap.org/swap?chain=arbitrum
        await page.goto("https://app.uniswap.org/swap?chain=celo")  # 设置超时时间为10000毫秒（10秒）

        await self_check_get_currency(page)
        await asyncio.sleep(30000000000)

if __name__ == "__main__":
    coina = "TCAP"
    coinb = "ZETA"
    print(len(list(uniswap_currencies["celo"])))
    asyncio.run(main())
