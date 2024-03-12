from playwright.async_api import async_playwright    #注 async是异步式的，还有一个是sync是同步的
import asyncio


class gather_action:
    def __init__(self):
        self.pages_pool = []
        self.playwright = None
        self.browser = None
        self.context = None
        self.detailed_url_get_data = None
        self.networks = None
        self.lock = asyncio.Lock()
        
    # await self.gather_instance.gather_start_up("unisawp",self.networks,self.detailed_url_get_data)
    async def gather_start_up(self,website_name,networks,gather_fuction):
        self.detailed_url_get_data = gather_fuction
        self.networks = networks
        self.website_name = website_name
        self.playwright = await async_playwright().start() 
        self.browser = await self.playwright.chromium.launch(headless=False)
        #new_context()即打开一个新的浏览器实例上下文
        self.context = await self.browser.new_context(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        # 设置请求拦截器来禁用图片加载，lambda是匿名函数
        await self.context.route("**/*", lambda route: asyncio.create_task(self.handle_route(route,load_img = True)))
        await self.create_page(1)    #预先生成一批浏览器
        
    # 设置请求拦截器来禁用图片加载，lambda是匿名函数
    async def handle_route(self, route,load_img):
        try:
            if route.request.resource_type == "image" and load_img:
                await route.abort()
            else:
                await route.continue_()
        except Exception as e:
            print(f"Error handling route: {e}")


    async def create_reduce_pop_pages(self,action,opening_pages = None):
        print("我调用了锁一次，现在是：：：", action)
        async with self.lock:  # 获取锁
            if action == "reduce":
                print("action == reduce")
                if len(self.pages_pool) > 1:
                    '''
                    opening_pages.append({"network_name":network_name, "network_url":network_url,"page":page})
             # 这里不要用create_reduce_pop_pages，否则会冲突。同时因它只调在star_up处调用了一次，不会资源冲突的。
            self.pages_pool.append(opening_pages)
            '''
                    opening_pages = self.pages_pool.pop()
                    for opening_page in opening_pages:
                        await opening_page["page"].close();
                        print("我已关了其中一个")

            elif action == "add":
                self.pages_pool.append(opening_pages)
                print("add:::",len(self.pages_pool))
            elif action == "pop":
                print("pop:::",len(self.pages_pool))
                if len(self.pages_pool) >= 1:
                    return self.pages_pool.pop()
                else:
                    await self.create_page(1)
                    return self.pages_pool.pop()
            print("我解锁了")



    # 生成一样的实例：[[{mainnet:url，others:url，...}, {mainnet:page，others:page，...}]]
    async def create_page(self, batch_amount):
        for _ in range(batch_amount):
            opening_pages = []    #注，这个要放在此处，不能放在全局量处，因他每次都是全新的列表
            for network_dict in self.networks:
                result = asyncio.create_task(self.start_multi_website(network_dict))
                opening_pages.append(result)  
            opening_pages = await asyncio.gather(*opening_pages)
            # 这里不要用create_reduce_pop_pages，否则会冲突。同时因它只调在star_up处调用了一次，不会资源冲突的。
            self.pages_pool.append(opening_pages)

    async def start_multi_website(self,network_dict):
        network_name = list(network_dict.keys())[0]
        network_url = list(network_dict.values())[0]

        if self.website_name == "sushi":
            if network_name == "polygon":
                context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_polygon',
                    headless=False
                )
            elif network_name == "bnb":
                context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_bnb',
                    headless=False
                )
            elif network_name == "ethereum":
                context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_ethereum',
                    headless=False
                )
            elif network_name == "arbitrum_one":
                context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_arbitrum_one',
                    headless=False
                )
            elif network_name == "base":
                context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir='C:/Users/16502/AppData/Local/Google/Chrome/User_Data_base',
                    headless=False
                )
            # 用context.pages[0]，不要new一个新的，否则会再建立一个新的空白页面再执行代码
            page = context.pages[0]    
            await page.goto('https://www.sushi.com/swap',timeout=60000)
        else:
            if self.website_name == "curve":
                await self.context.route("**/*", lambda route: asyncio.create_task(self.handle_route(route,load_img = False)))
            page = await self.context.new_page()   #注意：这个page是一个实例
            await page.goto(network_url,timeout=60000)
        return {"network_name":network_name, "network_url":network_url,"page":page}
    



    async def start_gather(self,data):
        print("gather_action received:",data)
        opening_pages = await self.create_reduce_pop_pages("pop")
        opening_page_and_gathered_results = []
        for opening_page in opening_pages:
            result = asyncio.create_task(self.gather_with_timeout(data,opening_page))
            opening_page_and_gathered_results.append(result)
        opening_page_and_gathered_results = await asyncio.gather(*opening_page_and_gathered_results) 
        results = []
        #print("original_results:::",opening_page_and_gathered_results) 

        for opening_page_and_gathered_result in opening_page_and_gathered_results:
            opening_page = opening_page_and_gathered_result["opening_page"]
            result={}
            result[opening_page["network_name"]] = opening_page_and_gathered_result["data"]
            results.append(result)
        print(self.website_name，"获取各个ulr后得到的数据:",results)
        to_fastapi_result = {self.website_name : results}
        asyncio.create_task(self.go_default_url(opening_page_and_gathered_results))
        return to_fastapi_result
    
    async def gather_with_timeout(self,data,opening_page):
        try: 
            # 等待任务完成，设置超时时间
            result = await asyncio.wait_for(self.detailed_url_get_data(data,opening_page), 120)
            return result
        except asyncio.TimeoutError:
            return {"data":{"error":"time out during gathering data "}, "opening_page":opening_page }
    
    async def go_default_url(self,opening_page_and_gathered_results):
        only_once= True
        opening_pages = []
        for opening_page_and_gathered_result in opening_page_and_gathered_results:
            opening_page = opening_page_and_gathered_result["opening_page"]
            url = opening_page["network_url"]
            page = opening_page["page"]

            if only_once:    #只第一次要等，其它不用等
                await asyncio.sleep(3)     #此处要加时间，否则报错，会提示没处理完毕。原因不明
            only_once = False
            try:
                await page.goto(url,timeout=60000)              
                opening_pages.append({"network_name":opening_page["network_name"], "network_url":url,"page":page})
              
            except Exception as e:
                # 处理异常，可以记录日志或采取其他措施
                print(e)
        await self.create_reduce_pop_pages("add",opening_pages)
        await asyncio.sleep(30)
        print("我要调用reduce了")
        await self.create_reduce_pop_pages("reduce")


    def check_token_match(self,input_tokens,original_tokes):
        input_tokens_uppers = [coin.upper() for coin in input_tokens]
        keys_upper_to_original = {key.upper(): key for key in original_tokes.keys()}
        verified_token = []
        for input_tokens_upper in input_tokens_uppers: 
            if input_tokens_upper not in keys_upper_to_original:
                return False
            else:
                verified_token.append(keys_upper_to_original[input_tokens_upper])
        return verified_token
        

