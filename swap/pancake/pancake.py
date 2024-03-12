 
import asyncio
import sys
import os
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from swap.gather_action import gather_action 
from swap.pancake.pancake_currency import pancake_currencies

class pancake():
    def __init__(self):
        self.networks = [{'ethereum':"https://pancakeswap.finance/swap?chain=eth"},
                         {'bnb':"https://pancakeswap.finance/swap?chain=bsc"},
                         {'opbnb':"https://pancakeswap.finance/swap?chain=opBNB"},
                         {'zksync':"https://pancakeswap.finance/swap?chain=zkSync"},
                         {'base':"https://pancakeswap.finance/swap?chain=base"},
                         {'aptos':"https://aptos.pancakeswap.finance/swap"},                 
                         ]
 
    async def start_up(self):
        self.gather_instance = gather_action()
        await self.gather_instance.gather_start_up("pancake",self.networks,self.detailed_url_get_data)
      

    async def start_gather(self,data):
        to_fastapi_result = await self.gather_instance.start_gather(data)
        return to_fastapi_result

        
    async def detailed_url_get_data(self, data_from_websocket,opening_page):
        input_coina = data_from_websocket["coina"]
        input_coinb = data_from_websocket["coinb"]
        network_name = opening_page["network_name"]
        for key in list(pancake_currencies.keys()):
            if key  ==  network_name:
                uniswap_currency = pancake_currencies[key]
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
 
            
            await page.wait_for_selector("xpath=//input[contains(@placeholder, '0.0')]", state="visible")

            input_one_elements = await page.query_selector_all('input[placeholder="0.0"]')
            input_one_element = input_one_elements[0]
            parent_div = await input_one_element.query_selector("xpath=./../../../..")
            # 没有了img，网站用了一个svg来代替，所以定位他也是可以的
            input_one_img = await parent_div.query_selector('svg')
            
            await input_one_img.click() 

            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search name or paste address')]", state="visible")
            print(1111)

            await page.type('input[placeholder="Search name or paste address"]', coina)
            
            await self.enter_action(page)
            print(22222)


            await page.wait_for_selector("xpath=//input[contains(@placeholder, '0.0')]", state="visible")

            input_elements = await page.query_selector_all('input[placeholder="0.0"]')
            input_two_element = input_elements[1]
            await input_two_element.type("222222")
            parent_div = await input_two_element.query_selector("xpath=./../../../..")
            # 没有了img，网站用了一个svg来代替，所以定位他也是可以的
            input_two_img = await parent_div.query_selector('svg')
            
            await input_two_img.click() 

            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search name or paste address')]", state="visible")
            print(3333)

            await page.type('input[placeholder="Search name or paste address"]', coinb)
            # 这个方法很好用，在input处输入的内容不算是text，只能算是value的数值。因此可以避免误判
            await asyncio.sleep(0.1)
            print(44444)

            await self.enter_action(page)
            print(55555)

            await page.wait_for_selector("xpath=//input[contains(@placeholder, '0.0')]", state="visible")
            
            await page.type('input[placeholder="0.0"]', amount)
    
            print(7777)

            # 以下是等页面进行跳转
            # 这个方法很好用，在input处输入的内容不算是text，只能算是value的数值。也可以作为普通的页面出现了这个内容
            # 现在这个是是完全text相同，若只是包含的可用正表达式，如  await page.wait_for_selector("text=/Minimum received/")
            # 同时这个方法是等元素 的DOM完全load完，相当于 playwright的 “visible”，若是js动态加载的要等它完全加载才算await完
            # 同时它区分大小写
            await page.wait_for_selector("text='Minimum received'")
            Minimum_received = await self.gather_value(page,'Minimum received') 
            print(Minimum_received)
            Price_Impact = await self.gather_value(page,'Price Impact')
            print(Price_Impact) 
            Trading_Fee = await self.gather_value(page,'Trading Fee') 
            print(Trading_Fee)


            data = {"Minimum_received":Minimum_received, "Price_Impact":Price_Impact, "Trading_Fee": Trading_Fee, }
            

            return {"data":data, "opening_page":opening_page }
            
        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            return {"data":{"error":f"{e} "}, "opening_page":opening_page }
                

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


    async def gather_value(self,page,target):
        time = 0
        while time < 20:
            describe_element = await page.query_selector(f'xpath=//*[contains(text(), "{target}")]')
            parent_div = await describe_element.query_selector("xpath=./../..")
            second_div = await parent_div.query_selector("xpath=./div[2]")
            text = await second_div.inner_text()
            if text != "":
                return text
            time = time +1
            await asyncio.sleep(0.1)
        
 

    

    



'''#######################################################################################
###########################################################################################
测试代码'''
from playwright.async_api import async_playwright

async def get_currency():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    # 打开一个新页面
    page = await browser.new_page()
    
    # 导航到指定的URL
    await page.goto("https://aptos.pancakeswap.finance/swap")   
    # Trade tokens in an instant
    await page.wait_for_selector("xpath=//*[contains(text(), 'Trade tokens in an instant')]", state="visible")

    await asyncio.sleep(2)
    input_one_elements = await page.query_selector_all('input[placeholder="0.0"]')
    input_one_element = input_one_elements[0]
    parent_div = await input_one_element.query_selector("xpath=./../../../../../..")
    input_one_img = await parent_div.query_selector('img')
    await input_one_img.click() 


    await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search name or paste address')]", state="visible")
    print(1111)
    


    all_tokens = {}
    end = False
    distance  = 150
    while distance < 200:
        end = True
        # _1i5r5na0 ern30g6i ern30gc ern30g220   这个是aptos 的class    _1i5r5na0 ern30g6 ern30g16 ern30g7c
        # ._1a5xov70._1qhetbf6._1qhetbf16._1qhetbf7c'   这个是aptos 外的其它class

        parent_elements = await page.query_selector_all('._1i5r5na0.ern30g6.ern30g16.ern30g7c')
        # 上面的parent_elements第一个是没有token_description的，可能原网站内容设计了给推荐用的。所以要用try
        for parent_element in parent_elements:
            try:
                #以下二个是aptos 的class，aptos 外的其它class是其它的
                token_element = await parent_element.query_selector('.sc-jSwlEQ.knGzug')
                token = await token_element.inner_text()
                token_description_element = await parent_element.query_selector('.sc-jSwlEQ.gUakbh')
                token_description = await token_description_element.inner_text()
            except:
                print("i am exept")
                continue

            if token not in all_tokens:
                all_tokens[token] = token_description
                print("我加入了：",token)
                print("现在长度是：",len([*list(all_tokens.values())]))
                end = False
                distance = 100

        if end ==  True:
            distance = distance + 10
        # 不一定通过class或id定位，任何css都能定位
        await page.evaluate("""(distance) => {
            container = document.querySelector("div[style*='position: relative; height: 390px;']");
            container.scrollBy(0, distance);
            }
        """,distance)

        
        print("i have moved 10")

    print(all_tokens)
    print(len(all_tokens))
    a = []
    for key in all_tokens:
        if key not in [*list(pancake_currencies["aptos"].keys())]:
            a.append(key)

    print("有些key是已保存的币中没有的，可能是新加的：",a) 
  
    c= []
    for key in all_tokens:
        if all_tokens[key] != pancake_currencies["aptos"][key]:
            c.append(all_tokens[key])
    print("已保存的币中 value与最新的value不对的，可能是新加的:",c)

    a = []
    for key in [*list(pancake_currencies["aptos"].keys())]:
        if key not in [*list(all_tokens.keys())]:
            a.append(key)

    print("有些key是已保存的币中 在最新网站中没有的，即可能是已删除不用的：",a) 
  



    

if __name__ == "__main__":
    '''coina = "ETH"
    coinb = "LDO"'''
    asyncio.run(get_currency())




