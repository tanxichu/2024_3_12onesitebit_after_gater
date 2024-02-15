
from playwright.async_api import async_playwright    #注 async是异步式的，还有一个是sync是同步的
import asyncio

'''
{"optimism":"https://app.uniswap.org/swap?chain=optimism"},
                {"polygon":"https://app.uniswap.org/swap?chain=polygon"},
                {"base":"https://app.uniswap.org/swap?chain=base"},
                {"celo":"https://app.uniswap.org/swap?chain=celo"},
                {"bnb":"https://app.uniswap.org/swap?chain=bnb"}, 
                {"avalanche":"https://app.uniswap.org/swap?chain=avalanche"},'''

class uniswap:
    def __init__(self):
        self.networks = [{'Ethereum':"https://app.uniswap.org/swap?chain=mainnet"},
                {"arbitrum": "https://app.uniswap.org/swap?chain=arbitrum"},
                ]
        self.total_pages_pairs = []
        self.check_currency_valid = True
        self.initialized = asyncio.Event()
        # 这个Queue() 除了序列功能外，还有一个功能是协程，它get出来的方法能自动实现并发协程功能
        #动态task要建立一个队列
        self.task_queue = asyncio.Queue()
        self.tasks = []  # 初始化任务列表

    async def start_up(self):
        self.playwright = await async_playwright().start()    #启动了一个异步的playwright
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        # 设置请求拦截器来禁用图片加载，lambda是匿名函数
        await self.context.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())
        await self.create_page(batch_amount=2)    #默认是生成二批

        
        while True:
            print("i am ture1111111111111111111111111")
            task_func, args = await self.task_queue.get()
            args= [args]   #特殊的，*args中的*用于不定长参数外，还有一个是解包功能。
                            #为避免此情况，此处人为加下外[]
            asyncio.create_task(task_func(*args))
            # task_done()是 asyncio.Queue 类的内置方法，用于告诉系统已执行完毕。若系统有 join方法的，一定要写。
            self.task_queue.task_done()

    #产生二批一样的实例
    # [[{mainnet:page，others:page},{mainnet:page，others:page}],  [{mainnet:page，others:page},{mainnet:page，others:page}]]
    async def create_page(self, batch_amount):
        for _ in range(batch_amount):
            pages = []    #注，这个要放在此处，不能放在全局量处，因他每次都是全新的列表
            for network_dict in self.networks:
                network_url = list(network_dict.values())[0]
                network_name = list(network_dict.keys())[0]
                page = await self.context.new_page()
                await page.goto(network_url)
                pages.append({network_name: page})
            self.total_pages_pairs.append(pages)
            print(self.total_pages_pairs)

        # 设置事件，set()表示初始化完成，用于控制初始化实例已完成
        self.initialized.set()
  

    async def get_data(self):
        print(33333333333333333333333333,len(self.total_pages_pairs))
        if len(self.total_pages_pairs)>0 :
            print(22222222222222222)
            pages = self.total_pages_pairs.pop()
            # 此处要加入一个元组
            await self.task_queue.put((self.fetch_data_from_page,pages))
                
        
    async def add_pages(self):
        if len(self.total_pages_pairs)<2 :
            add_page_amount = 2 - len(self.total_pages_pairs)
            for _ in add_page_amount:
                self.create_page()

    #循环检测total_pages_pairs,让一段时间内没有再使用，同时多于2 个的，就将它删除
    async def reduce_page(self):
        await asyncio.sleep(30)   #单位是秒
        if len(self.total_pages_pairs)>2 :
            self.total_pages_pairs.pop()
            self.reduce_page()

    async def fetch_data_from_page(self, page_dicts):
        tasks = []  # 创建一个任务列表
        for page_dict in page_dicts:
            # 为每个页面字典创建一个独立的任务
            task = asyncio.create_task(self.process_page(page_dict))
            tasks.append(task)
        # 等待所有页面处理任务完成
        await asyncio.gather(*tasks)

    async def process_page(self, page_dict):
        try: 
            print(9999999)   
            page = list(page_dict.values())[0]
            network_name = list(page_dict.keys())[0]
            element= None
            if (network_name == "Ethereum" or  "arbitrum" or "optimism" or "base"):
                print("i am hereeee!!!!!!!!!!!!")
                element = await page.query_selector("xpath=//*[contains(text(), 'ETH')]")
            elif (network_name == "polygon" ):
                #MATIC
                element = await page.query_selector("xpath=//*[contains(text(), 'MATIC')]")
            elif (network_name == "bnb" ):
                #BNB
                element = await page.query_selector("xpath=//*[contains(text(), 'BNB')]")
            elif (network_name == "avalanche" ):
                #AVAX
                element = await page.query_selector("xpath=//*[contains(text(), 'AVAX')]")
            elif (network_name == "celo" ):
                #celo   
                element = await page.query_selector("xpath=//*[contains(text(), 'celo')]")
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

                self.tasks.append(asyncio.create_task(self.reduce_page()) )
                await asyncio.gather(*self.tasks)

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

    async def close(self):
        # 使用 hasattr 检查属性是否存在，这样可以避免 AttributeError
        if hasattr(self, 'browser') and self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright') and self.playwright:
            await self.playwright.stop()

     





async def main():
    #只产生一个brower的实例
    uniswap_instance = uniswap()
    '''启动处理队列的循环协程但不等待它,相当于建立一个主的协程。很重要
    不能用 await uniswap_instance.start_up(). 但这个是非阻塞的，
    会导致下面的await uniswap_instance.get_data() 立即执行，
    但后者的序列中还没有建立好，所以会报错。可以用 await asyncio.sleep(30) 
    但它太不理想。现改用
    '''
    asyncio.create_task(uniswap_instance.start_up())
     # 等待初始化完成
    await uniswap_instance.initialized.wait()
    print("Initialization completed. I am start up.")
 
    await uniswap_instance.get_data()
    await uniswap_instance.get_data()
    await uniswap_instance.get_data()

    
    try:
        # 使用无限循环来保持程序运行
        await asyncio.Future()  # 这将永远挂起，直到Future对象被取消或异常发生
    finally:
        # 无论如何都会执行资源清理
        await uniswap_instance.close()


if __name__ == "__main__":
    asyncio.run(main())