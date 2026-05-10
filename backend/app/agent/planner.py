"""Task planner that decomposes user commands into executable steps using the LLM."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.llm.ollama_client import OllamaClient
from app.llm.prompts import PLANNING_PROMPT

logger = logging.getLogger(__name__)


class TaskPlan:
    """A sequence of steps the agent should execute."""

    def __init__(self, steps: list[dict[str, str]], reasoning: str = "") -> None:
        self.steps = steps
        self.reasoning = reasoning

    def __repr__(self) -> str:
        return f"TaskPlan(steps={len(self.steps)}, reasoning={self.reasoning[:60]}...)"


class Planner:
    """Uses the LLM to break a user command into actionable browser/desktop steps."""

    def __init__(self, llm: OllamaClient) -> None:
        self._llm = llm

    async def plan(self, command: str, context: dict[str, Any] | None = None) -> TaskPlan:
        context_str = json.dumps(context) if context else "{}"
        prompt = PLANNING_PROMPT.format(command=command, context=context_str)

        response = await self._llm.generate(prompt)

        try:
            parsed = self._parse_plan(response)
            return parsed
        except Exception:
            logger.warning("Failed to parse structured plan, using fallback")
            return TaskPlan(
                steps=[{"action": "execute", "description": command}],
                reasoning="Fallback: could not decompose command",
            )

    def _parse_plan(self, llm_response: str) -> TaskPlan:
        cleaned = llm_response.strip()

        json_start = cleaned.find("[")
        json_end = cleaned.rfind("]") + 1

        if json_start >= 0 and json_end > json_start:
            json_str = cleaned[json_start:json_end]
            steps = json.loads(json_str)
        else:
            json_start = cleaned.find("{")
            json_end = cleaned.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(cleaned[json_start:json_end])
                steps = data.get("steps", [data])
            else:
                raise ValueError("No JSON found in LLM response")

        reasoning_marker = "reasoning:"
        reasoning_idx = cleaned.lower().find(reasoning_marker)
        reasoning = ""
        if reasoning_idx >= 0:
            reasoning = cleaned[reasoning_idx + len(reasoning_marker) :].split("\n")[0].strip()

        return TaskPlan(steps=steps, reasoning=reasoning)
