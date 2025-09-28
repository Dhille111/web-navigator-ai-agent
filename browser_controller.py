"""
Browser Controller using Playwright for web automation
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, ElementHandle
import os
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for browser automation"""
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: Optional[str] = None
    timeout: int = 30000
    slow_mo: int = 0  # milliseconds to slow down operations


@dataclass
class ActionResult:
    """Result of a browser action"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BrowserController:
    """Playwright-based browser controller for web automation"""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.config.timeout = 30000  # Fix timeout to 30 seconds
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start the browser and create context"""
        try:
            self.playwright = await async_playwright().start()
            
            # Launch browser
            browser_launch_options = {
                'headless': self.config.headless,
                'slow_mo': self.config.slow_mo
            }
            
            if self.config.browser_type == "chromium":
                self.browser = await self.playwright.chromium.launch(**browser_launch_options)
            elif self.config.browser_type == "firefox":
                self.browser = await self.playwright.firefox.launch(**browser_launch_options)
            elif self.config.browser_type == "webkit":
                self.browser = await self.playwright.webkit.launch(**browser_launch_options)
            else:
                raise ValueError(f"Unsupported browser type: {self.config.browser_type}")
            
            # Create context
            context_options = {
                'viewport': {
                    'width': self.config.viewport_width,
                    'height': self.config.viewport_height
                },
                'user_agent': self.config.user_agent
            }
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            # Set default timeout (fix the 15ms issue)
            self.page.set_default_timeout(30000)  # 30 seconds
            
            logger.info(f"Browser started: {self.config.browser_type} (headless={self.config.headless})")
            
        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            raise
    
    async def close(self):
        """Close browser and cleanup"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            logger.info("Browser closed")
            
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
    
    async def goto(self, url: str, timeout: Optional[int] = None) -> ActionResult:
        """Navigate to a URL"""
        try:
            logger.info(f"Navigating to: {url}")
            
            # Use 30 seconds timeout instead of 15ms
            response = await self.page.goto(url, timeout=30000)
            
            if response and response.status >= 400:
                return ActionResult(
                    success=False,
                    error=f"HTTP {response.status}: {response.status_text}"
                )
            
            return ActionResult(
                success=True,
                data={'url': url, 'status': response.status if response else None},
                metadata={'action': 'goto', 'url': url}
            )
            
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'goto', 'url': url}
            )
    
    async def click(self, selector: str, timeout: Optional[int] = None) -> ActionResult:
        """Click on an element"""
        try:
            logger.info(f"Clicking element: {selector}")
            
            # Wait for element to be visible and clickable
            await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            
            # Click the element
            await self.page.click(selector)
            
            return ActionResult(
                success=True,
                data={'selector': selector},
                metadata={'action': 'click', 'selector': selector}
            )
            
        except Exception as e:
            logger.error(f"Failed to click {selector}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'click', 'selector': selector}
            )
    
    async def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> ActionResult:
        """Fill an input field"""
        try:
            logger.info(f"Filling {selector} with: {value}")
            
            # Wait for element to be visible
            await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            
            # Clear and fill the field
            await self.page.fill(selector, value)
            
            return ActionResult(
                success=True,
                data={'selector': selector, 'value': value},
                metadata={'action': 'fill', 'selector': selector, 'value': value}
            )
            
        except Exception as e:
            logger.error(f"Failed to fill {selector}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'fill', 'selector': selector, 'value': value}
            )
    
    async def extract(self, selector: str, multiple: bool = False, timeout: Optional[int] = None) -> ActionResult:
        """Extract content from elements"""
        try:
            logger.info(f"Extracting from: {selector} (multiple={multiple})")
            
            if multiple:
                # Extract from multiple elements
                elements = await self.page.query_selector_all(selector)
                data = []
                
                for element in elements:
                    element_data = await self._extract_element_data(element)
                    if element_data:
                        data.append(element_data)
                
                return ActionResult(
                    success=True,
                    data=data,
                    metadata={'action': 'extract', 'selector': selector, 'count': len(data)}
                )
            else:
                # Extract from single element
                element = await self.page.query_selector(selector)
                if not element:
                    return ActionResult(
                        success=False,
                        error=f"Element not found: {selector}"
                    )
                
                data = await self._extract_element_data(element)
                return ActionResult(
                    success=True,
                    data=data,
                    metadata={'action': 'extract', 'selector': selector}
                )
                
        except Exception as e:
            logger.error(f"Failed to extract from {selector}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'extract', 'selector': selector}
            )
    
    async def _extract_element_data(self, element: ElementHandle) -> Dict[str, Any]:
        """Extract data from a single element"""
        try:
            data = {}
            
            # Get text content
            text = await element.text_content()
            if text:
                data['text'] = text.strip()
            
            # Get HTML content
            html = await element.inner_html()
            if html:
                data['html'] = html
            
            # Get attributes
            attributes = await element.evaluate("el => el.attributes")
            if attributes:
                data['attributes'] = attributes
            
            # Get tag name
            tag_name = await element.evaluate("el => el.tagName")
            if tag_name:
                data['tag'] = tag_name.lower()
            
            # Get href if it's a link
            href = await element.get_attribute('href')
            if href:
                data['href'] = href
            
            # Get src if it's an image
            src = await element.get_attribute('src')
            if src:
                data['src'] = src
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to extract element data: {e}")
            return {}
    
    async def wait(self, timeout: int) -> ActionResult:
        """Wait for a specified time"""
        try:
            logger.info(f"Waiting for {timeout} seconds")
            await asyncio.sleep(timeout)
            
            return ActionResult(
                success=True,
                data={'wait_time': timeout},
                metadata={'action': 'wait', 'timeout': timeout}
            )
            
        except Exception as e:
            logger.error(f"Wait failed: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'wait', 'timeout': timeout}
            )
    
    async def screenshot(self, filename: Optional[str] = None) -> ActionResult:
        """Take a screenshot"""
        try:
            if not filename:
                timestamp = int(time.time())
                filename = f"screenshot_{timestamp}.png"
            
            screenshot_path = self.screenshots_dir / filename
            
            await self.page.screenshot(path=str(screenshot_path))
            
            logger.info(f"Screenshot saved: {screenshot_path}")
            
            return ActionResult(
                success=True,
                data={'screenshot_path': str(screenshot_path)},
                screenshot_path=str(screenshot_path),
                metadata={'action': 'screenshot', 'filename': filename}
            )
            
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'screenshot'}
            )
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get current page information"""
        try:
            return {
                'url': self.page.url,
                'title': await self.page.title(),
                'viewport': await self.page.viewport_size()
            }
        except Exception as e:
            logger.error(f"Failed to get page info: {e}")
            return {}
    
    async def safe_click(self, selector: str, timeout: Optional[int] = None) -> ActionResult:
        """Safely click an element with error handling"""
        try:
            # Try to find the element first
            await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            
            # Check if element is visible and enabled
            is_visible = await self.page.is_visible(selector)
            is_enabled = await self.page.is_enabled(selector)
            
            if not is_visible:
                return ActionResult(
                    success=False,
                    error=f"Element not visible: {selector}"
                )
            
            if not is_enabled:
                return ActionResult(
                    success=False,
                    error=f"Element not enabled: {selector}"
                )
            
            # Click the element
            await self.page.click(selector)
            
            return ActionResult(
                success=True,
                data={'selector': selector},
                metadata={'action': 'safe_click', 'selector': selector}
            )
            
        except Exception as e:
            logger.error(f"Safe click failed for {selector}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'safe_click', 'selector': selector}
            )
    
    async def safe_extract(self, selector: str, multiple: bool = True, timeout: Optional[int] = None) -> ActionResult:
        """Safely extract content with error handling"""
        try:
            # Wait for elements to be present
            if multiple:
                await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            else:
                await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)
            
            return await self.extract(selector, multiple, timeout)
            
        except Exception as e:
            logger.error(f"Safe extract failed for {selector}: {e}")
            return ActionResult(
                success=False,
                error=str(e),
                metadata={'action': 'safe_extract', 'selector': selector}
            )


class BrowserControllerFactory:
    """Factory for creating browser controllers"""
    
    @staticmethod
    def create_controller(
        headless: bool = True,
        browser_type: str = "chromium",
        **kwargs
    ) -> BrowserController:
        """Create a browser controller with specified configuration"""
        config = BrowserConfig(
            headless=headless,
            browser_type=browser_type,
            **kwargs
        )
        return BrowserController(config)


# Example usage
async def main():
    """Example usage of browser controller"""
    config = BrowserConfig(headless=False, slow_mo=1000)
    
    async with BrowserController(config) as browser:
        # Navigate to a page
        result = await browser.goto("https://www.google.com")
        print(f"Navigation result: {result.success}")
        
        # Fill search box
        result = await browser.fill("input[name='q']", "playwright python")
        print(f"Fill result: {result.success}")
        
        # Click search button
        result = await browser.click("input[type='submit']")
        print(f"Click result: {result.success}")
        
        # Wait for results
        await browser.wait(3)
        
        # Extract results
        result = await browser.extract(".g", multiple=True)
        print(f"Extract result: {result.success}, found {len(result.data) if result.data else 0} results")
        
        # Take screenshot
        result = await browser.screenshot("google_search.png")
        print(f"Screenshot result: {result.success}")


if __name__ == "__main__":
    asyncio.run(main())
