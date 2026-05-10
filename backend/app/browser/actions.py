"""Browser action primitives — atomic operations the agent can perform."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    SELECT = "select"
    HOVER = "hover"
    DRAG = "drag"
    UPLOAD_FILE = "upload_file"
    EXECUTE_JS = "execute_js"
    EXTRACT_TEXT = "extract_text"
    GO_BACK = "go_back"
    GO_FORWARD = "go_forward"
    REFRESH = "refresh"
    NEW_TAB = "new_tab"
    CLOSE_TAB = "close_tab"
    SWITCH_TAB = "switch_tab"


@dataclass
class BrowserAction:
    action_type: ActionType
    params: dict[str, Any]
    description: str = ""

    @classmethod
    def navigate(cls, url: str) -> BrowserAction:
        return cls(ActionType.NAVIGATE, {"url": url}, f"Navigate to {url}")

    @classmethod
    def click(cls, selector: str) -> BrowserAction:
        return cls(ActionType.CLICK, {"selector": selector}, f"Click {selector}")

    @classmethod
    def click_coordinates(cls, x: int, y: int) -> BrowserAction:
        return cls(
            ActionType.CLICK,
            {"x": x, "y": y, "use_coordinates": True},
            f"Click at ({x}, {y})",
        )

    @classmethod
    def type_text(cls, selector: str, text: str) -> BrowserAction:
        return cls(
            ActionType.TYPE,
            {"selector": selector, "text": text},
            f"Type '{text[:30]}...' into {selector}",
        )

    @classmethod
    def press_key(cls, key: str) -> BrowserAction:
        return cls(ActionType.PRESS_KEY, {"key": key}, f"Press {key}")

    @classmethod
    def scroll(cls, direction: str = "down", amount: int = 300) -> BrowserAction:
        return cls(
            ActionType.SCROLL,
            {"direction": direction, "amount": amount},
            f"Scroll {direction} {amount}px",
        )

    @classmethod
    def screenshot(cls) -> BrowserAction:
        return cls(ActionType.SCREENSHOT, {}, "Take screenshot")

    @classmethod
    def wait(cls, seconds: float = 1.0) -> BrowserAction:
        return cls(ActionType.WAIT, {"seconds": seconds}, f"Wait {seconds}s")

    @classmethod
    def extract_text(cls, selector: str = "body") -> BrowserAction:
        return cls(
            ActionType.EXTRACT_TEXT,
            {"selector": selector},
            f"Extract text from {selector}",
        )

    @classmethod
    def execute_js(cls, script: str) -> BrowserAction:
        return cls(
            ActionType.EXECUTE_JS,
            {"script": script},
            f"Execute JS: {script[:50]}...",
        )

    @classmethod
    def go_back(cls) -> BrowserAction:
        return cls(ActionType.GO_BACK, {}, "Go back")

    @classmethod
    def go_forward(cls) -> BrowserAction:
        return cls(ActionType.GO_FORWARD, {}, "Go forward")

    @classmethod
    def refresh(cls) -> BrowserAction:
        return cls(ActionType.REFRESH, {}, "Refresh page")

    @classmethod
    def hover(cls, selector: str) -> BrowserAction:
        return cls(ActionType.HOVER, {"selector": selector}, f"Hover over {selector}")

    @classmethod
    def new_tab(cls, url: str = "") -> BrowserAction:
        return cls(ActionType.NEW_TAB, {"url": url}, f"Open new tab: {url}")

    @classmethod
    def close_tab(cls) -> BrowserAction:
        return cls(ActionType.CLOSE_TAB, {}, "Close current tab")

    @classmethod
    def switch_tab(cls, index: int) -> BrowserAction:
        return cls(ActionType.SWITCH_TAB, {"index": index}, f"Switch to tab {index}")
