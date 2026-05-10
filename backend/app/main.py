"""FastAPI entry point for the AI Agent Platform."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.agent.orchestrator import AgentOrchestrator
from app.agent.task_manager import TaskManager
from app.api.routes import create_routes
from app.api.websocket import WebSocketHandler
from app.browser.controller import BrowserController
from app.config import settings
from app.llm.ollama_client import OllamaClient
from app.streaming.stream_manager import StreamManager
from app.vault.credential_store import CredentialStore

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Service instances ──
task_manager = TaskManager()
llm = OllamaClient()
browser = BrowserController()
vault = CredentialStore()
stream_manager = StreamManager(browser)
orchestrator = AgentOrchestrator(llm, browser, task_manager)
ws_handler = WebSocketHandler(stream_manager, task_manager)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting AI Agent Platform...")

    try:
        await llm.start()
        logger.info("LLM client started")
    except Exception as e:
        logger.warning("LLM client unavailable (will work without it): %s", e)

    try:
        await browser.start()
        logger.info("Browser started")
    except Exception as e:
        logger.warning("Browser unavailable (will work without it): %s", e)

    try:
        await vault.initialize()
        logger.info("Vault initialized")
    except Exception as e:
        logger.warning("Vault unavailable: %s", e)

    try:
        await stream_manager.start()
        await orchestrator.start()
    except Exception as e:
        logger.warning("Orchestrator/stream partial start: %s", e)

    logger.info("Platform started (some services may be unavailable)")
    yield

    logger.info("Shutting down...")
    await orchestrator.stop()
    await stream_manager.stop()
    try:
        await vault.close()
    except Exception:
        pass
    try:
        await browser.stop()
    except Exception:
        pass
    try:
        await llm.stop()
    except Exception:
        pass
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Autonomous AI Agent Platform with browser control and cloud desktop",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = create_routes(task_manager, orchestrator, browser, llm, vault, stream_manager)
app.include_router(api_router)


# ── WebSocket endpoints ──


@app.websocket("/ws/stream")
async def ws_stream(websocket: WebSocket) -> None:
    await ws_handler.handle_stream(websocket)


@app.websocket("/ws/tasks/{task_id}")
async def ws_task_events(websocket: WebSocket, task_id: str) -> None:
    await ws_handler.handle_task_events(websocket, task_id)


# ── Root endpoint ──


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse(
        {
            "name": settings.app_name,
            "version": "0.1.0",
            "docs": "/docs",
            "status": "/api/v1/status",
            "websocket_stream": "/ws/stream",
        }
    )
