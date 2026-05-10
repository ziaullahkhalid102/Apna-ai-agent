"""WebSocket endpoints for real-time streaming and task events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from fastapi import WebSocket, WebSocketDisconnect

if TYPE_CHECKING:
    from app.agent.task_manager import TaskManager
    from app.streaming.stream_manager import StreamManager

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Manages WebSocket connections for streaming and task events."""

    def __init__(
        self,
        stream_manager: StreamManager,
        task_manager: TaskManager,
    ) -> None:
        self._stream_manager = stream_manager
        self._task_manager = task_manager

    async def handle_stream(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._stream_manager.add_client(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                await self._handle_stream_input(websocket, data)
        except WebSocketDisconnect:
            pass
        finally:
            self._stream_manager.remove_client(websocket)

    async def handle_task_events(self, websocket: WebSocket, task_id: str) -> None:
        await websocket.accept()

        task = self._task_manager.get_task(task_id)
        if not task:
            await websocket.send_json({"error": f"Task {task_id} not found"})
            await websocket.close()
            return

        queue = self._task_manager.subscribe(task_id)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30)
                    await websocket.send_json(event)
                except asyncio.TimeoutError:
                    await websocket.send_json({"type": "heartbeat"})
        except WebSocketDisconnect:
            pass
        finally:
            self._task_manager.unsubscribe(task_id, queue)

    async def _handle_stream_input(self, websocket: WebSocket, data: str) -> None:
        try:
            message: dict[str, Any] = json.loads(data)
            msg_type = message.get("type", "")

            if msg_type == "mouse_click":
                x = int(message.get("x", 0))
                y = int(message.get("y", 0))
                logger.info("Human click at (%d, %d)", x, y)
            elif msg_type == "keyboard":
                key = message.get("key", "")
                logger.info("Human key press: %s", key)
            elif msg_type == "scroll":
                delta_y = int(message.get("deltaY", 0))
                logger.info("Human scroll: %d", delta_y)

        except (json.JSONDecodeError, ValueError):
            logger.warning("Invalid WebSocket message: %s", data[:100])
