import logging
import asyncio
import os
from automation.browser import ApplicationBrowser

logger = logging.getLogger(__name__)

class FormFiller:
    def __init__(self, browser_mgr: ApplicationBrowser, cv_data: dict, cv_file_path: str):
        self.browser_mgr = browser_mgr
        self.page = browser_mgr.page
        self.cv_data = cv_data
        self.cv_file_path = cv_file_path

    async def fill_generic_form(self):
        """Attempts to fill standard fields based on generic selectors."""
        logger.info("Attempting to fill form fields...")
        
        field_mappings = {
            "first_name": ["input[name*='first']", "input[id*='first']", "input[name*='fname']"],
            "last_name": ["input[name*='last']", "input[id*='last']", "input[name*='lname']"],
            "email": ["input[type='email']", "input[name*='email']", "input[id*='email']"],
            "phone": ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"],
            "linkedin": ["input[name*='linkedin']", "input[id*='linkedin']"],
            "github": ["input[name*='github']", "input[id*='github']", "input[name*='portfolio']"]
        }

        for cv_key, selectors in field_mappings.items():
            value = self.cv_data.get(cv_key)
            if not value:
                continue

            for selector in selectors:
                try:
                    locator = self.page.locator(selector).first
                    if await locator.is_visible() and await locator.is_enabled():
                        await locator.fill(value)
                        logger.info(f"Filled {cv_key} using selector: {selector}")
                        await asyncio.sleep(0.5)
                        break 
                except Exception as e:
                    logger.debug(f"Selector {selector} for {cv_key} failed: {e}")

    async def upload_cv(self):
        """Attempts to find file upload inputs and attach the CV."""
        if not os.path.exists(self.cv_file_path):
            logger.warning(f"CV file not found at {self.cv_file_path}. Skipping upload.")
            return

        logger.info("Looking for CV upload field...")
        file_inputs = self.page.locator("input[type='file']")
        count = await file_inputs.count()
        if count > 0:
            try:
                await file_inputs.first.set_input_files(self.cv_file_path)
                logger.info(f"Uploaded CV: {self.cv_file_path}")
            except Exception as e:
                logger.error(f"Failed to upload CV: {e}")
        else:
            logger.info("No file upload field found automatically.")

    async def take_screenshot(self, path: str):
        """Take a full page screenshot and save it."""
        try:
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved to {path}")
            return path
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None

    async def click_submit(self):
        """Attempt to find and click the submit button."""
        logger.info("Attempting to submit form...")
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Apply')"
        ]
        
        for selector in submit_selectors:
            try:
                locator = self.page.locator(selector).first
                if await locator.is_visible() and await locator.is_enabled():
                    await locator.click()
                    logger.info(f"Clicked submit using {selector}")
                    await asyncio.sleep(2) # wait for submission to process
                    return True
            except Exception as e:
                logger.debug(f"Failed to click submit button {selector}: {e}")
                
        logger.warning("Could not automatically find submit button.")
        return False
