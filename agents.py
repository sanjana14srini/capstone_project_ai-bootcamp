from tools import Agent_Tools
from elasticsearch import Elasticsearch

from pydantic_ai import Agent, RunContext
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic import BaseModel
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


    # Summarizing agent
    summarizing_instructions = """
        You are a helpful assistant that answers user questions only based on arxiv research articles.

        When a user asks a query, you first search the index to find relevant results. 
        If you cannot find anything relevant, then you fetch the relevant articles from arxiv using the get_data_to_index tool.
        Then you perfrom a search using the search tool again.

        You answer the user's question by summarizing all these search results.
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

    return summarize_agent

