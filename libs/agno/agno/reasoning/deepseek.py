from __future__ import annotations

from typing import List, Optional

from agno.models.base import Model
from agno.models.message import Message
from agno.utils.log import logger


def get_deepseek_reasoning_agent(reasoning_model: Model, monitoring: bool = False) -> "Agent":  # type: ignore  # noqa: F821
    from agno.agent import Agent

    return Agent(model=reasoning_model, monitoring=monitoring)


def get_deepseek_reasoning(reasoning_agent: "Agent", messages: List[Message]) -> Optional[Message]:  # type: ignore  # noqa: F821
    from agno.run.response import RunResponse

    try:
        reasoning_agent_response: RunResponse = reasoning_agent.run(messages=messages)
    except Exception as e:
        logger.warning(f"Reasoning error: {e}")
        return None

    extracted_reasoning: str = ""
    if reasoning_agent_response.messages is not None:
        for msg in reasoning_agent_response.messages:
            if msg.reasoning_content is not None:
                extracted_reasoning = msg.reasoning_content
                break

    return Message(
        role="assistant", content=f"<thinking>{extracted_reasoning}</thinking>", reasoning_content=extracted_reasoning
    )


async def aget_deepseek_reasoning(reasoning_agent: "Agent", messages: List[Message]) -> Optional[Message]:  # type: ignore  # noqa: F821
    from agno.run.response import RunResponse

    try:
        reasoning_agent_response: RunResponse = await reasoning_agent.arun(messages=messages)
    except Exception as e:
        logger.warning(f"Reasoning error: {e}")
        return None

    extracted_reasoning: str = ""
    if reasoning_agent_response.messages is not None:
        for msg in reasoning_agent_response.messages:
            if msg.reasoning_content is not None:
                extracted_reasoning = msg.reasoning_content
                break

    return Message(
        role="assistant", content=f"<thinking>{extracted_reasoning}</thinking>", reasoning_content=extracted_reasoning
    )
