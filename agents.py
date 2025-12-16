from tools import Agent_Tools
from elasticsearch import Elasticsearch

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic import BaseModel, HttpUrl
from toyaikit.chat.interface import StdOutputInterface
from toyaikit.chat.runners import PydanticAIRunner
import asyncio

class Reference(BaseModel):
    title: str
    url: str


class SearchResultSummary(BaseModel):
    title: str
    summary: str
    references: list[Reference]

    def format_article(self):
        output = f"# {self.title}\n\n"

        output += f"## Summary \n {self.summary} \n\n"
        output += "## References\n"
        for ref in self.references:
            output += f"- [{ref.title}]({ref.url})\n"

        return output

class SearchResultEvaluation(BaseModel):
    title: str
    url: HttpUrl
    relevance: float  # 0.0 to 1.0
    completeness: float  # 0.0 to 1.0
    credibility: float  # 0.0 to 1.0
    currency: float  # 0.0 to 1.0

# Overall evaluation and decision
class SearchEvaluationOutput(BaseModel):
    results_evaluation: List[SearchResultEvaluation]
    overall_quality_score: float  # 0.0 to 1.0
    decision: str  # "Good enough" or "Fetch more data"
    suggested_search_terms: List[str]  # optional if decision is "Fetch more data"


class NamedCallback:

    def __init__(self, agent):
        self.agent_name = agent.name

    async def print_function_calls(self, ctx, event):
        # Detect nested streams
        if hasattr(event, "__aiter__"):
            async for sub in event:
                await self.print_function_calls(ctx, sub)
            return

        if isinstance(event, FunctionToolCallEvent):
            tool_name = event.part.tool_name
            args = event.part.args
            print(f"TOOL CALL ({self.agent_name}): {tool_name}({args})")

    async def __call__(self, ctx, event):
        return await self.print_function_calls(ctx, event)





def create_agents():
    es = Elasticsearch("http://localhost:9200")
    agent_class = Agent_Tools(es_index=es)


    search_quality_check_instructions = f"""
        You are an expert research assistant. You will evaluate the following search results for the query:
        '{query}'

        Search results:
        {search_results}

        For each result, score the following on a scale of 0 to 1:
        - Relevance
        - Completeness
        - Credibility
        - Currency

        Then provide:
        1. An overall quality score (0–1)
        2. Whether the current results are sufficient or if more data should be fetched
        3. If more data is needed, suggest 2–3 alternative search terms to improve coverage

        Provide your response as JSON.
    """.strip()

        search_quality_check_agent = Agent(
        name="search_quality_check",
        instructions=search_quality_check_instructions,
        model='openai:gpt-4o-mini',
        output_type=SearchEvaluationOutput
    )



    # Summarizing agent
    summarizing_instructions = """
        You are a helpful assistant that answers user questions only based on arxiv research articles.

        When a user asks a query, you first search the index to find relevant results. 
        If you cannot find anything relevant, then you fetch the relevant articles from arxiv using the get_data_to_index tool.
        Then you perfrom a search using the search tool again.

        You make sure that the search results you utilize are directly related to the user's query.
        You can do this by calling the search_quality_check_agent.

        You provide a complete and correct answer to the user's question by summarizing all these search results.
        You always provide at least 3 relevant and appropriate references to all artciles you use when summarizing search results.
    """.strip()

    summarizing_tools = [agent_class.get_data_to_index, agent_class.search]

    summarize_agent = Agent(
        name="summarize",
        tools=summarizing_tools,
        instructions=summarizing_instructions,
        model='openai:gpt-4o-mini',
        output_type=SearchResultSummary
    )
    
    @summarize_agent.tool
    async def search_quality_check(ctx: RunContext, query: str):
        """
        Runs the search_quality_check_agent agent to check the quality of search

        and saves the results.

        Args:
            query: raw user request

        Returns:
            SearchEvaluationOutput with a decision to either continue searching or use the available data
        """

        callback = NamedCallback(search_quality_check_agent)
        results = await search_quality_check_agent.run(user_prompt=query, event_stream_handler=callback)
        
        return results.output


    return summarize_agent

