import asyncio
import logging
from playwright.async_api import async_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)

class ApplicationBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, headless: bool = True):
        """Start the browser."""
        self.playwright = await async_playwright().start()
        # Use chromium
        self.browser = await self.playwright.chromium.launch(headless=headless, args=['--start-maximized'])
        self.context = await self.browser.new_context(no_viewport=True)
        self.page = await self.context.new_page()
        logger.info(f"Browser started (headless={headless}).")

    async def stop(self):
        """Stop the browser."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser stopped.")

    async def navigate(self, url: str):
        """Navigate to a URL."""
        logger.info(f"Navigating to {url} ...")
        await self.page.goto(url)
        # Give page time to fully load scripts
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
