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
        system += "\n\nSetelah Anda mengedit atau menulis file, sistem akan otomatis menjalankan linter. Jika ada error linter, hasilnya akan ditampilkan — perbaiki error tersebut sebelum lanjut."
        self.messages.append({"role": "system", "content": system})

    def run(self, user_input: str) -> str:
        if self.llm is None:
            return "API key belum di-set. Ketik /login untuk setup provider dan API key."
        result = ""
        for event in self.run_streaming(user_input):
            if event["type"] == "done":
                result = event["content"]
        return result

    def run_streaming(self, user_input: str):
        """Generator that yields streaming events while processing input.
        
        Events:
          {"type": "content", "content": str}      — text token
          {"type": "content_done", "content": str} — full text complete
          {"type": "tool_call", ...}                — tool call started (non-streaming event from previous round)
          {"type": "tool_start", "name": str}       — tool execution starting
          {"type": "tool_result", "name": str, "content": str, "error": bool} — tool result
          {"type": "done", "content": str}          — all done, final response
        """
        if self.llm is None:
            yield {"type": "done", "content": "API key belum di-set. Ketik /login untuk setup provider dan API key."}
            return

        self.messages.append({"role": "user", "content": user_input})
        final_response = ""
        tool_round = 0
        retry_counts: dict[str, int] = {}
        max_retries_per_tool = 3

        while tool_round < self.max_tool_rounds:
            tool_round += 1
            round_content = ""
            round_tool_calls = []
            usage = None

            try:
                for event in self.llm.chat(
                    messages=self.messages,
                    tools=self._get_tools_for_api(),
                ):
                    if event["type"] == "content":
                        round_content += event["content"]
                        yield event
                    elif event["type"] == "content_done":
                        round_content = event["content"]
                        yield event
                    elif event["type"] == "tool_call":
                        round_tool_calls.append(event)
                    elif event["type"] == "usage":
                        usage = event
            except Exception as e:
                err = str(e).lower()
                if "401" in err or "unauthorized" in err or "auth" in err:
                    yield {"type": "done", "content": "✖ API Key tidak valid. Ketik /login untuk set API key baru."}
                elif "429" in err or "rate" in err or "quota" in err:
                    yield {"type": "done", "content": "✖ Rate limit / quota habis. Tunggu beberapa saat atau ganti provider."}
                elif "timeout" in err or "timed out" in err:
                    yield {"type": "done", "content": "✖ Provider AI timeout. Coba model yang lebih kecil atau effort lebih rendah."}
                elif ("context" in err and "length" in err) or "too long" in err or ("maximum" in err and "token" in err):
                    self.messages = [self.messages[0]] + self.messages[-4:]
                    yield {"type": "done", "content": "✖ Konteks penuh — percakapan lama dihapus, silakan kirim ulang."}
                else:
                    raise
                return

            if usage:
                self.cost_tracker.add_usage(
                    usage.get("input_tokens", 0),
                    usage.get("output_tokens", 0),
                    self.config.provider,
                )

            if not round_tool_calls:
                final_response += round_content
                self.messages.append({"role": "assistant", "content": round_content})
                yield {"type": "done", "content": final_response.strip()}
                return

            has_tool_calls = True
            if round_content:
                final_response += round_content + "\n\n"

            tool_results = []
            for tc in round_tool_calls:
                name = tc.get("name", "")
                raw_args = tc.get("arguments", "{}")
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
                        "role": "tool", "tool_call_id": tc.get("id", ""),
                        "tool_name": name,
                        "content": f"Error: Tool '{name}' is denied by project config (faresta.json)",
                    })
                    continue
                elif allowed is None and self.config.tool_confirm:
                    args_str = ", ".join(f"{k}={v}" for k, v in args.items())
                    if not confirm_action(f"Run tool '{name}' with args: {args_str}"):
                        tool_results.append({
                            "role": "tool", "tool_call_id": tc.get("id", ""),
                            "tool_name": name, "content": "Tool execution cancelled by user",
                        })
                        continue

                yield {"type": "tool_start", "name": name}
                result = self.registry.execute(name, **args)

                if not result.startswith("Error") and name in ("edit", "write", "delete"):
                    lint_result = self.registry.execute("lint_test", command="lint", path=".")
                    if lint_result and "No recognized" not in lint_result:
                        result += f"\n\n[auto-lint]\n{lint_result}"

                is_error = "Error" in result[:10]
                yield {"type": "tool_result", "name": name, "content": result[:300] if is_error else result[:200], "error": is_error}

                if is_error and tool_round < self.max_tool_rounds:
                    retry_counts[name] = retry_counts.get(name, 0) + 1
                    if retry_counts[name] > max_retries_per_tool:
                        print_warning(f"  Tool '{name}' gagal setelah {max_retries_per_tool}x percobaan, berhenti")
                        tool_results.append({
                            "role": "tool", "tool_call_id": tc.get("id", ""),
                            "tool_name": name, "content": result[:2000],
                        })
                        continue
                    assistant_msg = {"role": "assistant", "content": round_content, "tool_calls": [{
                        "id": tc.get("id", ""), "type": "function",
                        "function": {"name": name, "arguments": raw_args},
                    }]}
                    self.messages.append(assistant_msg)
                    self.messages.append({
                        "role": "tool", "tool_call_id": tc.get("id", ""),
                        "tool_name": name, "content": result[:2000],
                    })
                    self.messages.append({
                        "role": "user",
                        "content": f"Tool '{name}' returned an error: {result[:500]}. Please analyze the error and try a different approach or fix the issue.",
                    })
                    continue

                tool_results.append({
                    "role": "tool", "tool_call_id": tc.get("id", ""),
                    "tool_name": name, "content": result[:3000] if len(result) > 3000 else result,
                })

            if tool_results:
                assistant_msg = {"role": "assistant", "content": round_content, "tool_calls": [
                    {"id": tc.get("id", ""), "type": "function",
                     "function": {"name": tc.get("name", ""), "arguments": tc.get("arguments", "{}")}}
                    for tc in round_tool_calls
                ]}
                self.messages.append(assistant_msg)
                self.messages.extend(tool_results)

            if not has_tool_calls:
                break

        yield {"type": "done", "content": final_response.strip()}

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