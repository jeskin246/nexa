"""
NEXA Agent Loop — The core agent execution loop.

This is the brain of NEXA. It orchestrates:
Goal → Analyze → Plan → Execute → Observe → Verify → Adapt → Complete
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Awaitable, Optional

from loguru import logger

from app.agent.executor import Executor
from app.agent.observer import Observer
from app.agent.planner import Planner
from app.agent.recovery import RecoveryManager
from app.agent.verifier import Verifier
from app.ai.base import LLMMessage, LLMProvider
from app.api.models import AgentState, StepStatus, TaskStep
from app.memory.manager import MemoryManager
from app.security.emergency import EmergencyStop
from app.tools.registry import ToolRegistry


# Type for the status callback
StatusCallback = Callable[[dict[str, Any]], Awaitable[None]]


class AgentLoop:
    """
    The core agent loop that processes user goals end-to-end.
    
    Flow:
    1. Receive user goal
    2. Analyze intent
    3. Create execution plan
    4. For each step in the plan:
       a. Select and execute tool
       b. Observe result
       c. Verify outcome
       d. Handle failures (retry/replan/ask user)
    5. Verify overall goal completion
    6. Report result
    """

    def __init__(
        self,
        llm: LLMProvider,
        registry: ToolRegistry,
        executor: Executor,
        planner: Planner,
        observer: Observer,
        verifier: Verifier,
        recovery: RecoveryManager,
        memory: MemoryManager,
        emergency_stop: EmergencyStop,
        max_iterations: int = 20,
    ):
        self._llm = llm
        self._registry = registry
        self._executor = executor
        self._planner = planner
        self._observer = observer
        self._verifier = verifier
        self._recovery = recovery
        self._memory = memory
        self._emergency_stop = emergency_stop
        self._max_iterations = max_iterations

    async def process_goal(
        self,
        goal: str,
        status_callback: StatusCallback,
    ) -> dict[str, Any]:
        """
        Process a user goal through the complete agent loop.
        
        Args:
            goal: Natural language goal from the user
            status_callback: Async callback to send status updates to frontend
            
        Returns:
            Final result dict with success status and data
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"[{task_id}] Processing goal: {goal}")
        
        # Store in memory
        self._memory.add_message("user", goal)
        self._memory.store_task(task_id, {"goal": goal, "status": "started"})

        try:
            # ─── Phase 1: Understanding ─────────────────────────────────
            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": AgentState.THINKING.value,
                "message": "Understanding your request...",
            })

            intent = await self._planner.analyze_intent(goal)
            
            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": AgentState.THINKING.value,
                "message": f"I understand: {intent.get('intent', goal)}",
            })

            # ─── Phase 2: Planning ──────────────────────────────────────
            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": AgentState.PLANNING.value,
                "message": "Creating execution plan...",
            })

            # Update planner with current tool descriptions
            self._planner.update_tool_descriptions(
                self._registry.get_tool_descriptions()
            )

            memory_context = self._memory.get_context_summary()
            plan = await self._planner.create_plan(
                goal=goal,
                memory_context=memory_context,
            )

            if "error" in plan:
                raise Exception(f"Planning failed: {plan.get('error')}")

            steps = plan.get("steps", [])
            if not steps:
                raise Exception("No steps generated in plan")

            # Send plan to frontend
            await status_callback({
                "type": "plan",
                "task_id": task_id,
                "data": {
                    "understanding": plan.get("understanding", ""),
                    "steps": [
                        {
                            "index": s.get("index", i),
                            "description": s.get("description", ""),
                            "tool_name": s.get("tool_name", ""),
                            "status": "pending",
                        }
                        for i, s in enumerate(steps)
                    ],
                    "total_steps": len(steps),
                },
            })

            # ─── Phase 3: Execution Loop ────────────────────────────────
            completed_steps: list[dict[str, Any]] = []
            final_result: Any = None
            context_accumulator = ""

            for step_idx, step in enumerate(steps):
                # Check emergency stop
                if self._emergency_stop.is_task_cancelled(task_id):
                    logger.warning(f"[{task_id}] Task cancelled by emergency stop")
                    await status_callback({
                        "type": "status",
                        "task_id": task_id,
                        "state": AgentState.ERROR.value,
                        "message": "Task stopped by user",
                    })
                    return {
                        "task_id": task_id,
                        "success": False,
                        "error": "Task cancelled",
                        "completed_steps": completed_steps,
                    }

                tool_name = step.get("tool_name", "")
                params = step.get("parameters", {})
                description = step.get("description", f"Step {step_idx + 1}")

                # Update status
                await status_callback({
                    "type": "step_update",
                    "task_id": task_id,
                    "data": {
                        "step_index": step_idx,
                        "status": "in_progress",
                        "description": description,
                        "total_steps": len(steps),
                        "percentage": (step_idx / len(steps)) * 100,
                    },
                })

                await status_callback({
                    "type": "status",
                    "task_id": task_id,
                    "state": AgentState.EXECUTING.value,
                    "message": description,
                })

                # Execute tool
                result = await self._executor.execute(
                    task_id=task_id,
                    tool_name=tool_name,
                    parameters=params,
                )

                # Observe
                await status_callback({
                    "type": "status",
                    "task_id": task_id,
                    "state": AgentState.OBSERVING.value,
                    "message": "Checking result...",
                })

                observations = await self._observer.observe_after_action(
                    tool_name, result
                )

                # Verify
                verification = await self._verifier.verify_step(
                    step_description=description,
                    tool_name=tool_name,
                    result=result,
                    observations=observations,
                )

                step_result = {
                    "index": step_idx,
                    "description": description,
                    "tool_name": tool_name,
                    "success": verification.success,
                    "result": str(result.data)[:500] if result.data else None,
                    "error": result.error,
                }

                if verification.success:
                    # Step succeeded
                    completed_steps.append(step_result)
                    final_result = result.data

                    # Accumulate context for future steps
                    if result.data:
                        context_accumulator += (
                            f"\nStep {step_idx + 1} result: "
                            f"{str(result.data)[:300]}"
                        )

                    await status_callback({
                        "type": "step_update",
                        "task_id": task_id,
                        "data": {
                            "step_index": step_idx,
                            "status": "completed",
                            "description": description,
                            "result": result.message or "Done",
                            "total_steps": len(steps),
                            "percentage": ((step_idx + 1) / len(steps)) * 100,
                        },
                    })
                else:
                    # Step failed — attempt recovery
                    step_key = f"{task_id}_{step_idx}"
                    strategy = self._recovery.determine_strategy(
                        step_key=step_key,
                        tool_name=tool_name,
                        error=result.error or "Unknown error",
                        step_index=step_idx,
                        total_steps=len(steps),
                    )

                    logger.info(
                        f"[{task_id}] Step {step_idx} failed, "
                        f"strategy: {strategy.action}"
                    )

                    if strategy.action == "retry":
                        await self._recovery.apply_wait(strategy)
                        # Re-execute (simple retry)
                        result = await self._executor.execute(
                            task_id=task_id,
                            tool_name=tool_name,
                            parameters=params,
                        )
                        if result.success:
                            step_result["success"] = True
                            step_result["result"] = (
                                str(result.data)[:500] if result.data else None
                            )
                            completed_steps.append(step_result)
                            final_result = result.data
                            await status_callback({
                                "type": "step_update",
                                "task_id": task_id,
                                "data": {
                                    "step_index": step_idx,
                                    "status": "completed",
                                    "description": f"{description} (retry succeeded)",
                                    "total_steps": len(steps),
                                    "percentage": (
                                        (step_idx + 1) / len(steps)
                                    ) * 100,
                                },
                            })
                        else:
                            completed_steps.append(step_result)
                            await status_callback({
                                "type": "step_update",
                                "task_id": task_id,
                                "data": {
                                    "step_index": step_idx,
                                    "status": "failed",
                                    "description": description,
                                    "error": result.error,
                                    "total_steps": len(steps),
                                    "percentage": (
                                        (step_idx + 1) / len(steps)
                                    ) * 100,
                                },
                            })

                    elif strategy.action == "skip":
                        step_result["status"] = "skipped"
                        completed_steps.append(step_result)
                        await status_callback({
                            "type": "step_update",
                            "task_id": task_id,
                            "data": {
                                "step_index": step_idx,
                                "status": "skipped",
                                "description": f"{description} (skipped)",
                                "total_steps": len(steps),
                                "percentage": (
                                    (step_idx + 1) / len(steps)
                                ) * 100,
                            },
                        })

                    elif strategy.action == "abort":
                        completed_steps.append(step_result)
                        await status_callback({
                            "type": "step_update",
                            "task_id": task_id,
                            "data": {
                                "step_index": step_idx,
                                "status": "failed",
                                "description": description,
                                "error": strategy.description,
                                "total_steps": len(steps),
                                "percentage": (
                                    (step_idx + 1) / len(steps)
                                ) * 100,
                            },
                        })
                        break

                    else:
                        # ask_user or unknown — report and continue
                        completed_steps.append(step_result)
                        await status_callback({
                            "type": "step_update",
                            "task_id": task_id,
                            "data": {
                                "step_index": step_idx,
                                "status": "failed",
                                "description": description,
                                "error": result.error,
                                "total_steps": len(steps),
                                "percentage": (
                                    (step_idx + 1) / len(steps)
                                ) * 100,
                            },
                        })

            # ─── Phase 4: Final Verification ────────────────────────────
            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": AgentState.OBSERVING.value,
                "message": "Verifying results...",
            })

            # Generate a summary using the LLM
            summary = await self._generate_summary(
                goal, completed_steps, final_result
            )

            # Mark success
            success = any(s.get("success") for s in completed_steps)
            state = AgentState.SUCCESS if success else AgentState.ERROR

            await status_callback({
                "type": "task_complete",
                "task_id": task_id,
                "data": {
                    "success": success,
                    "summary": summary,
                    "completed_steps": len(
                        [s for s in completed_steps if s.get("success")]
                    ),
                    "total_steps": len(steps),
                    "result": str(final_result)[:1000] if final_result else None,
                },
            })

            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": state.value,
                "message": summary,
            })

            # Update memory
            self._memory.add_message("assistant", summary)
            self._memory.complete_task(task_id, final_result)

            return {
                "task_id": task_id,
                "success": success,
                "summary": summary,
                "completed_steps": completed_steps,
                "result": final_result,
            }

        except Exception as e:
            error_msg = f"Agent error: {str(e)}"
            logger.error(f"[{task_id}] {error_msg}")

            await status_callback({
                "type": "error",
                "task_id": task_id,
                "message": error_msg,
            })

            await status_callback({
                "type": "status",
                "task_id": task_id,
                "state": AgentState.ERROR.value,
                "message": error_msg,
            })

            self._memory.complete_task(task_id, {"error": error_msg})

            return {
                "task_id": task_id,
                "success": False,
                "error": error_msg,
            }

    async def _generate_summary(
        self,
        goal: str,
        completed_steps: list[dict],
        final_result: Any,
    ) -> str:
        """Generate a human-friendly summary of the task execution."""
        try:
            messages = [
                LLMMessage(
                    role="system",
                    content=(
                        "Summarize what was accomplished in 1-2 sentences. "
                        "Be concise and user-friendly."
                    ),
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"Goal: {goal}\n"
                        f"Steps completed: {len(completed_steps)}\n"
                        f"Results: {str(final_result)[:500]}"
                    ),
                ),
            ]
            response = await self._llm.complete(
                messages=messages,
                max_tokens=200,
                temperature=0.5,
            )
            return response.content.strip()
        except Exception:
            successful = sum(
                1 for s in completed_steps if s.get("success")
            )
            return (
                f"Completed {successful}/{len(completed_steps)} steps "
                f"for: {goal[:100]}"
            )
