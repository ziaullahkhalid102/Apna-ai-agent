"""Playwright-based browser controller for AI agent automation."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.browser.dom_parser import DOMParser
from app.config import settings

logger = logging.getLogger(__name__)


class BrowserController:
    """Controls a Chromium browser via Playwright for agent automation.

    Supports navigation, clicking, typing, screenshots, DOM extraction,
    and coordinate-based interactions for "computer use" style automation.
    """

    def __init__(self) -> None:
        self._playwright: Any = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._dom_parser = DOMParser()
        self._screenshot_counter = 0
        self._human_control = False

    @property
    def page(self) -> Page | None:
        return self._page

    @property
    def is_human_controlled(self) -> bool:
        return self._human_control

    async def start(self) -> None:
        os.makedirs(settings.screenshot_dir, exist_ok=True)

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.browser_headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
            ],
        )
        self._context = await self._browser.new_context(
            viewport={
                "width": settings.browser_viewport_width,
                "height": settings.browser_viewport_height,
            },
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        self._page = await self._context.new_page()
        logger.info("Browser started (headless=%s)", settings.browser_headless)

    async def stop(self) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._page = None
        logger.info("Browser stopped")

    async def navigate(self, url: str) -> str:
        if not self._page:
            raise RuntimeError("Browser not started")
        response = await self._page.goto(url, wait_until="domcontentloaded")
        await self._page.wait_for_load_state("networkidle")
        status = response.status if response else 0
        logger.info("Navigated to %s (status=%d)", url, status)
        return await self._page.title()

    async def click(self, selector: str) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.click(selector, timeout=settings.browser_timeout)

    async def click_coordinates(self, x: int, y: int) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.mouse.click(x, y)

    async def type_text(self, selector: str, text: str, clear: bool = True) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        if clear:
            await self._page.fill(selector, text, timeout=settings.browser_timeout)
        else:
            await self._page.type(selector, text, timeout=settings.browser_timeout)

    async def press_key(self, key: str) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        await self._page.keyboard.press(key)

    async def scroll(self, direction: str = "down", amount: int = 300) -> None:
        if not self._page:
            raise RuntimeError("Browser not started")
        delta = amount if direction == "down" else -amount
        await self._page.mouse.wheel(0, delta)

    async def screenshot(self, full_page: bool = False) -> str:
        if not self._page:
            raise RuntimeError("Browser not started")
        self._screenshot_counter += 1
        path = os.path.join(
            settings.screenshot_dir,
            f"screenshot_{int(time.time())}_{self._screenshot_counter}.png",
        )
        await self._page.screenshot(path=path, full_page=full_page)
        return path

    async def extract_text(self, selector: str = "body") -> str:
        if not self._page:
            raise RuntimeError("Browser not started")
        element = await self._page.query_selector(selector)
        if element:
            return await element.inner_text()
        return ""

    async def get_title(self) -> str:
        if not self._page:
            return ""
        return await self._page.title()

    async def get_url(self) -> str:
        if not self._page:
            return ""
        return self._page.url

    async def execute_js(self, script: str) -> Any:
        if not self._page:
            raise RuntimeError("Browser not started")
        return await self._page.evaluate(script)

    async def get_dom_snapshot(self) -> str:
        if not self._page:
            raise RuntimeError("Browser not started")
        tree = await self._page.accessibility.snapshot()
        if not tree:
            return "Empty accessibility tree"

        elements = self._dom_parser.parse_accessibility_tree(tree.get("children", []))
        return self._dom_parser.build_dom_summary(elements)

    async def get_interactive_elements(self) -> list[dict[str, Any]]:
        if not self._page:
            return []

        return await self._page.evaluate("""() => {
            const interactiveSelectors = [
                'a[href]', 'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="link"]', '[role="textbox"]',
                '[role="checkbox"]', '[role="radio"]', '[role="combobox"]',
                '[onclick]', '[tabindex]'
            ];
            const elements = document.querySelectorAll(interactiveSelectors.join(','));
            return Array.from(elements).slice(0, 200).map((el, i) => {
                const rect = el.getBoundingClientRect();
                return {
                    index: i,
                    tag: el.tagName.toLowerCase(),
                    text: (el.textContent || '').trim().substring(0, 100),
                    type: el.type || '',
                    id: el.id || '',
                    className: el.className || '',
                    href: el.href || '',
                    placeholder: el.placeholder || '',
                    ariaLabel: el.getAttribute('aria-label') || '',
                    role: el.getAttribute('role') || '',
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    visible: rect.width > 0 && rect.height > 0
                };
            }).filter(el => el.visible);
        }""")

    async def wait_for_selector(self, selector: str, timeout: int | None = None) -> bool:
        if not self._page:
            return False
        try:
            await self._page.wait_for_selector(
                selector, timeout=timeout or settings.browser_timeout
            )
            return True
        except Exception:
            return False

    async def go_back(self) -> None:
        if self._page:
            await self._page.go_back()

    async def go_forward(self) -> None:
        if self._page:
            await self._page.go_forward()

    async def refresh(self) -> None:
        if self._page:
            await self._page.reload()

    def enable_human_control(self) -> None:
        self._human_control = True
        logger.info("Human control enabled — agent paused")

    def disable_human_control(self) -> None:
        self._human_control = False
        logger.info("Human control disabled — agent resumed")

    async def wait_for_human(self, timeout: float = 300) -> None:
        deadline = asyncio.get_event_loop().time() + timeout
        while self._human_control:
            if asyncio.get_event_loop().time() > deadline:
                self._human_control = False
                break
            await asyncio.sleep(0.5)
