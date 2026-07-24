from typing import Generator
from openai import OpenAI
from .base import LLMProvider


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096):
        super().__init__(api_key, model, temperature, max_tokens)
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
            for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    full_content += delta.content
                    yield {"type": "content", "content": delta.content}
                if delta and delta.tool_calls:
                    for tc in delta.tool_calls:
                        yield {"type": "tool_call_start", "id": tc.id, "name": tc.function.name if tc.function else "", "arguments": tc.function.arguments if tc.function else ""}
            if full_content:
                yield {"type": "content_done", "content": full_content}
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
        return result
