from typing import Generator
from google import genai
from google.genai import types
from .base import LLMProvider


class GoogleProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", temperature: float = 0.7, max_tokens: int = 4096, effort: str = "medium"):
        super().__init__(api_key, model, temperature, max_tokens, effort)
        self.client = genai.Client(api_key=api_key)

    def _prepare_contents(self, messages: list[dict]) -> tuple[str, list]:
        history = []
        system = ""
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            elif m["role"] == "tool":
                history.append(types.Content(
                    role="user",
                    parts=[types.Part.from_function_response(name=m.get("tool_name", ""), response={"result": m["content"]})]
                ))
            elif m["role"] == "assistant":
                parts = []
                if m.get("content"):
                    parts.append(types.Part.from_text(m["content"]))
                for tc in m.get("tool_calls", []):
                    fn = tc.get("function", {})
                    parts.append(types.Part.from_function_call(name=fn.get("name", ""), args=fn.get("arguments", {})))
                history.append(types.Content(role="model", parts=parts))
            elif m["role"] == "user":
                history.append(types.Content(role="user", parts=[types.Part.from_text(m["content"])]))
        return system, history

    def _build_tool_config(self, tools: list[dict] | None):
        if not tools:
            return None
        fn_decls = []
        for t in tools:
            t_func = t.get("function", t)
            fn_decls.append(types.FunctionDeclaration(
                name=t_func.get("name", ""),
                description=t_func.get("description", ""),
                parameters=t_func.get("parameters", {}),
            ))
        return types.Tool(function_declarations=fn_decls)

    def chat(self, messages: list[dict], stream: bool = True, tools: list[dict] | None = None) -> Generator[dict, None, None]:
        system, history = self._prepare_contents(messages)
        tool_config = self._build_tool_config(tools)

        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            system_instruction=system or None,
            tools=[tool_config] if tool_config else None,
        )

        response = self.client.models.generate_content_stream(
            model=self.model,
            contents=history,
            config=config,
        )

        full_content = ""
        for chunk in response:
            if chunk.text:
                full_content += chunk.text
                yield {"type": "content", "content": chunk.text}
            if chunk.candidates:
                for c in chunk.candidates:
                    if c.content and c.content.parts:
                        for part in c.content.parts:
                            if part.function_call:
                                fc = part.function_call
                                yield {"type": "tool_call", "id": str(id(fc)), "name": fc.name, "arguments": str(dict(fc.args)) if hasattr(fc, 'args') else "{}"}
        if full_content:
            yield {"type": "content_done", "content": full_content}
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            yield {"type": "usage", "input_tokens": response.usage_metadata.prompt_token_count, "output_tokens": response.usage_metadata.candidates_token_count}

    def chat_non_streaming(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        system, history = self._prepare_contents(messages)
        tool_config = self._build_tool_config(tools)

        config_kwargs = dict(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
            system_instruction=system or None,
            tools=[tool_config] if tool_config else None,
        )
        effort_map = {"low": "disable", "medium": "enable", "high": "enable"}
        if effort_map.get(self.effort) == "disable":
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        elif self.effort == "high":
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=4096)

        config = types.GenerateContentConfig(**config_kwargs)

        response = self.client.models.generate_content(
            model=self.model,
            contents=history,
            config=config,
        )

        content = response.text or ""
        tool_calls = []
        if response.candidates:
            for c in response.candidates:
                if c.content and c.content.parts:
                    for part in c.content.parts:
                        if part.function_call:
                            fc = part.function_call
                            tool_calls.append({
                                "id": str(id(fc)),
                                "type": "function",
                                "function": {"name": fc.name, "arguments": dict(fc.args) if hasattr(fc, 'args') else {}},
                            })
        result = {"role": "assistant", "content": content}
        if tool_calls:
            result["tool_calls"] = tool_calls
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            result["usage"] = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }
        return result
