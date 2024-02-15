'''
from playwright.async_api import async_playwright    #注 async是异步式的，还有一个是sync是同步的
import asyncio
from functools import partial

'''
{"optimism":"https://app.uniswap.org/swap?chain=optimism"},
                {"polygon":"https://app.uniswap.org/swap?chain=polygon"},
                {"base":"https://app.uniswap.org/swap?chain=base"},
                {"celo":"https://app.uniswap.org/swap?chain=celo"},
                {"bnb":"https://app.uniswap.org/swap?chain=bnb"}, 
                {"avalanche":"https://app.uniswap.org/swap?chain=avalanche"},
                '''

class uniswap:
    def __init__(self):
        self.networks = [{'Ethereum':"https://app.uniswap.org/swap?chain=mainnet"},
                        {"arbitrum": "https://app.uniswap.org/swap?chain=arbitrum"},
                ]
        self.pages_pool = []
        self.check_currency_valid = True
        self.initialized = asyncio.Event() #设置一个事件对象
        self.lock = asyncio.Lock()  # 添加一个异步锁

    async def start_up(self):
        self.playwright = await async_playwright().start()    #启动了一个异步的playwright
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        # 设置请求拦截器来禁用图片加载，lambda是匿名函数
        await self.context.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())
        await self.create_page(batch_amount=1)    #默认是生成二批



    # 生成一样的实例：[[{mainnet:page，others:page},{mainnet:page，others:page}]]
    async def create_page(self, batch_amount):
        for _ in range(batch_amount):
            pages = []    #注，这个要放在此处，不能放在全局量处，因他每次都是全新的列表
            for network_dict in self.networks:
                network_url = list(network_dict.values())[0]
                network_name = list(network_dict.keys())[0]
                page = await self.context.new_page()
                await page.goto(network_url)
                pages.append([network_name, network_url,page])
            self.pages_pool.append(pages)
            print(self.pages_pool)

        # 设置事件，set()表示初始化完成，用于控制初始化实例已完成
        self.initialized.set()
  

    async def get_data(self):
        pages = None
        if len(self.pages_pool)>0 :
            print(22222222222222222)
            pages = self.pages_pool.pop()
        else:
            await self.create_page(1)  #任何async方法都一定要await，否则报错
            # 查看事件状态，即原事件已运行了才可以调用。
            # 不能用锁，因锁会锁定没有用，锁了page还没准备好
            await self.initialized.wait() 
            pages = self.pages_pool.pop()
        await self.fetch_data_from_page(pages)
                
        
    async def add_pages(self):
        if len(self.pages_pool)<2 :
            add_page_amount = 2 - len(self.pages_pool)
            for _ in add_page_amount:
                self.create_page()

    '''#循环检测pages_pool,让一段时间内没有再使用，同时多于2 个的，就将它删除
    # pages.append([network_name, network_url,page])
    async def reduce_page(self, task, target_page):
        print("async def reduce_page(self, target:::::::::",target_page)
        await asyncio.sleep(10)  # 等待30秒
        async with self.lock:  # 获取锁
            if len(self.pages_pool) > 1:
                for page_info in self.pages_pool:
                    if page_info[2] == target_page:  
                        self.pages_pool.remove(page_info)'''

  
    
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

    async def fetch_data_from_page(self, page_dicts):
        tasks = []
        for page_dict in page_dicts:
            #建立协程并发办法，asyncio.create_task后只能跟一个动作------只有这个办法。
            # 用它后后部的下面的方法全是并发的。
            task = asyncio.create_task(self.process_page(page_dict))
            tasks.append(task)
  
    


  

    async def process_page(self, page_dict):
        try: 
            print(9999999)   
            network_name = page_dict[0]
            network_url = page_dict[1]
            page = page_dict[2]
            element = await page.wait_for_selector('.SwapCurrencyInputPanel__StyledTokenName-sc-4a8de273-9')
            await element.click()

            print(network_name,55555555555)

            # 等待输入字段可见
            await page.wait_for_selector('input[placeholder="Search name or paste address"]')

            # 在输入字段中输入文本
            await page.type('input[placeholder="Search name or paste address"]', 'WBTC')
            print(network_name, '66666')

            
            await self.enter_action(page)
            
            if self.check_currency_valid == True:
                select_token_button = await page.wait_for_selector('text=Select token')
                await select_token_button.click()
                print(network_name, '7777')

                await page.wait_for_selector('input[placeholder="Search name or paste address"]', state="visible")
                await page.type('input[placeholder="Search name or paste address"]', 'WETH')
                print(network_name, '8888')

    
                await self.enter_action(page)

                await page.wait_for_selector('.token-amount-input', state="visible")
                await page.type('.token-amount-input', '1')
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

                print(network_name,result)
                await page.goto(network_url)

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
        while count <20 :
            # 检查页面中是否存在特定元素,找不到就退出
            if not await page.locator('input[placeholder="Search name or paste address"]').count():
                return

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

            await asyncio.sleep(0.1)
            count = count + 1
        self.check_currency_valid = False

async def main():
    #只产生一个brower的实例
    uniswap_instance = uniswap()
    '''
    此处的start_up()是个异步的方法，因它内部有一些await，一定要await，
    否则要用asyncio.run  变成顺序执行
    '''
    await uniswap_instance.start_up()
 
    await uniswap_instance.get_data()
    await uniswap_instance.get_data()
    await asyncio.Future()  # 这将永远挂起，直到Future对象被取消或异常发生
    


if __name__ == "__main__":
    #异步方法的调用不能直接用 main， 一定要用asyncio 关键字,并调用它的run方法才能将它包装成顺序执行
    asyncio.run(main())'''