"""Task queue and lifecycle management for agent jobs."""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_HUMAN = "waiting_human"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStep(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    action: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    command: str
    status: TaskStatus = TaskStatus.PENDING
    steps: list[TaskStep] = Field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskManager:
    """Manages task lifecycle: creation, queuing, execution tracking."""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._listeners: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}

    async def create_task(self, command: str, metadata: dict[str, Any] | None = None) -> Task:
        task = Task(command=command, metadata=metadata or {})
        self._tasks[task.id] = task
        await self._queue.put(task.id)
        await self._notify(task.id, {"event": "task_created", "task_id": task.id})
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_tasks(self, status: TaskStatus | None = None, limit: int = 50) -> list[Task]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)[:limit]

    async def start_task(self, task_id: str) -> Task:
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now(timezone.utc)
        await self._notify(task_id, {"event": "task_started", "task_id": task_id})
        return task

    async def add_step(self, task_id: str, action: str, description: str) -> TaskStep:
        task = self._tasks[task_id]
        step = TaskStep(action=action, description=description)
        task.steps.append(step)
        await self._notify(
            task_id,
            {"event": "step_added", "task_id": task_id, "step_id": step.id, "action": action},
        )
        return step

    async def update_step(
        self,
        task_id: str,
        step_id: str,
        status: TaskStatus,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> TaskStep:
        task = self._tasks[task_id]
        for step in task.steps:
            if step.id == step_id:
                step.status = status
                step.result = result
                step.error = error
                if status == TaskStatus.RUNNING:
                    step.started_at = datetime.now(timezone.utc)
                elif status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                    step.completed_at = datetime.now(timezone.utc)
                await self._notify(
                    task_id,
                    {
                        "event": "step_updated",
                        "task_id": task_id,
                        "step_id": step_id,
                        "status": status.value,
                    },
                )
                return step
        raise ValueError(f"Step {step_id} not found in task {task_id}")

    async def complete_task(self, task_id: str, result: dict[str, Any] | None = None) -> Task:
        task = self._tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.now(timezone.utc)
        await self._notify(task_id, {"event": "task_completed", "task_id": task_id})
        return task

    async def fail_task(self, task_id: str, error: str) -> Task:
        task = self._tasks[task_id]
        task.status = TaskStatus.FAILED
        task.error = error
        task.completed_at = datetime.now(timezone.utc)
        await self._notify(task_id, {"event": "task_failed", "task_id": task_id, "error": error})
        return task

    async def request_human_input(self, task_id: str, prompt: str) -> None:
        task = self._tasks[task_id]
        task.status = TaskStatus.WAITING_HUMAN
        await self._notify(
            task_id,
            {"event": "human_input_required", "task_id": task_id, "prompt": prompt},
        )

    async def provide_human_input(self, task_id: str, input_data: dict[str, Any]) -> None:
        task = self._tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.metadata["human_input"] = input_data
        await self._notify(
            task_id,
            {"event": "human_input_provided", "task_id": task_id},
        )

    async def next_task_id(self) -> str:
        return await self._queue.get()

    def subscribe(self, task_id: str) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._listeners.setdefault(task_id, []).append(q)
        return q

    def unsubscribe(self, task_id: str, q: asyncio.Queue[dict[str, Any]]) -> None:
        listeners = self._listeners.get(task_id, [])
        if q in listeners:
            listeners.remove(q)

    async def _notify(self, task_id: str, event: dict[str, Any]) -> None:
        for q in self._listeners.get(task_id, []):
            await q.put(event)
