"""
NEXA Agent Planner — Analyzes intent and creates execution plans.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from loguru import logger

from app.ai.base import LLMMessage, LLMProvider


PLANNING_SYSTEM_PROMPT = """You are NEXA, an AI agent planner. Your job is to analyze the user's goal and create a detailed execution plan.

You have access to these tools:
{tool_descriptions}

Given a user's goal, create a step-by-step plan. Each step should specify:
1. A clear description of what to do
2. Which tool to use (from the available tools)
3. The parameters needed for the tool

Important rules:
- Break complex goals into simple, atomic steps
- For movie, software, or file downloading (e.g. "download karuppu", "download <movie>", "download <file>"), ALWAYS use `browser.download` directly with the item query and quality parameters (e.g. tool_name: "browser.download", parameters: {{"query": "karuppu", "file_type": "movie", "quality": "720p"}}). This will automatically open Chrome, navigate directly to https://www.moviesda.studio/, search for the movie, check video quality options (480p, 720p, 1080p), and initiate download to the device.
- For web or YouTube searches, ALWAYS use `browser.search` or `app.launch` directly with the exact query text in parameters (e.g., tool_name: "browser.search", parameters: {{"query": "DSA in Tamil", "site": "youtube.com"}} or tool_name: "app.launch", parameters: {{"name": "chrome", "args": "DSA in Tamil"}}). Never omit the user's search query terms!
- Always preserve the exact full query requested by the user (including language or topic modifiers like "in Tamil").
- Use the most specific tool available for each step
- Be practical - don't add unnecessary steps

{memory_context}
"""


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "understanding": {
            "type": "string",
            "description": "Brief summary of what the user wants"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "description": {"type": "string"},
                    "tool_name": {"type": "string"},
                    "parameters": {"type": "object"},
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Indices of steps this depends on"
                    },
                    "verification": {
                        "type": "string",
                        "description": "How to verify this step succeeded"
                    }
                },
                "required": ["index", "description", "tool_name", "parameters"]
            }
        },
        "estimated_risk": {
            "type": "string",
            "enum": ["low", "medium", "high"]
        }
    },
    "required": ["understanding", "steps"]
}


class Planner:
    """
    Analyzes user goals and creates structured execution plans.
    Uses the LLM to decompose natural language goals into tool-based steps.
    """

    def __init__(self, llm: LLMProvider, tool_descriptions: str = ""):
        self._llm = llm
        self._tool_descriptions = tool_descriptions

    def update_tool_descriptions(self, descriptions: str):
        """Update available tool descriptions."""
        self._tool_descriptions = descriptions

    async def analyze_intent(self, user_input: str) -> dict[str, Any]:
        """
        Analyze the user's intent from natural language input.
        Returns a structured understanding of what the user wants.
        """
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are NEXA, an AI assistant. Analyze the user's request "
                    "and determine their intent. Respond with JSON containing: "
                    '"intent" (brief description), "category" (one of: search, '
                    'create, modify, delete, navigate, analyze, automate, query), '
                    '"complexity" (simple, moderate, complex), '
                    '"requires_confirmation" (boolean).'
                ),
            ),
            LLMMessage(role="user", content=user_input),
        ]

        result = await self._llm.complete_structured(
            messages=messages,
            response_schema={
                "type": "object",
                "properties": {
                    "intent": {"type": "string"},
                    "category": {"type": "string"},
                    "complexity": {"type": "string"},
                    "requires_confirmation": {"type": "boolean"},
                },
                "required": ["intent", "category", "complexity"],
            },
            temperature=0.3,
        )

        logger.info(f"Intent analysis: {result}")
        return result

    async def create_plan(
        self,
        goal: str,
        context: str = "",
        memory_context: str = "",
    ) -> dict[str, Any]:
        """
        Create an execution plan for a user goal.
        
        Args:
            goal: The user's natural language goal
            context: Additional context (previous results, observations)
            memory_context: User preferences and task history
            
        Returns:
            Structured plan with steps, tools, and parameters
        """
        system_prompt = PLANNING_SYSTEM_PROMPT.format(
            tool_descriptions=self._tool_descriptions or "No tools loaded yet.",
            memory_context=(
                f"\nUser context: {memory_context}" if memory_context else ""
            ),
        )

        user_content = goal
        if context:
            user_content += f"\n\nAdditional context:\n{context}"

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]

        plan = await self._llm.complete_structured(
            messages=messages,
            response_schema=PLAN_SCHEMA,
            temperature=0.3,
        )

        logger.info(
            f"Created plan with {len(plan.get('steps', []))} steps "
            f"for goal: {goal[:80]}"
        )

        return plan

    async def replan(
        self,
        original_goal: str,
        completed_steps: list[dict],
        failed_step: dict,
        error: str,
        context: str = "",
    ) -> dict[str, Any]:
        """
        Create a revised plan after a step failure.
        
        The agent calls this when a step fails and needs an alternative approach.
        """
        system_prompt = PLANNING_SYSTEM_PROMPT.format(
            tool_descriptions=self._tool_descriptions or "No tools loaded yet.",
            memory_context="",
        )

        user_content = (
            f"Original goal: {original_goal}\n\n"
            f"Completed steps so far:\n"
            f"{json.dumps(completed_steps, indent=2)}\n\n"
            f"Failed step:\n{json.dumps(failed_step, indent=2)}\n\n"
            f"Error: {error}\n\n"
            f"Please create a revised plan to achieve the original goal, "
            f"taking into account what has already been done and the error. "
            f"Find an alternative approach for the failed step."
        )
        if context:
            user_content += f"\n\nAdditional context:\n{context}"

        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_content),
        ]

        plan = await self._llm.complete_structured(
            messages=messages,
            response_schema=PLAN_SCHEMA,
            temperature=0.4,
        )

        logger.info(f"Created revised plan with {len(plan.get('steps', []))} steps")
        return plan
