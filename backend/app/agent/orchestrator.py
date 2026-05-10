"""Main agent orchestrator — coordinates LLM, browser, and desktop to execute tasks."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.agent.planner import Planner
from app.agent.task_manager import TaskManager, TaskStatus
from app.browser.controller import BrowserController
from app.llm.ollama_client import OllamaClient
from app.llm.prompts import ACTION_DECISION_PROMPT

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Runs the agent loop: plan → observe → decide → act → repeat."""

    def __init__(
        self,
        llm: OllamaClient,
        browser: BrowserController,
        task_manager: TaskManager,
    ) -> None:
        self._llm = llm
        self._browser = browser
        self._task_manager = task_manager
        self._planner = Planner(llm)
        self._running = False
        self._current_task_id: str | None = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def current_task_id(self) -> str | None:
        return self._current_task_id

    async def start(self) -> None:
        self._running = True
        logger.info("Agent orchestrator started")
        asyncio.create_task(self._process_loop())

    async def stop(self) -> None:
        self._running = False
        logger.info("Agent orchestrator stopped")

    async def _process_loop(self) -> None:
        while self._running:
            try:
                task_id = await asyncio.wait_for(self._task_manager.next_task_id(), timeout=1.0)
                await self._execute_task(task_id)
            except asyncio.TimeoutError:
                continue
            except Exception:
                logger.exception("Error in agent process loop")
                await asyncio.sleep(1)

    async def _execute_task(self, task_id: str) -> None:
        self._current_task_id = task_id
        task = self._task_manager.get_task(task_id)
        if not task:
            return

        try:
            await self._task_manager.start_task(task_id)

            plan = await self._planner.plan(task.command)
            logger.info("Plan for task %s: %s", task_id, plan)

            for step_def in plan.steps:
                action = step_def.get("action", "unknown")
                description = step_def.get("description", "")

                step = await self._task_manager.add_step(task_id, action, description)
                await self._task_manager.update_step(task_id, step.id, TaskStatus.RUNNING)

                try:
                    result = await self._execute_step(action, step_def)
                    await self._task_manager.update_step(
                        task_id, step.id, TaskStatus.COMPLETED, result=result
                    )
                except HumanInterventionRequired as e:
                    await self._task_manager.request_human_input(task_id, str(e))
                    await self._wait_for_human_input(task_id)
                    await self._task_manager.update_step(
                        task_id,
                        step.id,
                        TaskStatus.COMPLETED,
                        result={"note": "Completed after human intervention"},
                    )
                except Exception as e:
                    logger.error("Step %s failed: %s", step.id, e)
                    await self._task_manager.update_step(
                        task_id, step.id, TaskStatus.FAILED, error=str(e)
                    )
                    raise

            await self._task_manager.complete_task(
                task_id, result={"message": "Task completed successfully"}
            )

        except Exception as e:
            logger.error("Task %s failed: %s", task_id, e)
            await self._task_manager.fail_task(task_id, str(e))
        finally:
            self._current_task_id = None

    async def _execute_step(self, action: str, step_def: dict[str, Any]) -> dict[str, Any]:
        handlers: dict[str, Any] = {
            "navigate": self._handle_navigate,
            "click": self._handle_click,
            "type": self._handle_type,
            "screenshot": self._handle_screenshot,
            "scroll": self._handle_scroll,
            "execute": self._handle_execute,
            "wait": self._handle_wait,
            "extract": self._handle_extract,
        }

        handler = handlers.get(action, self._handle_generic)
        return await handler(step_def)

    async def _handle_navigate(self, step: dict[str, Any]) -> dict[str, Any]:
        url = step.get("url", step.get("target", ""))
        await self._browser.navigate(url)
        return {"url": url, "title": await self._browser.get_title()}

    async def _handle_click(self, step: dict[str, Any]) -> dict[str, Any]:
        selector = step.get("selector", step.get("target", ""))
        await self._browser.click(selector)
        return {"clicked": selector}

    async def _handle_type(self, step: dict[str, Any]) -> dict[str, Any]:
        selector = step.get("selector", step.get("target", ""))
        text = step.get("text", step.get("value", ""))
        await self._browser.type_text(selector, text)
        return {"typed": text, "into": selector}

    async def _handle_screenshot(self, step: dict[str, Any]) -> dict[str, Any]:
        path = await self._browser.screenshot()
        return {"screenshot_path": path}

    async def _handle_scroll(self, step: dict[str, Any]) -> dict[str, Any]:
        direction = step.get("direction", "down")
        amount = int(step.get("amount", 300))
        await self._browser.scroll(direction, amount)
        return {"scrolled": direction, "amount": amount}

    async def _handle_extract(self, step: dict[str, Any]) -> dict[str, Any]:
        selector = step.get("selector", "body")
        content = await self._browser.extract_text(selector)
        return {"content": content[:2000]}

    async def _handle_wait(self, step: dict[str, Any]) -> dict[str, Any]:
        seconds = float(step.get("seconds", step.get("duration", 2)))
        await asyncio.sleep(seconds)
        return {"waited": seconds}

    async def _handle_execute(self, step: dict[str, Any]) -> dict[str, Any]:
        description = step.get("description", "")
        dom = await self._browser.get_dom_snapshot()
        screenshot_path = await self._browser.screenshot()

        prompt = ACTION_DECISION_PROMPT.format(
            task=description,
            dom_summary=dom[:4000],
            screenshot_path=screenshot_path,
        )
        decision = await self._llm.generate(prompt)
        return {"llm_decision": decision[:500], "dom_length": len(dom)}

    async def _handle_generic(self, step: dict[str, Any]) -> dict[str, Any]:
        return {"action": step.get("action", "unknown"), "status": "no handler"}

    async def _wait_for_human_input(self, task_id: str, timeout: float = 300) -> None:
        task = self._task_manager.get_task(task_id)
        if not task:
            return
        deadline = asyncio.get_event_loop().time() + timeout
        while task.status == TaskStatus.WAITING_HUMAN:
            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError("Human intervention timed out")
            await asyncio.sleep(1)
            task = self._task_manager.get_task(task_id)
            if not task:
                return


class HumanInterventionRequired(Exception):
    """Raised when the agent detects a CAPTCHA, 2FA, or other human-required action."""
