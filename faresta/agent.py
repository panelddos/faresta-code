import json
import time
from .config import Config
from .project_config import ProjectConfig
from .llm.base import LLMProvider
from .tools.registry import get_registry
from .utils.display import console, print_error, print_info, print_warning, confirm_action


class CostTracker:
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.rounds = 0

    def add_usage(self, input_tokens: int, output_tokens: int, provider: str = "openai"):
        rates = {
            "openai": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
            "anthropic": {"input": 3.00 / 1_000_000, "output": 15.00 / 1_000_000},
            "google": {"input": 0.10 / 1_000_000, "output": 0.40 / 1_000_000},
        }
        rate = rates.get(provider, rates["openai"])
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost += (input_tokens * rate["input"]) + (output_tokens * rate["output"])
        self.rounds += 1

    def summary(self) -> str:
        return (
            f"Tokens: {self.total_input_tokens:,} in / {self.total_output_tokens:,} out | "
            f"Cost: ${self.total_cost:.4f} | Rounds: {self.rounds}"
        )


class Agent:
    def __init__(self, llm: LLMProvider, config: Config):
        self.llm = llm
        self.config = config
        self.registry = get_registry()
        self.messages: list[dict] = []
        self.max_tool_rounds = 25
        self.project_config = ProjectConfig.load()
        self.cost_tracker = CostTracker()
        self.session_id = str(int(time.time()))

    def add_system_prompt(self):
        tools_desc = "\n".join(f"  - {t.name}: {t.description}" for t in self.registry.list_tools())
        system = self.config.system_prompt

        if self.project_config.system_prompt_extra:
            system += f"\n\n{self.project_config.system_prompt_extra}"

        if tools_desc:
            system += f"\n\nAnda memiliki akses ke tools berikut:\n{tools_desc}\n\nGunakan tools saat diperlukan. Jika tool mengembalikan error, jelaskan ke user dan coba pendekatan alternatif."
        system += "\n\nSebelum menjalankan tool, jelaskan secara singkat apa yang akan Anda lakukan dan mengapa."
        self.messages.append({"role": "system", "content": system})

    def run(self, user_input: str) -> str:
        if self.llm is None:
            return "API key belum di-set. Ketik /login untuk setup provider dan API key."
        self.messages.append({"role": "user", "content": user_input})
        final_response = ""
        tool_round = 0

        while tool_round < self.max_tool_rounds:
            tool_round += 1
            has_tool_calls = False

            assistant_msg = self.llm.chat_non_streaming(
                messages=self.messages,
                tools=self._get_tools_for_api(),
            )

            response_text = assistant_msg.get("content", "")
            tool_calls = assistant_msg.get("tool_calls", [])

            if assistant_msg.get("usage"):
                usage = assistant_msg.pop("usage")
                self.cost_tracker.add_usage(
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    self.config.provider,
                )

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

                    allowed = self.project_config.is_tool_allowed(name)
                    if allowed is False:
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "tool_name": name,
                            "content": f"Error: Tool '{name}' is denied by project config (faresta.json)",
                        })
                        continue
                    elif allowed is None and self.config.tool_confirm:
                        args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                        if not confirm_action(f"Run tool '{name}' with args: {args_str}"):
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tc.get("id", ""),
                                "tool_name": name,
                                "content": "Tool execution cancelled by user",
                            })
                            continue

                    print_info(f"  Using tool: {name}")
                    result = self.registry.execute(name, **args)

                    if "Error" in result[:10] and tool_round < self.max_tool_rounds:
                        print_warning(f"  Tool '{name}' returned error, will retry with explanation")
                        self.messages.append(assistant_msg)
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tc.get("id", ""),
                            "tool_name": name,
                            "content": result[:2000] if len(result) > 2000 else result,
                        })
                        self.messages.append({
                            "role": "user",
                            "content": f"Tool '{name}' returned an error: {result[:500]}. Please analyze the error and try a different approach or fix the issue.",
                        })
                        continue

                    tool_results.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id", ""),
                        "tool_name": name,
                        "content": result[:3000] if len(result) > 3000 else result,
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

    def get_history(self) -> list[dict]:
        return self.messages

    def restore_history(self, messages: list[dict]):
        self.messages = messages