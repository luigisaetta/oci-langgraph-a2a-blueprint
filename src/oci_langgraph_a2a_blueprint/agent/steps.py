"""
Author: L. Saetta
Date last modified: 2026-07-07
License: MIT
Description: LangChain Runnable step definitions for the sample LangGraph agent.
Agent customization: Modify only when changing the sample step workflow.
"""

# pylint: disable=redefined-builtin

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig

from oci_langgraph_a2a_blueprint.agent.llm_client import LlmResponder
from oci_langgraph_a2a_blueprint.agent.state import AgentState

LOGGER = logging.getLogger(__name__)


class BaseStep(Runnable[AgentState, AgentState]):
    """Base runnable for one blueprint workflow step.

    Args:
        name: Step name used in the LangGraph node.
        sleep_seconds: Simulated work duration.
        logger: Logger used for start and completion messages.
    """

    def __init__(
        self,
        name: str,
        sleep_seconds: float,
        logger: logging.Logger | None = None,
    ) -> None:
        self.name = name
        self.sleep_seconds = sleep_seconds
        self.logger = logger or LOGGER

    def invoke(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """Run the concrete step.

        Args:
            input: Current shared agent state.
            config: Optional LangChain runnable configuration.
            **kwargs: Additional runnable invocation arguments.

        Returns:
            Partial state update produced by this step.

        Raises:
            NotImplementedError: Always raised by the base class.
        """
        raise NotImplementedError  # pragma: no cover

    def _simulate_work(self) -> None:
        """Log start, sleep, and leave completion logging to the concrete step."""
        self.logger.info("%s started", self.name)
        time.sleep(self.sleep_seconds)

    def _log_completed(self) -> None:
        """Log the step completion message."""
        self.logger.info("%s completed", self.name)


class Step1(BaseStep):
    """First blueprint step.

    Args:
        sleep_seconds: Simulated work duration.
    """

    def __init__(self, sleep_seconds: float) -> None:
        super().__init__(name="step1", sleep_seconds=sleep_seconds)

    def invoke(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """Produce `state1` from the original input text.

        Args:
            input: Current shared agent state.
            config: Optional LangChain runnable configuration.
            **kwargs: Additional runnable invocation arguments.

        Returns:
            Partial state update containing `state1` and progress.
        """
        self._simulate_work()
        output = f"step1 processed: {input['input_text']}"
        self._log_completed()
        return {"state1": output, "progress": ["step1 completed"]}


class Step2(BaseStep):
    """Second blueprint step backed by an LLM call.

    Args:
        sleep_seconds: Simulated work duration.
        llm_client: Responder that calls the configured LLM.
    """

    def __init__(self, sleep_seconds: float, llm_client: LlmResponder) -> None:
        super().__init__(name="step2", sleep_seconds=sleep_seconds)
        self.llm_client = llm_client

    def invoke(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """Produce `state2` by sending the original input to the LLM.

        Args:
            input: Current shared agent state.
            config: Optional LangChain runnable configuration.
            **kwargs: Additional runnable invocation arguments.

        Returns:
            Partial state update containing `state2` and progress.
        """
        self._simulate_work()
        output = self.llm_client.answer(input["input_text"])
        self._log_completed()
        return {"state2": output, "progress": ["step2 completed"]}


class Step3(BaseStep):
    """Third blueprint step.

    Args:
        sleep_seconds: Simulated work duration.
    """

    def __init__(self, sleep_seconds: float) -> None:
        super().__init__(name="step3", sleep_seconds=sleep_seconds)

    def invoke(
        self,
        input: AgentState,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> AgentState:
        """Produce `state3` and the final output from `state2`.

        Args:
            input: Current shared agent state.
            config: Optional LangChain runnable configuration.
            **kwargs: Additional runnable invocation arguments.

        Returns:
            Partial state update containing `state3`, `final_output`, and progress.
        """
        self._simulate_work()
        output = f"step3 processed: {input['state2']}"
        self._log_completed()
        return {
            "state3": output,
            "final_output": output,
            "progress": ["step3 completed"],
        }


def create_default_steps(
    step_sleep_seconds: float = 1.0,
    llm_client: LlmResponder | None = None,
) -> list[BaseStep]:
    """Create the default three-step blueprint workflow.

    Args:
        step_sleep_seconds: Simulated work duration for each step.
        llm_client: Responder used by `step2` to call the configured LLM.

    Returns:
        Ordered runnable steps for `step1`, `step2`, and `step3`.

    Raises:
        ValueError: If `step_sleep_seconds` is negative.
    """
    if step_sleep_seconds < 0:
        raise ValueError("step_sleep_seconds must be greater than or equal to 0")
    if llm_client is None:
        raise ValueError("llm_client is required")

    return [
        Step1(step_sleep_seconds),
        Step2(step_sleep_seconds, llm_client=llm_client),
        Step3(step_sleep_seconds),
    ]
