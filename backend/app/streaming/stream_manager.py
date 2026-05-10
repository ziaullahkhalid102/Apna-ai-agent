"""WebSocket-based streaming manager for browser/desktop frames."""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Any

from app.browser.controller import BrowserController
from app.config import settings

logger = logging.getLogger(__name__)


class StreamManager:
    """Captures browser screenshots and streams them via WebSocket.

    Provides a frame loop that captures the browser viewport at a
    configurable FPS and pushes base64-encoded JPEG frames to
    connected WebSocket clients.
    """

    def __init__(self, browser: BrowserController) -> None:
        self._browser = browser
        self._clients: set[Any] = set()
        self._running = False
        self._fps = settings.stream_fps
        self._quality = settings.stream_quality
        self._frame_count = 0
        self._last_frame_time = 0.0

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def is_running(self) -> bool:
        return self._running

    def add_client(self, websocket: Any) -> None:
        self._clients.add(websocket)
        logger.info("Stream client connected (total=%d)", len(self._clients))

    def remove_client(self, websocket: Any) -> None:
        self._clients.discard(websocket)
        logger.info("Stream client disconnected (total=%d)", len(self._clients))

    async def start(self) -> None:
        self._running = True
        asyncio.create_task(self._frame_loop())
        logger.info("Stream manager started (fps=%d, quality=%d)", self._fps, self._quality)

    async def stop(self) -> None:
        self._running = False
        logger.info("Stream manager stopped")

    async def _frame_loop(self) -> None:
        interval = 1.0 / self._fps
        while self._running:
            if not self._clients:
                await asyncio.sleep(0.1)
                continue

            start = time.monotonic()
            try:
                frame = await self._capture_frame()
                if frame:
                    await self._broadcast(frame)
            except Exception:
                logger.exception("Error capturing/broadcasting frame")

            elapsed = time.monotonic() - start
            sleep_time = max(0, interval - elapsed)
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def _capture_frame(self) -> str | None:
        page = self._browser.page
        if not page:
            return None

        try:
            screenshot_bytes = await page.screenshot(
                type="jpeg",
                quality=self._quality,
            )
            self._frame_count += 1
            self._last_frame_time = time.time()
            return base64.b64encode(screenshot_bytes).decode("ascii")
        except Exception:
            return None

    async def _broadcast(self, frame_b64: str) -> None:
        message = {
            "type": "frame",
            "data": frame_b64,
            "frame_number": self._frame_count,
            "timestamp": self._last_frame_time,
        }

        dead_clients: set[Any] = set()
        for client in self._clients:
            try:
                await client.send_json(message)
            except Exception:
                dead_clients.add(client)

        for client in dead_clients:
            self._clients.discard(client)

    async def send_event(self, event_type: str, data: dict[str, Any]) -> None:
        message = {
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        }
        dead_clients: set[Any] = set()
        for client in self._clients:
            try:
                await client.send_json(message)
            except Exception:
                dead_clients.add(client)
        for client in dead_clients:
            self._clients.discard(client)
