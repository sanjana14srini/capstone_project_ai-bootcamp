import json

from dataclasses import dataclass
from typing import List


@dataclass
class ToolCall:
    name: str
    args: dict


def get_tool_calls(result) -> List[ToolCall]:
    """Extract tool-call parts from an agent result and return them as ToolCall objects."""
    calls: List[ToolCall] = []

    for m in result.new_messages():
        for p in m.parts:
            kind = p.part_kind
            if kind == 'tool-call':
                call = ToolCall(
                    name=p.tool_name,
                    args=json.loads(p.args)
                )
                calls.append(call)

    return calls
