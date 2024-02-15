import asyncio
from playwright.async_api import async_playwright
from time import sleep

class Uniswap:
    def __init__(self):
        self.networks = [{'Ethereum': "https://app.uniswap.org/swap?chain=mainnet"}]
        self.pages_pool = []
        self.task_queue = asyncio.Queue()
        self.lock = asyncio.Lock()  # 用于保护 self.pages_pool 的锁

    async def start_up(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        await self.context.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())
        await self.create_page(3)  # 初始创建页面不需要锁

    async def create_page(self, batch_amount):
        pages = []
        for _ in range(batch_amount):
            for network in self.networks:
                network_url = list(network.values())[0]
                network_name = list(network.keys())[0]
                page = await self.context.new_page()
                await page.goto(network_url)
                pages.append({network_name: page})
            async with self.lock:  # 只在修改 self.pages_pool 时使用锁
                self.pages_pool.append(pages)
        print(f"应是只有一条才对. Total pages now: {len(self.pages_pool)}")

    async def get_data(self):
        print("Attempting to fetch data...")
        pages = None
        async with self.lock:  # 只在访问 self.pages_pool 时使用锁
            if self.pages_pool:
                pages = self.pages_pool.pop()
        if pages:
            await asyncio.sleep(1)  # 模拟异步操作
            print("采集结束.开始时有三个一起结束，后面的不定，有可能是多个，也有可能是一到二个")
        else:
            print("No pages available, 进行加page.")
            await asyncio.create_task(self.create_page(1))  # 异步创建页面，不等待完成，一定要await
            await self.get_data()

    async def close(self):
        await self.browser.close()
        await self.playwright.stop()



async def main():
    uniswap_instance = Uniswap()
    await uniswap_instance.start_up()

    # Simulate multiple get_data calls
    await asyncio.gather(
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
        uniswap_instance.get_data(),
      
    )
    await asyncio.sleep(100000)

    await uniswap_instance.close()

if __name__ == "__main__":
    asyncio.run(main())
