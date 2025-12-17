from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai import AgentRunResult
from capstone_project.main import run_agent
from tests.utils import get_tool_calls
import pytest
from capstone_project.agents import SearchResultSummary

judge_instructions = """
you are an expert judge evaluating the performance of an AI search agent.
"""

class JudgeCriterion(BaseModel):
    criterion_description: str
    passed: bool
    judgement: str


class JudgeFeedback(BaseModel):
    criteria: list[JudgeCriterion]
    feedback: str


def create_judge():
    judge = Agent(
        name="judge",
        instructions=judge_instructions,
        model="openai:gpt-4o-mini",
        output_type=JudgeFeedback,
    )
    return judge


async def evaluate_agent_performance(
        criteria: list[str],
        result: AgentRunResult,
        output_transformer: callable = None
) -> JudgeFeedback:
    judge = create_judge()

    tool_calls = get_tool_calls(result)

    output = result.output
    if output_transformer is not None:
        output = output_transformer(output)

    user_prompt = f"""
Evaluate the agent's performance based on the following criteria:
<CRITERIA>
{'\n'.join(criteria)}
</CRITERIA>

The agent's final output was:
<AGENT_OUTPUT>
{output}
</AGENT_OUTPUT>

Tool calls:
<TOOL_CALLS>
{'\n'.join([str(c) for c in tool_calls])}
</TOOL_CALLS>
    """

    print("Judge evaluating with prompt:")
    print("-----")
    print(user_prompt)
    print("-----")

    eval_results = await judge.run(
        user_prompt=user_prompt
    )

    return eval_results.output


@pytest.mark.asyncio
async def test_no_judicial_terms_in_search_queries():
    criteria = [
        "agent makes at least 1 search call",
        "agent makes a search_Quality_check call after every search call"
        "there are at least 3 references provided"
        "the references are appropriate and relevant to the topic",
        "the summary contains broader introduction before describing finer details",
    ]

    result = await run_agent("recent research in transformer models")

    eval_results = await evaluate_agent_performance(
        criteria,
        result,
        output_transformer=lambda x: x.format_article()
    )

    print(eval_results)

    for criterion in eval_results.criteria:
        print(criterion)
        assert criterion.passed, f"Criterion failed: {criterion.criterion_description}"