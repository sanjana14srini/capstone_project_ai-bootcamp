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
    
class SearchResultInput(BaseModel):
    title: str
    snippet: str
    url: HttpUrl

class SearchQualityCheckInput(BaseModel):
    user_query: str
    search_results: list[SearchResultInput]

class SearchResultEvaluation(BaseModel):
    title: str
    url: str
    relevance: float  # 0.0 to 1.0
    completeness: float  # 0.0 to 1.0
    credibility: float  # 0.0 to 1.0
    currency: float  # 0.0 to 1.0

# Overall evaluation and decision
class SearchEvaluationOutput(BaseModel):
    results_evaluation: list[SearchResultEvaluation]
    overall_quality_score: float  # 0.0 to 1.0
    decision: str  # "Good enough" or "Fetch more data"
    suggested_search_terms: list[str]  # optional if decision is "Fetch more data"


class Message(BaseModel):
    role: str
    content: str
    latest_query: str

class OrchestratorInput(BaseModel):
    messages: list[Message]


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


    search_quality_check_instructions = """
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
        2. Whether the current results are 'Good enough' or if 'more data is needed'
        3. If more data is needed, suggest 2–3 alternative search terms to improve coverage

        Provide your response as JSON.
    """.strip()

    def format_search_results(results):
        formatted = []
        for res in results:
            formatted.append({
                "title": res.get("title", ""),
                "snippet": res.get("summary", "") or res.get("content", "")[:200],
                "url": res.get("url", "https://example.com")
            })
        return formatted

    search_quality_check_agent = Agent(
        name="search_quality_check",
        instructions=search_quality_check_instructions,
        model='openai:gpt-4o-mini',
        output_type=SearchEvaluationOutput
    )


    # @summarize_agent.tool
    async def search_quality_check(
        ctx: RunContext,
        params: SearchQualityCheckInput | None = None
    ) -> SearchEvaluationOutput:

        if params is None:
            params = SearchQualityCheckInput(
                user_query=ctx.state["latest_query"],
                search_results=[
                    SearchResultInput(**r)
                    for r in ctx.state["search_results"]
                ]
            )

        result = await search_quality_check_agent.run(
            user_prompt=params.model_dump_json()
        )
        return result.output
    
    # fetch more data using the get_data_to_index tool and 
    # Summarizing agent
    summarizing_instructions = """
        Based on the following conversation history:
        Context: {context}
        Current query: {latest_query}

        Provide a concise summary of what the user is asking.
    """

    summarize_agent = Agent(
        name="summarize",
        instructions=summarizing_instructions,
        # tools= summarize_tool,
        model='gpt-4o-mini'
    )

    def format_summarizing_instructions(context, latest_query):

        return summarizing_instructions.format(
            context=context,
            latest_query=latest_query
        )

    async def generate_summary(ctx: RunContext, user_prompt):
        """
        Runs the summarizing agent to summarize conversation history

        Args:
            query: raw user request.

        Returns:
            A short text summarizing the answer to user's query
        """

        callback = NamedCallback(summarize_agent)
        results = await summarize_agent.run(user_prompt=user_prompt, event_stream_handler=callback)

        return results.output


     # You repeat this process at least 3 times or until the search_quality_check agent has overall_quality_score of at least 0.4.
    orchestrator_instructions = """
        You are a helpful assistant that answers user questions only based on arxiv research articles.

        When a user asks a query, you always summarize the query using the generate_summary tool.
        Then you search the index to find relevant results. 
        If you cannot find anything relevant, then you fetch the relevant articles from arxiv using the get_data_to_index tool.
        Then you perfrom a search using the search tool again.

        You always call the search_quality_check tool after searching the index to evaluate the quality of the retrieved search results.
        If the search_quality_check tool indicates "More data is needed", then you may perform additional search using the suggested_search_terms.

        You provide a complete and correct answer to the user's question by summarizing all these search results. Do not spend too much time searching.
        You always provide at least 3 relevant and appropriate references to all artciles you use when summarizing search results.
    """.strip()

    orchestrator_tools = [agent_class.get_data_to_index, agent_class.search, search_quality_check]

    orchestrator_agent = Agent(
        name="orchestrator",
        tools=orchestrator_tools,
        instructions=orchestrator_instructions,
        model='openai:gpt-4o-mini',
        output_type=SearchResultSummary
    )
    

    return orchestrator_agent

