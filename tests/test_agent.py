from main import run_sync_agent
from tests.utils import get_tool_calls
from agents import SearchResultSummary


def test_agent_tool_calls_present():
    result = run_sync_agent("recent research in transformer models")
    # print(result.output)

    tool_calls = get_tool_calls(result)

    search_tool_calls = 0
    get_data_to_index_tool_calls = 0
    search_quality_check_tool_calls = 0
    for call in tool_calls:
        if call.name == 'search':
            search_tool_calls += 1
        if call.name == 'get_data_to_index':
            get_data_to_index_tool_calls += 1
        if call.name == 'search_quality_check':
            search_quality_check_tool_calls += 1


    assert len(tool_calls) > 0, "No tool calls found"
    assert search_tool_calls > 0, "No calls made for search tool"
    assert search_quality_check_tool_calls > 0, "No calls made for search_quality_check tool"


    
def test_agent_adds_references():
    user_prompt = "recent research in transformer models"
    result = run_sync_agent(user_prompt)

    summary: SearchResultSummary = result.output
    print(summary.format_article())

    tool_calls = get_tool_calls(result)
    assert len(tool_calls) >= 1, f"Expected at least 1 tool call, got {len(tool_calls)}"

    assert len(summary.summary) > 0, "Expected at summary section in the article"
    assert len(summary.references) > 0, "Expected at least one reference in the article"

def test_agent_quality_check_after_search():
    result = run_sync_agent("recent research in transformer models")
    # print(result.output)

    tool_calls = get_tool_calls(result)

    search_tool_calls = 0
    search_quality_check_tool_calls = 0
    for call in tool_calls:
        if call.name == 'search':
            search_tool_calls += 1
        if call.name == 'search_quality_check':
            search_quality_check_tool_calls += 1


    assert len(tool_calls) > 0, "No tool calls found"
    assert search_tool_calls == search_quality_check_tool_calls, "Search calls were not checked for quality"