"""Provider-neutral envelopes for one native tool-calling turn."""
from dataclasses import dataclass, field


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: object


@dataclass
class AgentTurn:
    text: str = ''
    calls: list[ToolCall] = field(default_factory=list)
    continuation: list = field(default_factory=list)


def tool_result_messages(provider, results):
    if provider == 'openai':
        return [{'type': 'function_call_output', 'call_id': call.id, 'output': result} for call, result in results]
    if provider == 'anthropic':
        return [{'role': 'user', 'content': [{'type': 'tool_result', 'tool_use_id': call.id, 'content': result} for call, result in results]}]
    return [{'role': 'tool', 'tool_call_id': call.id, 'name': call.name, 'content': result} for call, result in results]
