 
import asyncio
import sys
import os
# 将本文件的父级目录添加到sys.path中
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from swap.gather_action import gather_action 
from swap.sushi.sushi_currency import shushi_currencies

class sushi():
    def __init__(self):
        self.networks = [{'ethereum':"https://www.sushi.com/swap"},
                         {"arbitrum_one":"https://www.sushi.com/swap"},
                         {'polygon':"https://www.sushi.com/swap"},
                         {"base":"https://www.sushi.com/swap"},
                         {'bnb':"https://www.sushi.com/swap"},
                         ]
        self.check_currency_valid = True
 
    async def start_up(self):
        self.gather_instance = gather_action()
        await self.gather_instance.gather_start_up("sushi",self.networks,self.detailed_url_get_data)
      

    async def start_gather(self,data):
        to_fastapi_result = await self.gather_instance.start_gather(data)
        return to_fastapi_result

        
    async def detailed_url_get_data(self, data_from_websocket,opening_page):
        input_coina = data_from_websocket["coina"]
        input_coinb = data_from_websocket["coinb"]
        network_name = opening_page["network_name"]
        for key in list(shushi_currencies.keys()):
            if key  ==  network_name:
                uniswap_currency = shushi_currencies[key]
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

            
            input_one_element = await page.query_selector("xpath=//input[contains(@placeholder, '0')]")
            parent_div = await input_one_element.query_selector("xpath=./../../../../..")
            input_one_img = await parent_div.query_selector('img')
            await input_one_img.click()
            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token or address')]", state="visible")


            await page.type('input[placeholder="Search by token or address"]', coina)
            await page.wait_for_selector(f'text="{coina}"')
            print(22222)


            coina_element = await page.query_selector(f'//*[contains(text(), "{coina}")]')
            await self.select_coin(page, coina, network_name)
            print("i have click ",coina)
            await asyncio.sleep(3)


            
            input_two_elements = await page.query_selector_all("xpath=//input[contains(@placeholder, '0')]")
            parent_div = await input_two_elements[1].query_selector("xpath=./../../../../..")
            input_two_img = await parent_div.query_selector('img')
            await input_two_img.click()
            await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token or address')]", state="visible")

            await page.type('input[placeholder="Search by token or address"]', coinb)
            print('55555')
            await page.wait_for_selector(f'text="{coinb}"')
            print("i will click", coinb)

            await self.select_coin(page, coinb, network_name)

            print("i have click on coinb")

            await page.wait_for_selector("xpath=//input[contains(@placeholder, '0.0')]", state="visible")
            
            element = await page.query_selector(f'//*[contains(text(), "{coinb}")]')
            
            
            await page.type('input[placeholder="0.0"]', amount)

                
            print(7777)

            await page.wait_for_selector("xpath=//*[contains(text(), 'Network fee')]", state="visible")
            print(8888)

            # 定位包含 "Network fee" 文本的 span 元素，然后获取其后紧跟着的同级 span 元素中的数值
            price_impact_element = await page.query_selector("xpath=//span[contains(text(), 'Price impact')]/following-sibling::span[1]")
            Est_received_element = await page.query_selector("xpath=//span[contains(text(), 'Est. received')]/following-sibling::span[1]")
            network_fee_element = await page.query_selector("xpath=//span[contains(text(), 'Network fee')]/following-sibling::span[1]")
            await asyncio.sleep(0.3)
            est_received = ""
            network_fee = ""  
            time = 0
            while (est_received == "" or network_fee == "") and time < 300:
                network_fee = await network_fee_element.text_content()
                price_impact = await price_impact_element.text_content()
                est_received = await Est_received_element.text_content()
                await asyncio.sleep(0.1)
                time = time + 1
            if "SUSHI" in est_received and coinb != "SUSHI" and coina != "SUSHI":
                return {"data":{"error":f"wrong in coinb click "}, "opening_page":opening_page }
            print(network_fee,price_impact,est_received)
            data = {"est_received":est_received, "network_fee":network_fee, "price_impact": price_impact, }

            return {"data":data, "opening_page":opening_page }
            
        except Exception as e:
            # 处理异常，可以记录日志或采取其他措施
            return {"data":{"error":f"{e} "}, "opening_page":opening_page }
                

    async def select_coin(self, page, coin, network_name):
        print("i am select_coin::::",coin)
        check_name = shushi_currencies[network_name][coin]
        await page.wait_for_selector(f'text="{check_name}"')    # 要加上这个，否则会因等不了报错
        coin_name_elements = await page.query_selector_all(f'//*[contains(text(), "{coin}")]')
        check_break = False
        for coin_element in coin_name_elements:
            print("i am in for")
            orignal_coin_element = coin_element
            nikename_parent_quantiy = 0 
            while nikename_parent_quantiy  < 3 :  
                print("im in while")
                parent_div = await coin_element.query_selector('xpath=..')  # 向上查找父级元素
                
                print(1111111111,check_name)

                element_with_text = await parent_div.query_selector(f"text='{check_name}'")

                if element_with_text:
                    print("will click",coin)
                    await orignal_coin_element.click()    # 注父级不能点。因它元素太大了
                    
                    check_break = True
                    break
                # 如果没有找到继续向上查找
                coin_element = parent_div  # 将父级元素作为下一个循环的起点
                nikename_parent_quantiy = nikename_parent_quantiy  + 1
            if check_break :
                break

 

    



'''#######################################################################################
###########################################################################################
测试代码'''

import asyncio
from playwright.async_api import async_playwright

double_check_add_instance_ever = []
async def get_currency(page):
    time = 0
    while time < 10:
        # 检测Connect Wallet 不能是二个，以确保钱包已连接上了
        elements = await page.query_selector_all(f'//*[contains(text(), "Connect Wallet")]')
        if len(list(enumerate(elements))) < 2:
            break
        time = time + 1
        await asyncio.sleep(1)

    await page.wait_for_selector("xpath=//input[contains(@placeholder, '0')]", state="visible")
    input_one_element = await page.query_selector("xpath=//input[contains(@placeholder, '0')]")
    parent_div = await input_one_element.query_selector("xpath=./../../../../..")
    input_one_img = await parent_div.query_selector('img')
    await input_one_img.click()
    await page.wait_for_selector("xpath=//input[contains(@placeholder, 'Search by token or address')]", state="visible")
    all_tokens = {}
    distance = 150
    await asyncio.sleep(5)
    while True :
        # 查找所有代币行的父元素 
           #元素找不出来，经常是要await
        token_elements = await page.query_selector_all('.font-semibold.text-gray-900')   # 类，若是多个用"."连接起来
        check_move = False
        # 提取并打印所有代币的名称
        for token_element in token_elements:
            full_name_text = await token_element.text_content()
            parent_div = await token_element.query_selector("xpath=./../..")
            description_element = await parent_div.query_selector(".text-sm.text-muted-foreground")
            
            description_text = await description_element.text_content()

            # sushi 有时移动太小时会导致它移不了，估计是有时会有失控现象。为了解决这个问题，检测下本次最后一个for
            # 时有没有得到新数值，若有的则代表没到底，否则，再加大distance再移一下，但若到300还是不动的就退出
            # 以下是在有新币时才移动的，没有新币时是不执行的
            if full_name_text not in all_tokens:
                all_tokens[full_name_text] = description_text
                print("我加入了：",full_name_text,description_text)
                print("现在长度是：",len([*list(all_tokens.values())]))
                #这个是for完后进入下一轮while时登记本轮for最后一个full_name_text. 
                # for if 不是一个块，check_move能穿透到外面，因此后面的if能检测得到
                check_move = True
        
        if check_move :
            distance = 150   #之前修改过distance，现在将它设回100
            await move(page,distance )
            #await asyncio.sleep(0.1)
        elif distance  < 200:
            distance = distance + 10   
            await move(page,distance )
            await asyncio.sleep(0.1)
        else:    #由这个来控制退出
            break
    
    print(all_tokens)
    print(len([*list(all_tokens.values())]))
    a = []
   
    for key in all_tokens:
        if key not in [*list(shushi_currencies["base"].keys())]:
            a.append(key)

    print("有些key是没有的:",a) 
  
    c= []
    for key in all_tokens:
        if all_tokens[key] != shushi_currencies["base"][key]:
            c.append(all_tokens[key])
    print("value不对的:",c)



async def move(page,distance):
    # 获取所有具有特定类名的元素,在playwright中，滑动不能用。只能借助js，同时若要从 PYTHON 传入
    # 变量给js，只能用参数方式传入，下面的""" 是多行的一种表示方式。同时PYTHON不能传句柄进去，
    # 所以这个elements 只能在js中自已获取。
    await page.evaluate("""
        (distance) => {
            elements = document.querySelectorAll('.scroll');
            elements[1].scrollBy(0, distance);
        }
    """, distance)
    print("移动了一次")


async def main(): 
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            #user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_polygon',
            #user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_bnb',
            #user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_ethereum',
            #user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_arbitrum_one',
            user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_base',
            headless=False
        )
        
        #page = await context.new_page()
        await context.pages[0].goto('https://www.sushi.com/swap')

        await get_currency(context.pages[0])

if __name__ == "__main__":
    coina = "TCAP"
    coinb = "ZETA"
    asyncio.run(main())




