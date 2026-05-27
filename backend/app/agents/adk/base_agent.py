from __future__ import annotations

import json
import logging
from collections.abc import AsyncGenerator
from typing import Callable, Optional

from pydantic import PrivateAttr

from app.agents.base_agent import AgentStepResult as GrantOpsStepResult

logger = logging.getLogger(__name__)

STEP_STATE_KEY = "_grant_ops_adk_steps_"

try:
    from google.adk.agents.base_agent import BaseAgent as AdkBaseAgent
    from google.adk.agents.invocation_context import InvocationContext
    from google.adk.agents.sequential_agent import SequentialAgent
    from google.adk.events.event import Event
    from google.adk.utils.context_utils import Aclosing
    from google.genai import types

    ADK_AVAILABLE = True

    class GrantOpsAdkStepAgent(AdkBaseAgent):
        """Minimal ADK agent: runs one GrantOps pipeline step deterministically."""

        description: str = ""

        _grantops_runner: Callable[[], GrantOpsStepResult] = PrivateAttr()

        def __init__(
            self,
            *,
            name: str,
            description: str,
            runner: Callable[[], GrantOpsStepResult],
        ) -> None:
            super().__init__(name=name, description=description)
            object.__setattr__(self, "_grantops_runner", runner)

        async def _run_async_impl(  # type: ignore[override]
            self,
            ctx: InvocationContext,
        ) -> AsyncGenerator[Event, None]:
            result = self._grantops_runner()

            serialized = {
                "step": result.step,
                "status": result.status,
                "message": result.message,
                "data": result.data,
            }
            bucket = ctx.session.state.setdefault(STEP_STATE_KEY, [])
            bucket.append(serialized)

            payload = json.dumps(serialized, default=str)
            preview = payload if len(payload) <= 8000 else payload[:8000] + "…"

            yield Event(
                author=self.name,
                invocation_id=ctx.invocation_id,
                branch=ctx.branch,
                content=types.Content(
                    role="model",
                    parts=[types.Part(text=preview)],
                ),
            )

            if result.status == "failed":
                ctx.end_invocation = True

    class GrantOpsStoppingSequentialAgent(SequentialAgent):
        """Runs sub-agents in order; respects ctx.end_invocation between steps."""

        async def _run_async_impl(  # type: ignore[override]
            self,
            ctx: InvocationContext,
        ) -> AsyncGenerator[Event, None]:
            if not self.sub_agents:
                return

            for sub_agent in self.sub_agents:
                if ctx.end_invocation:
                    return
                async with Aclosing(sub_agent.run_async(ctx)) as agen:
                    async for event in agen:
                        yield event
                if ctx.end_invocation:
                    return

except ImportError:  # pragma: no cover - optional dependency
    ADK_AVAILABLE = False
    GrantOpsAdkStepAgent = None  # type: ignore[misc, assignment]
    GrantOpsStoppingSequentialAgent = None  # type: ignore[misc, assignment]
    InvocationContext = None  # type: ignore[misc, assignment]
    Event = None  # type: ignore[misc, assignment]


class GrantOpsAdkStepUnavailableError(RuntimeError):
    """Raised when USE_ADK_ORCHESTRATOR is true but google-adk cannot be imported."""


def make_step_agent(
    name: str,
    description: str,
    runner: Callable[[], GrantOpsStepResult],
) -> Optional["GrantOpsAdkStepAgent"]:
    if not ADK_AVAILABLE or GrantOpsAdkStepAgent is None:
        return None
    return GrantOpsAdkStepAgent(name=name, description=description, runner=runner)
