import logging
from typing import List

from openai import BadRequestError
from pydantic_ai.messages import ModelMessage
import tiktoken

logger = logging.getLogger(__name__)

MODEL_NAME = "gpt-4o"
MODEL_CONTEXT_LIMIT = 128_000
SAFETY_MARGIN = 0.8  # 80%

encoder = tiktoken.encoding_for_model(MODEL_NAME)


def count_tokens(text: str) -> int:
    return len(encoder.encode(text))


def trim_to_tokens(text: str, max_tokens: int) -> str:
    tokens = encoder.encode(text)
    return encoder.decode(tokens[:max_tokens])


def summarize_context(
    history: List[str],
    max_tokens: int = 2000,
) -> str:
    """
    Reduce conversation/tool history to a compact form.
    Keeps the most recent content.
    """
    combined = "\n\n".join(history)
    return trim_to_tokens(combined, max_tokens)


def ensure_context_within_limit(
    system_prompt: str,
    user_prompt: str,
    history: List[str],
) -> List[str]:
    """
    Trims history if token budget is close to the limit.
    """
    total_tokens = (
        count_tokens(system_prompt)
        + count_tokens(user_prompt)
        + sum(count_tokens(h) for h in history)
    )

    max_allowed = int(MODEL_CONTEXT_LIMIT * SAFETY_MARGIN)

    if total_tokens <= max_allowed:
        return history

    logger.warning(
        "Context too large (%d tokens), summarizing history",
        total_tokens,
    )

    return [summarize_context(history)]

async def handle_context_overflow_runner(
    runner,
    messages: list[ModelMessage],
):
    logging.warning("Context length exceeded — retrying with reduced context")

    # Reduce to a summarized system message
    reduced_messages = summarize_context(messages)

    # Runner expects messages to already be in the interface
    runner.chat_interface.messages = reduced_messages

    return await runner.run()


