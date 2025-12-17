import logging
from typing import List

from openai import BadRequestError
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

def handle_context_overflow(
    agent,
    system_prompt: str,
    user_prompt: str,
    history: List[str],
):
    """
    Last-resort recovery when model rejects request.
    """
    logger.warning("Context length exceeded — resetting history")

    history.clear()

    trimmed_prompt = trim_to_tokens(user_prompt, 2000)

    return agent.run_sync(
        trimmed_prompt,
        system_prompt=system_prompt,
    )

def run_agent_safe(
    agent,
    system_prompt: str,
    user_prompt: str,
    history: List[str],
):
    """
    Runs the agent safely with:
    - token pre-check
    - context trimming
    - overflow recovery
    """

    history[:] = ensure_context_within_limit(
        system_prompt,
        user_prompt,
        history,
    )

    try:
        result = agent.run_agent_with_logging(
            user_prompt,
            system_prompt=system_prompt,
        )
        history.append(user_prompt)
        history.append(str(result))
        return result

    except BadRequestError as e:
        if "context length" in str(e).lower():
            return handle_context_overflow(
                agent,
                system_prompt,
                user_prompt,
                history,
            )
        raise

