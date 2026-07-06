"""
Author: L. Saetta
Date last modified: 2026-07-06
License: MIT
Description: Reusable A2A AgentExecutor adapter for streaming LangGraph agents.
Agent customization: Do not modify unless the A2A event mapping changes.
"""

from __future__ import annotations

from a2a import types as a2a_types
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from oci_langgraph_a2a_blueprint.a2a_contract import AgentFactory


class LangGraphAgentExecutor(AgentExecutor):
    """Bridge a streaming LangGraph agent to the A2A SDK executor interface.

    Args:
        agent_factory: Factory that creates one streaming agent per request.
        final_output_key: State key used to read the final artifact text.
    """

    def __init__(
        self,
        agent_factory: AgentFactory,
        final_output_key: str = "final_output",
    ) -> None:
        self.agent_factory = agent_factory
        self.final_output_key = final_output_key

    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Execute the streaming LangGraph agent and publish A2A task updates.

        Args:
            context: A2A request context.
            event_queue: Queue used by the SDK to stream task events.
        """
        updater = self._create_task_updater(context, event_queue)

        try:
            await event_queue.enqueue_event(
                a2a_types.Task(
                    id=updater.task_id,
                    context_id=updater.context_id,
                    status=a2a_types.TaskStatus(
                        state=a2a_types.TaskState.TASK_STATE_SUBMITTED,
                        message=self._new_agent_message(
                            updater,
                            "Task submitted.",
                        ),
                    ),
                )
            )
            await updater.start_work(
                self._new_agent_message(updater, "LangGraph workflow started.")
            )

            final_output = ""
            agent = self.agent_factory()
            async for event in agent.stream(context.get_user_input()):
                if event.event_type == "step_completed":
                    await updater.update_status(
                        a2a_types.TaskState.TASK_STATE_WORKING,
                        message=self._new_agent_message(updater, event.message),
                        metadata={
                            "langgraph_event_type": event.event_type,
                            "langgraph_step_name": event.step_name,
                        },
                    )
                elif event.event_type == "agent_completed":
                    final_output = event.state.get(self.final_output_key, "")

            await updater.add_artifact(
                parts=[a2a_types.Part(text=final_output)],
                name="final_output",
                last_chunk=True,
                metadata={"artifact_type": "final_output"},
            )
            await updater.complete(
                self._new_agent_message(updater, "LangGraph workflow completed.")
            )
        except ValueError as exc:
            await updater.failed(self._new_agent_message(updater, str(exc)))

    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Cancel an active task.

        Args:
            context: A2A request context.
            event_queue: Queue used by the SDK to stream task events.
        """
        updater = self._create_task_updater(context, event_queue)
        await updater.cancel(self._new_agent_message(updater, "Task cancelled."))

    @staticmethod
    def _create_task_updater(
        context: RequestContext,
        event_queue: EventQueue,
    ) -> TaskUpdater:
        """Create the SDK task updater for the current request.

        Args:
            context: A2A request context.
            event_queue: Queue used by the SDK to stream task events.

        Returns:
            Configured task updater.

        Raises:
            ValueError: If the SDK context does not contain task identifiers.
        """
        if context.task_id is None or context.context_id is None:
            raise ValueError("A2A task_id and context_id are required")

        return TaskUpdater(
            event_queue=event_queue,
            task_id=context.task_id,
            context_id=context.context_id,
        )

    @staticmethod
    def _new_agent_message(updater: TaskUpdater, text: str) -> a2a_types.Message:
        """Create an A2A agent message with one text part.

        Args:
            updater: Task updater that owns task and context identifiers.
            text: Message text.

        Returns:
            A2A agent message.
        """
        return updater.new_agent_message(parts=[a2a_types.Part(text=text)])
