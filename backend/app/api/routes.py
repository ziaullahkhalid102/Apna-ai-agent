"""REST API routes for the AI Agent Platform."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agent.task_manager import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agent"])


class TaskCreate(BaseModel):
    command: str
    metadata: dict[str, Any] | None = None


class HumanInput(BaseModel):
    input_data: dict[str, Any]


class CredentialStore(BaseModel):
    service: str
    username: str
    credentials: dict[str, str]


class CredentialRetrieve(BaseModel):
    service: str
    username: str


class ModelPull(BaseModel):
    model_name: str


def create_routes(
    task_manager: Any,
    orchestrator: Any,
    browser: Any,
    llm: Any,
    vault: Any,
    stream_manager: Any,
) -> APIRouter:
    """Create API routes with injected dependencies."""

    # ── Tasks ──

    @router.post("/tasks")
    async def create_task(body: TaskCreate) -> dict[str, Any]:
        task = await task_manager.create_task(body.command, body.metadata)
        return {"task_id": task.id, "status": task.status.value}

    @router.get("/tasks")
    async def list_tasks(status: str | None = None, limit: int = 50) -> dict[str, Any]:
        task_status = TaskStatus(status) if status else None
        tasks = task_manager.list_tasks(status=task_status, limit=limit)
        return {
            "tasks": [
                {
                    "id": t.id,
                    "command": t.command,
                    "status": t.status.value,
                    "steps_count": len(t.steps),
                    "created_at": t.created_at.isoformat(),
                }
                for t in tasks
            ]
        }

    @router.get("/tasks/{task_id}")
    async def get_task(task_id: str) -> dict[str, Any]:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {
            "id": task.id,
            "command": task.command,
            "status": task.status.value,
            "steps": [
                {
                    "id": s.id,
                    "action": s.action,
                    "description": s.description,
                    "status": s.status.value,
                    "result": s.result,
                    "error": s.error,
                }
                for s in task.steps
            ],
            "result": task.result,
            "error": task.error,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }

    @router.post("/tasks/{task_id}/human-input")
    async def provide_human_input(task_id: str, body: HumanInput) -> dict[str, str]:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await task_manager.provide_human_input(task_id, body.input_data)
        return {"status": "input_received"}

    @router.post("/tasks/{task_id}/cancel")
    async def cancel_task(task_id: str) -> dict[str, str]:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        await task_manager.fail_task(task_id, "Cancelled by user")
        return {"status": "cancelled"}

    # ── Browser ──

    @router.post("/browser/navigate")
    async def browser_navigate(url: str) -> dict[str, str]:
        title = await browser.navigate(url)
        return {"url": url, "title": title}

    @router.get("/browser/screenshot")
    async def browser_screenshot() -> dict[str, str]:
        path = await browser.screenshot()
        return {"path": path}

    @router.get("/browser/dom")
    async def browser_dom() -> dict[str, str]:
        dom = await browser.get_dom_snapshot()
        return {"dom": dom}

    @router.get("/browser/url")
    async def browser_url() -> dict[str, str]:
        return {"url": await browser.get_url(), "title": await browser.get_title()}

    @router.get("/browser/elements")
    async def browser_elements() -> dict[str, Any]:
        elements = await browser.get_interactive_elements()
        return {"elements": elements, "count": len(elements)}

    @router.post("/browser/human-control/enable")
    async def enable_human_control() -> dict[str, str]:
        browser.enable_human_control()
        return {"status": "human_control_enabled"}

    @router.post("/browser/human-control/disable")
    async def disable_human_control() -> dict[str, str]:
        browser.disable_human_control()
        return {"status": "human_control_disabled"}

    # ── LLM ──

    @router.get("/llm/models")
    async def list_models() -> dict[str, Any]:
        models = await llm.list_models()
        return {"models": models}

    @router.post("/llm/pull")
    async def pull_model(body: ModelPull) -> dict[str, str]:
        await llm.pull_model(body.model_name)
        return {"status": "pulled", "model": body.model_name}

    @router.get("/llm/health")
    async def llm_health() -> dict[str, bool]:
        healthy = await llm.health_check()
        return {"healthy": healthy}

    # ── Vault ──

    @router.post("/vault/credentials")
    async def store_credentials(body: CredentialStore) -> dict[str, str]:
        await vault.store(body.service, body.username, body.credentials)
        return {"status": "stored"}

    @router.post("/vault/credentials/retrieve")
    async def retrieve_credentials(body: CredentialRetrieve) -> dict[str, Any]:
        creds = await vault.retrieve(body.service, body.username)
        if not creds:
            raise HTTPException(status_code=404, detail="Credentials not found")
        return {"service": body.service, "username": body.username, "credentials": creds}

    @router.delete("/vault/credentials/{service}/{username}")
    async def delete_credentials(service: str, username: str) -> dict[str, str]:
        deleted = await vault.delete(service, username)
        if not deleted:
            raise HTTPException(status_code=404, detail="Credentials not found")
        return {"status": "deleted"}

    @router.get("/vault/services")
    async def list_services() -> dict[str, Any]:
        services = await vault.list_services()
        return {"services": services}

    # ── System ──

    @router.get("/status")
    async def system_status() -> dict[str, Any]:
        return {
            "agent_running": orchestrator.is_running,
            "current_task": orchestrator.current_task_id,
            "browser_human_control": browser.is_human_controlled,
            "stream_clients": stream_manager.client_count,
            "llm_healthy": await llm.health_check(),
        }

    return router
