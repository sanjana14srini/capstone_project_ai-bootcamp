from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from main import run_sync_agent
import json
import asyncio
from jaxn import StreamingJSONParser, JSONParserHandler
from agents import create_agents, NamedCallback
from agent_logging import log_run, save_log, create_log_entry, log_streamed_run
from pydantic import BaseModel

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

app = FastAPI()


class SearchResultArticleHandler(JSONParserHandler):
    def on_field_start(self, path: str, field_name: str):
        if field_name == "references":
            level = path.count("/") + 2
            print(f"\n{'#' * level} References\n")

    def on_field_end(self, path, field_name, value, parsed_value=None):
        if field_name == "title" and path == "":
            print(f"# {value}")

        elif field_name == "heading":
            print(f"\n\n## {value}\n")
        elif field_name == "content":
            print("\n") 

    def on_value_chunk(self, path, field_name, chunk):
        if field_name == "content":
            print(chunk, end="", flush=True)

    def on_array_item_end(self, path, field_name, item=None):
        if field_name == "references":
            title = item.get("title", "")
            filename = item.get("filename", "")
            print(f"- [{title}]({filename})")

# -----------------------------------------------------
# Replace this with your real agent logic.
# It must be an async generator that yields events.
# -----------------------------------------------------
handler = SearchResultArticleHandler()
parser = StreamingJSONParser(handler)

async def agent_stream(messages):
    """
    Simulated agent generator.
    Replace this with your actual agent/tool logic.
    Must be async generator.
    """

    try:
        agent = create_agents()
        agent_callback = NamedCallback(agent)


        handler = SearchResultArticleHandler()
        parser = StreamingJSONParser(handler)

        previous_text = ""

        user_input = messages[-1]["content"]
        result = await agent.run(
            user_input, event_stream_handler=agent_callback
        ) 

        # Assuming result.output is a SearchResultSummary object
        summary: SearchResultSummary = result.output

        # Keep the if logic by checking attributes on the final object
        # Process text attribute if it exists
        if hasattr(summary, "text") and summary.text:
            yield {"type": "token", "content": summary.text}

        # Process final_result tool (full output now)
        # Apply format_article on the structured object
        formatted_article = summary.format_article()

        # Assume formatted_article is the fully formatted string
        chunk_size = 10  # number of characters per chunk, adjust as needed
        start = 0
        end = chunk_size
        length = len(formatted_article)

        while start < length:
            yield {
                "type": "token",
                "content": formatted_article[start:end]
            }
            start = end
            end = min(end + chunk_size, length)
            await asyncio.sleep(0.1)


        log_entry = log_run(agent, result)
        save_log(log_entry)
    
    except Exception as e:
        yield {"type": "error", "message": str(e)}

    # try:
    #     # Example token streaming
    #     for word in ["Hello", ", ", "this ", "is ", "a ", "streamed ", "response."]:
    #         yield {"type": "token", "content": word}
    #         await asyncio.sleep(0.2)  # simulate processing time

    #     # Example tool call
    #     yield {
    #         "type": "tool_call",
    #         "tool_name": "search",
    #         "arguments": {"query": "Example search query"}
    #     }

    #     # Another token after tool
    #     yield {"type": "token", "content": "\nDone!"}

    # except Exception as e:
    #     # Yield error as a streamed event
    #     yield {"type": "error", "message": str(e)}


@app.post("/chat")
async def chat_endpoint(request: Request):
    try:
        payload = await request.json()
        messages = payload.get("messages", [])

        async def event_generator():
            async for event in agent_stream(messages):
                # Convert event to JSON string + newline
                yield json.dumps(event) + "\n"

        return StreamingResponse(event_generator(), media_type="text/plain")

    except Exception as e:
        # Return a simple JSON error if parsing fails
        return {"error": str(e)}
