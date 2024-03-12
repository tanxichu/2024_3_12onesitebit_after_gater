
import asyncio
import sys
import os
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from swap.gather_action import gather_action 
from swap.curve.curve_currency import curve_currencies
class curve():
    def __init__(self):
        self.networks = [{'ethereum':"https://curve.fi/#/ethereum"},
                         {'arbitrum':"https://curve.fi/#/arbitrum"},
                         {'optimism':"https://curve.fi/#/optimism"},
                         {"polygon":"https://curve.fi/#/polygon"},
                         {"avalanche":"https://curve.fi/#/avalanche"},
                         {"gnosis":"https://curve.fi/#/xdai"},
                         {"fantom":"https://curve.fi/#/fantom"}
                         ]

    async def start_up(self):
        self.gather_instance = gather_action()
        await self.gather_instance.gather_start_up("curve",self.networks,self.detailed_url_get_data)
      

    async def start_gather(self,data):
        to_fastapi_result = await self.gather_instance.start_gather(data)
        return to_fastapi_result


        
    async def detailed_url_get_data(self, data_from_websocket,opening_page):
        input_coina = data_from_websocket["coina"]
        input_coinb = data_from_websocket["coinb"]
        for key in list(curve_currencies.keys()):
            if key  ==  opening_page["network_name"]:
                uniswap_currency = curve_currencies[key]
        input_tokens = [input_coina, input_coinb]
        input_tokens_verified = self.gather_instance.check_token_match(input_tokens, uniswap_currency)
        if input_tokens_verified == False:
            return {"data":{"error":f"Can not find currency:{input_coina} or {input_coinb} "}, "opening_page":opening_page }
        coina = input_tokens_verified[0]
        coinb = input_tokens_verified[1]
        
        try: 
            print(9999999) 
            print("got_data_from_websocket",data_from_websocket)
              
            page = opening_page["page"]
            amount = data_from_websocket["amount"]
              
            # 这个网站的load较慢
            await page.wait_for_selector("xpath=//*[contains(text(), 'Price impact')]", state="visible")

            input_one_elements = await page.query_selector_all("xpath=//input")
            print(len(input_one_elements))
            input_one_element = input_one_elements[2]   
            parent_div = await input_one_element.query_selector("xpath=./../../../../../..")
            await self.safe_click(parent_div)
            
            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token name or address')]", state="visible")
            
            print("will type coina:::",coina)
            await page.type('input[placeholder="Search by token name or address"]', coina)

            print('22222')
            await page.wait_for_selector(f'text="{coina}"',state = "visible")
            #img_element = await page.query_selector(f"xpath=//div[contains(text(), '{coina}')]/ancestor::div[contains(., '{coina}')]//img")
            text_element = await page.query_selector(f"xpath=//div[contains(text(), '{coina}')]")
            parent_div = await text_element.query_selector("xpath=./../../..")
            img_element =  await parent_div.query_selector('img')

            await img_element.click()

            #Cuver很特殊的，它在弹窗时还能在页面上找到旧的coin。同时页面的下载较电慢，所以目前用二个
            await page.wait_for_selector('text="Hide tokens from very small pools"', state='hidden')
            await page.wait_for_selector("xpath=//*[contains(text(), 'Price impact')]", state="visible")


            input_two_element = await page.query_selector('#inpTo')
            parent_div = await input_two_element.query_selector("xpath=./../../..")
            await self.safe_click(parent_div)
            


            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token name or address')]", state="visible")
            print("will type coinb:::",coinb)

            await page.type('input[placeholder="Search by token name or address"]', coinb)
            print('55555')

            #img_element = await page.query_selector(f"xpath=//div[contains(text(), '{coinb}')]/ancestor::div[contains(., '{coinb}')]//img")
            text_element = await page.query_selector(f"xpath=//div[contains(text(), '{coinb}')]")
            parent_div = await text_element.query_selector("xpath=./../../..")
            img_element =  await parent_div.query_selector('img')
            await img_element.click()
       
            await page.wait_for_selector(f"xpath=//*[contains(text(), {coinb})]", state="visible")

            elements = await page.query_selector_all('input')

            await elements[2].type(amount)
            time = 0
            price = ""   
            while time <60 and (not price):
                await asyncio.sleep(1)
                price = await elements[3].input_value()
                time = time + 1

            element_count = await page.locator('xpath=//span[contains(text(), "High price impact:")]/following-sibling::div').count()
            print(456)
            if element_count:
                element = page.locator('xpath=//span[contains(text(), "High price impact:")]/following-sibling::div')
                print(7777)
            else:
                element = page.locator('xpath=//span[contains(text(), "Price impact:")]/following-sibling::div')
                print(88888)
            print(123)
            price_impact = await element.text_content()
            print(9999)

            print(price_impact)
                
            data = {"price":price, "price_impact":price_impact}

            return {"data":data, "opening_page":opening_page }
            
        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            return {"data":{"error":f"{e} "}, "opening_page":opening_page }
                

    async def safe_click(self,element):
        img_element = await element.query_selector('img')
        while True : 
            if not img_element:
                await asyncio.sleep(0.5)
                img_element = await element.query_selector('img')
            else:
                await img_element.click()
                break


'''#######################################################################################
###########################################################################################
测试代码'''

import asyncio
from playwright.async_api import async_playwright

async def curve_swap_test(coina, coinb, amount):   
    async with async_playwright() as p:
        # 启动浏览器，headless参数为False意味着浏览器会有界面显示
        browser = await p.chromium.launch(headless=False)
        # 打开一个新页面
        page = await browser.new_page()
        
        # 导航到指定的URL
        await page.goto("https://curve.fi/#/ethereum")  # 设置超时时间为10000毫秒（10秒）

        await page.wait_for_selector("xpath=//*[contains(text(), 'USDT')]", state="visible")
        element = await page.query_selector('//*[contains(text(), "USDT")]')    

        await element.click()
        print(21111111111111111111111111111345)

        await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token name or address')]", state="visible")
        print(1111)
   

        await page.type(f'input[placeholder="Search by token name or address"]', coina)

        

        print('22222')
        await page.wait_for_selector(f'text="{coina}"')
        img_element = await page.query_selector(f"xpath=//div[contains(text(), '{coina}')]/ancestor::div[contains(., '{coina}')]//img")


        await img_element.click()
        
        if coina == "ETH":
            print(144444446)
            coinb_default_context = "USDT"
        else:
            print(123446)
            coinb_default_context = "ETH"
        await page.wait_for_selector(f"xpath=//*[contains(text(), {coina})]", state="visible")
        print(555555)
        element = await page.query_selector(f'//*[contains(text(), "{coinb_default_context}")]')  
        print(66666)  
        await element.click()


        await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token name or address')]", state="visible")
        print(44444)

        await page.type('input[placeholder="Search by token name or address"]', coinb)
        print('55555')
        await page.wait_for_selector(f'text="{coinb}"')
        img_element = await page.query_selector(f"xpath=//div[contains(text(), '{coinb}')]/ancestor::div[contains(., '{coinb}')]//img")

        await img_element.click()


        await page.wait_for_selector(f"xpath=//*[contains(text(), {coinb})]", state="visible")

        elements = await page.query_selector_all('input')

        await elements[2].type(amount)
        time = 0
        price = ""   
        while time <60 and (not price):
            await asyncio.sleep(1)
            price = await elements[3].input_value()
            time = time + 1
        print(price)
        # //span[contains(text(), 'High price impact:')]/following-sibling::div
        element_count = await page.locator('xpath=//span[contains(text(), "High price impact:")]/following-sibling::div').count()
        if element_count:
            element = page.locator('xpath=//span[contains(text(), "High price impact:")]/following-sibling::div')
        else:
            element = page.locator('xpath=//span[contains(text(), "Price impact:")]/following-sibling::div')
        price_impact = await element.text_content()

        print(price_impact)
        print(price, price_impact)
        await asyncio.sleep(10000)




























async def get_currency():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    # 打开一个新页面
    page = await browser.new_page()
    
    # 导航到指定的URL
    await page.goto("https://curve.fi/#/xdai/swap", wait_until='networkidle')   # 这个网站的load较慢

    input_one_elements = await page.query_selector_all("xpath=//input")
    input_one_element = input_one_elements[2]    #这二个input分别是2与3
    parent_div = await input_one_element.query_selector("xpath=./../../../../../..")
    input_one_img = await parent_div.query_selector('img')
    await input_one_img.click() 


    await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token name or address')]", state="visible")
    print(1111)


    all_tokens = {}
    end = False
    distance  = 150
    while distance < 200:
        end = True
        token_elements = await page.query_selector_all('.sc-96400c07-1.cwXbzv')
        
        # 提取并打印所有代币的名称
        for token_element in token_elements:  
            token = await token_element.inner_text()
            if token not in all_tokens:
                all_tokens[token] = token
                print("我加入了：",token)
                print("现在长度是：",len([*list(all_tokens.values())]))
                end = False
                distance = 100

        if end ==  True:
            distance = distance + 10

        #现在找到第一个元素。
        await page.evaluate("""(distance) => {
            document.querySelector('.sc-55063ecc-1.jQgCBv').scrollBy(0, 150);
            }""",distance )

    print(all_tokens)
    print(len(all_tokens))
    a = []
    for key in all_tokens:
        if key not in [*list(curve_currencies["gnosis"].keys())]:
            a.append(key)

    print("有些key是已保存的币中没有的，可能是新加的：",a) 
  
    c= []
    for key in all_tokens:
        if all_tokens[key] != curve_currencies["gnosis"][key]:
            c.append(all_tokens[key])
    print("已保存的币中 value与最新的value不对的，可能是新加的:",c)

    a = []
    for key in [*list(curve_currencies["gnosis"].keys())]:
        if key not in [*list(all_tokens.keys())]:
            a.append(key)

    print("有些key是已保存的币中 在最新网站中没有的，即可能是已删除不用的：",a) 
  



    

if __name__ == "__main__":
    '''coina = "ETH"
    coinb = "LDO"'''
    asyncio.run(get_currency())


