import json
import time
from .config import Config
from .llm.base import LLMProvider
from .tools.registry import get_registry
from .utils.display import console, print_error, print_info


class Agent:
    def __init__(self, llm: LLMProvider, config: Config):
        self.llm = llm
        self.config = config
        self.registry = get_registry()
        self.messages: list[dict] = []
        self.max_tool_rounds = 25
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def add_system_prompt(self):
        tools_desc = "\n".join(f"  - {t.name}: {t.description}" for t in self.registry.list_tools())
        system = self.config.system_prompt
        if tools_desc:
            system += f"\n\nAnda memiliki akses ke tools berikut:\n{tools_desc}\n\nGunakan tools saat diperlukan. Jika tool mengembalikan error, jelaskan ke user."
        self.messages.append({"role": "system", "content": system})

    def run(self, user_input: str) -> str:
        self.messages.append({"role": "user", "content": user_input})
        final_response = ""
        tool_round = 0

        while tool_round < self.max_tool_rounds:
            tool_round += 1
            has_tool_calls = False
            response_text = ""

            assistant_msg = self.llm.chat_non_streaming(
                messages=self.messages,
                tools=self._get_tools_for_api(),
            )

            response_text = assistant_msg.get("content", "")
            tool_calls = assistant_msg.get("tool_calls", [])

            if tool_calls:
                has_tool_calls = True
                if response_text:
                    final_response += response_text + "\n\n"

                tool_results = []
                for tc in tool_calls:
                    fn = tc.get("function", {})
                    name = fn.get("name", "")
                    raw_args = fn.get("arguments", "{}")
                    if isinstance(raw_args, str):
                        try:
                            args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = raw_args

                    print_info(f"  Using tool: {name}")

                    result = self.registry.execute(name, **args)
                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "tool_name": name,
                        "content": result[:2000] if len(result) > 2000 else result,
                    })

                self.messages.append(assistant_msg)
                self.messages.extend(tool_results)
            else:
                final_response += response_text
                self.messages.append(assistant_msg)
                break

            if not has_tool_calls:
                break

        return final_response.strip()

    def _get_tools_for_api(self):
        provider = self.config.provider
        tools = self.registry.list_tools()
        if not tools:
            return None
        if provider == "openai":
            return self.registry.to_openai_tools()
        elif provider == "anthropic":
            return self.registry.to_anthropic_tools()
        elif provider == "google":
            return self.registry.to_google_tools()
        return None

    def reset(self):
        self.messages = []
        self.add_system_prompt()
        self.total_input_tokens = 0
        self.total_output_tokens = 0
