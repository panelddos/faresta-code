from typing import Generator
from openai import OpenAI
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096, effort: str = "medium"):
        super().__init__(api_key, model, temperature, max_tokens, effort)
        self.client = OpenAI(api_key=api_key)

    def chat(self, messages: list[dict], stream: bool = True, tools: list[dict] | None = None) -> Generator[dict, None, None]:
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            stream=stream,
        )
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        if stream:
            full_content = ""
            tool_calls_acc: dict[int, dict] = {}
            for chunk in response:
                if not chunk.choices:
                    if hasattr(chunk, 'usage') and chunk.usage:
                        yield {"type": "usage", "input_tokens": chunk.usage.prompt_tokens or 0, "output_tokens": chunk.usage.completion_tokens or 0}
                    continue
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    full_content += delta.content
                    yield {"type": "content", "content": delta.content}
                if delta and delta.tool_calls:
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in tool_calls_acc:
                            tool_calls_acc[idx] = {"id": tc.id or "", "name": (tc.function.name if tc.function else "") or "", "arguments": ""}
                        if tc.id:
                            tool_calls_acc[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                tool_calls_acc[idx]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_acc[idx]["arguments"] += tc.function.arguments
            if full_content:
                yield {"type": "content_done", "content": full_content}
            if tool_calls_acc:
                calls = [{"type": "tool_call", "id": v["id"], "name": v["name"], "arguments": v["arguments"]} for k, v in sorted(tool_calls_acc.items())]
                for c in calls:
                    yield c
        else:
            msg = response.choices[0].message
            if msg.content:
                yield {"type": "content", "content": msg.content}
                yield {"type": "content_done", "content": msg.content}
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    yield {"type": "tool_call", "id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments}

    def chat_non_streaming(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        kwargs = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        effort_map = {"low": "low", "medium": "medium", "high": "high"}
        if self.model in ("o1", "o3-mini", "o1-mini", "o3"):
            kwargs["reasoning_effort"] = effort_map.get(self.effort, "medium")
        if tools:
            kwargs["tools"] = tools
        response = self.client.chat.completions.create(**kwargs)
        msg = response.choices[0].message
        result = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            result["tool_calls"] = [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in msg.tool_calls
            ]
        if hasattr(response, 'usage') and response.usage:
            result["usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        return result
