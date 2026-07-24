from typing import Generator
from openai import OpenAI
from .base import LLMProvider


COMPATIBLE_PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "env_key": "GROQ_API_KEY",
    },
    "xai": {
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-2-1212",
        "env_key": "XAI_API_KEY",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "meta/llama-3.1-70b-instruct",
        "env_key": "NVIDIA_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "env_key": "MISTRAL_API_KEY",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "default_model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "env_key": "TOGETHER_API_KEY",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3.5-sonnet",
        "env_key": "OPENROUTER_API_KEY",
    },
}


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o", temperature: float = 0.7, max_tokens: int = 4096, base_url: str | None = None):
        super().__init__(api_key, model, temperature, max_tokens)
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = OpenAI(**kwargs)

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
        if hasattr(response, 'usage') and response.usage:
            result["usage"] = {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        return result


def create_provider(name: str, api_key: str, model: str = "", temperature: float = 0.7, max_tokens: int = 4096) -> OpenAICompatibleProvider:
    info = COMPATIBLE_PROVIDERS.get(name)
    if not info:
        raise ValueError(f"Unknown provider '{name}'")
    return OpenAICompatibleProvider(
        api_key=api_key,
        model=model or info["default_model"],
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=info["base_url"],
    )