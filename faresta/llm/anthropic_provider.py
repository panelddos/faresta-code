from typing import Generator
from anthropic import Anthropic
from .base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", temperature: float = 0.7, max_tokens: int = 4096):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = Anthropic(api_key=api_key)

    def _prepare_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            elif m["role"] == "tool":
                filtered.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}]})
            else:
                filtered.append(m)
        return system, filtered

    def chat(self, messages: list[dict], stream: bool = True, tools: list[dict] | None = None) -> Generator[dict, None, None]:
        system, filtered = self._prepare_messages(messages)

        kwargs = dict(
            model=self.model,
            messages=filtered,
            system=system or None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools

        if stream:
            with self.client.messages.stream(**kwargs) as stream_resp:
                current_tool_block = None
                for event in stream_resp:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool_block = {"id": event.content_block.id, "name": event.content_block.name, "arguments": ""}
                            yield {"type": "tool_call_start", "id": event.content_block.id, "name": event.content_block.name, "arguments": ""}
                        elif event.content_block.type == "text":
                            yield {"type": "content", "content": event.content_block.text}
                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield {"type": "content", "content": event.delta.text}
                        elif event.delta.type == "input_json_delta" and current_tool_block:
                            current_tool_block["arguments"] += event.delta.partial_json
                            yield {"type": "tool_call_args", "id": current_tool_block["id"], "arguments": event.delta.partial_json}
                    elif event.type == "content_block_stop" and current_tool_block:
                        yield {"type": "tool_call", "id": current_tool_block["id"], "name": current_tool_block["name"], "arguments": current_tool_block["arguments"]}
                        current_tool_block = None
                final = stream_resp.get_final_message()
                if final.content:
                    for block in final.content:
                        if block.type == "text":
                            yield {"type": "content_done", "content": block.text}
                            break
        else:
            response = self.client.messages.create(**kwargs)
            result_content = ""
            for block in response.content:
                if block.type == "text":
                    result_content += block.text
                    yield {"type": "content", "content": block.text}
                elif block.type == "tool_use":
                    yield {"type": "tool_call", "id": block.id, "name": block.name, "arguments": block.input}
            if result_content:
                yield {"type": "content_done", "content": result_content}

    def chat_non_streaming(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        system, filtered = self._prepare_messages(messages)
        kwargs = dict(
            model=self.model,
            messages=filtered,
            system=system or None,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        if tools:
            kwargs["tools"] = tools
        response = self.client.messages.create(**kwargs)
        content = ""
        tool_calls = []
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({"id": block.id, "type": "function", "function": {"name": block.name, "arguments": block.input}})
        result = {"role": "assistant", "content": content}
        if tool_calls:
            result["tool_calls"] = tool_calls
        if hasattr(response, 'usage') and response.usage:
            result["usage"] = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        return result
