import asyncio
from agents import create_agents, NamedCallback
from toyaikit.chat.interface import StdOutputInterface
from pydantic_ai.messages import ModelMessage
from toyaikit.chat.runners import PydanticAIRunner
from monitoring.agent_logging import log_run, save_log, create_log_entry
import asyncio

class LoggingStdOutputInterface(StdOutputInterface):
    """
    StdOutputInterface that also captures messages for logging.
    """
    def __init__(self):
        super().__init__()
        self._captured_messages = []

    def send_message(self, message: ModelMessage):
        # Call the original StdOutputInterface behavior (prints to stdout)
        # super().send_message(message)
        self._captured_messages.append(message)
        
        # Save partial log
        log_entry = create_log_entry(
            agent=agent,
            messages=self._captured_messages,
            usage=None,  # or partial usage if available
            output=""
        )
        save_log(log_entry)

    @property
    def captured_messages(self):
        return self._captured_messages
    
async def run_agent_with_logging(agent, runner):
    """
    agent: your Agent
    runner: PydanticAIRunner with StdOutputInterface
    user_messages: List[ModelMessage] of the conversation so far
    """
    # Run the agent
    result = await runner.run()

    # Wrap agent output as a message
    agent_message = ModelMessage(role="assistant", content=result.output)

    # Combine user messages + agent output
    

    # Create log
    log_entry = create_log_entry(
        agent=agent,
        messages=agent_message,
        usage=result.usage(),
        output=result.output
    )

    # Save log
    log_file = save_log(log_entry)
    print(f"Log saved to: {log_file}")

    return result
    
agent = create_agents()
agent_callback = NamedCallback(agent)



async def run_agent(user_prompt: str):
    results = await agent.run(
            user_prompt=user_prompt,
            event_stream_handler=agent_callback
    )

    return results


def run_sync_agent(user_prompt: str):
    return asyncio.run(run_agent(user_prompt))


async def main():
    chat_interface = StdOutputInterface()
    # StdOutputInterface()

    runner = PydanticAIRunner(
        chat_interface=chat_interface,
        agent=agent
    )
    result = await run_agent_with_logging(agent, runner);
    output = result.output

    # print(output)

if __name__ == "__main__":
    asyncio.run(main())