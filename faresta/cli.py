import sys
import json
import click
from pathlib import Path
from datetime import datetime
from rich.prompt import Prompt
from rich.panel import Panel
from rich.table import Table
from rich import box
from .config import load_config, save_config, Config, HISTORY_DIR, PROVIDER_DEFAULTS
from .project_config import ProjectConfig
from .llm.base import LLMProvider
from .llm.openai_provider import OpenAIProvider
from .llm.anthropic_provider import AnthropicProvider
from .llm.google_provider import GoogleProvider
from .llm.openai_compatible import create_provider, COMPATIBLE_PROVIDERS
from .agent import Agent
from .tools.core import register_core_tools
from .tools.social import register_social_tools
from .utils.display import (
    console, print_welcome, print_markdown, print_error,
    print_info, print_success, print_warning, input_user,
)


SESSION_DIR = HISTORY_DIR


def get_provider(config: Config) -> LLMProvider | None:
    if not config.api_key:
        return None

    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
    }

    if config.provider in providers:
        cls = providers[config.provider]
        return cls(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            effort=config.effort,
        )

    if config.provider in COMPATIBLE_PROVIDERS:
        return create_provider(
            name=config.provider,
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            effort=config.effort,
        )

    known = ", ".join(providers.keys())
    if COMPATIBLE_PROVIDERS:
        known += ", " + ", ".join(COMPATIBLE_PROVIDERS.keys())
    print_error(f"Unknown provider '{config.provider}'. Available: {known}")
    print_info("Tip: Cek config dengan: faresta config-show")
    sys.exit(1)


@click.group()
@click.version_option(version="0.4.0", prog_name="faresta")
def main():
    register_core_tools()
    register_social_tools()


@main.command()
@click.argument("question", required=False)
@click.option("-p", "--provider", help="LLM provider (openai, anthropic, google)")
@click.option("-m", "--model", help="Model name")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation for tool execution")
def ask(question, provider, model, yes):
    """Ask a single question and get an answer."""
    config = load_config()
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if yes:
        config.tool_confirm = False

    llm = get_provider(config)
    agent = Agent(llm, config)
    agent.add_system_prompt()

    if not question:
        question = input_user("Question")

    console.print("[dim]Faresta:[/dim] ", end="")
    with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
        response = agent.run(question)
    print_markdown(response)

    tool_count = len([m for m in agent.messages if m["role"] == "tool"])
    if tool_count > 0:
        print_info(f"Tools used: {tool_count} calls")
    print_info(agent.cost_tracker.summary())


BANNER = """
[bold cyan]
    ███████▏ █████▏ ██████▏ ██████▏ ███████▏███████▏███████▏ █████▏
    ██╚████╝▕██╝╝██▏▕██╝╝██▏▕██╚████╝▕██╚████╝╚╝╝██╚╝╝▕██╝╝██▏
    █████▏  ███████▇▏██████▝▏█████▏  █████▏     ██▇   ███████▇▏
    ██╚╝  ▕██╝╝██▏▕██╝╝██▏▕██╝╝  ▕██╝╝     ██▇   ▕██╝╝██▏
    ██▇     ██▇  ██▏██▇  ██▏███████▏██▇        ██▇   ██▇  ██▏
    ╚╝     ╚╝  ╚╝╚╝  ╚╝╚╝╚╝╚╝╚╝╚╝╚╝        ╚╝   ╚╝  ╚╝
[/bold cyan]
"""


@main.command()
@click.option("-p", "--provider", help="LLM provider")
@click.option("-m", "--model", help="Model name")
@click.option("-y", "--yes", is_flag=True, help="Skip confirmation for tool execution")
@click.option("--resume", help="Resume a previous session by ID")
def chat(provider, model, yes, resume):
    """Start an interactive agentic chat session."""
    config = load_config()
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if yes:
        config.tool_confirm = False

    llm = get_provider(config)
    agent = Agent(llm, config)

    if resume:
        session_file = SESSION_DIR / f"{resume}.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            agent.restore_history(data["messages"])
            agent.cost_tracker.total_input_tokens = data.get("total_input_tokens", 0)
            agent.cost_tracker.total_output_tokens = data.get("total_output_tokens", 0)
            agent.cost_tracker.total_cost = data.get("total_cost", 0.0)
            agent.cost_tracker.rounds = data.get("rounds", 0)
        else:
            print_error(f"Session '{resume}' not found")
            agent.add_system_prompt()
            _inject_project_context(agent)
    else:
        agent.add_system_prompt()
        _inject_project_context(agent)

    _enter_alt_screen()
    _print_welcome(config)
    _repl(agent, config, llm)

    _enter_alt_screen()
    _print_welcome(config)
    _repl(agent, config, llm)


def _print_welcome(config):
    print("\033[2J\033[H", end="", flush=True)
    status = "[green]✓[/green]" if config.api_key else "[yellow]⚠ butuh /login[/yellow]"
    console.print(Panel(
        BANNER + f"\n[bold cyan]v0.6.0[/bold cyan] [dim]|[/dim] [cyan]{config.provider}/{config.model}[/cyan] [dim]|[/dim] Status: {status}",
        box=box.HEAVY, border_style="cyan", padding=(1, 2), subtitle="[dim]AI Coding Assistant CLI — ketik /help[/dim]"
    ))
    console.print("")
    if not config.api_key:
        console.print("  [yellow]⚠ API key belum di-set — ketik /login[/yellow]")
        console.print("")


@main.command()
def update():
    """Update Faresta Code to the latest version."""
    console.print("[cyan]Memeriksa pembaruan...[/cyan]")
    import os
    import subprocess
    import sys

    install_dir = os.environ.get("FARESTA_DIR") or os.path.expanduser("~/.faresta")
    if not os.path.isdir(install_dir):
        print_error("Tidak dapat menemukan instalasi Faresta Code.")
        console.print("  Jalankan ulang installer: curl -fsSL https://raw.githubusercontent.com/panelddos/faresta-code/main/install.sh | sh")
        return

    try:
        subprocess.run(["git", "-C", install_dir, "pull", "--ff-only"], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print_warning("Gagal pull update dari git. Coba manual: git pull di ~/.faresta")
        return

    venv_pip = os.path.join(install_dir, "venv", "bin", "pip")
    if not os.path.isfile(venv_pip):
        venv_pip = os.path.join(install_dir, "venv", "Scripts", "pip.exe")

    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", install_dir], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        if os.path.isfile(venv_pip) and os.access(venv_pip, os.X_OK):
            try:
                subprocess.run([venv_pip, "install", "-e", install_dir], check=True, capture_output=True)
            except subprocess.CalledProcessError as e2:
                print_error(f"Gagal update: {e2.stderr.decode()[:200]}")
                return
        else:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-e", install_dir, "--user"], check=True, capture_output=True)
            except subprocess.CalledProcessError:
                print_error("Gagal update. Coba manual: pip install -e ~/.faresta")
                return

    print_success("Faresta Code berhasil diupdate ke versi terbaru!")


def _inject_project_context(agent):
    try:
        from .tools.core.project import ProjectIndexTool
        tool = ProjectIndexTool()
        context = tool.execute(depth=2)
        agent.messages.append({
            "role": "user",
            "content": f"[Project context]\n{context}\n\nGunakan informasi ini untuk memahami struktur proyek. Jangan sebutkan bahwa kamu menjalankan project_index.",
        })
        agent.messages.append({
            "role": "assistant",
            "content": "Saya sudah membaca konteks proyek ini. Siap membantu.",
        })
    except Exception:
        pass


def _repl(agent, config, llm):
    def recreate_agent():
        nonlocal llm
        llm = get_provider(config)
        agent.llm = llm
        agent.messages = []
        agent.add_system_prompt()
        _print_welcome(config)

    while True:
        try:
            user_input = Prompt.ask("[bold]>[/bold]")
        except (EOFError, KeyboardInterrupt):
            _save_session(agent)
            _exit_alt_screen()
            console.print("[dim]bye[/dim]")
            break

        if user_input.lower() in ("exit", "quit"):
            _save_session(agent)
            _exit_alt_screen()
            console.print("[dim]bye[/dim]")
            break

        if user_input.strip().startswith("/"):
            _handle_slash_command(agent, user_input.strip(), config, recreate_agent)
            continue

        if not user_input.strip():
            continue

        console.rule(style="dim")
        console.print(f"[bold white on blue]  YOU  [/bold white on blue] [bold]{user_input}[/bold]")
        console.print("")

        response = ""
        tool_events = []
        error_occurred = False

        try:
            for event in agent.run_streaming(user_input):
                if event["type"] == "content":
                    if not response:
                        console.print(f"[bold white on cyan]  FARESTA  [/bold white on cyan]")
                        console.print("")
                    console.print(event["content"], end="", flush=True)
                    response += event["content"]
                elif event["type"] == "content_done":
                    response = event["content"]
                elif event["type"] == "tool_start":
                    print_info(f"  Using tool: {event['name']}")
                elif event["type"] == "tool_result":
                    tool_events.append(event)
                elif event["type"] == "done":
                    response = event["content"]
        except ConnectionError:
            console.print("\n[red]  ✖ Gagal terhubung ke provider AI. Periksa koneksi internet dan API key.[/red]")
            error_occurred = True
        except TimeoutError:
            console.print("\n[red]  ✖ Provider AI tidak merespon — coba lagi nanti atau ganti model/provider.[/red]")
            error_occurred = True
        except ValueError as e:
            msg = str(e)
            if "api key" in msg.lower() or "auth" in msg.lower():
                console.print("\n[red]  ✖ API Key tidak valid. Ketik /login untuk set API key baru.[/red]")
            elif "rate" in msg.lower() or "quota" in msg.lower():
                console.print("\n[red]  ✖ Rate limit tercapai atau quota habis. Tunggu beberapa saat.[/red]")
            else:
                console.print(f"\n[red]  ✖ Data tidak valid: {msg[:100]}[/red]")
            error_occurred = True
        except Exception:
            import traceback
            tb = traceback.format_exc()
            console.print(f"\n[red]  ✖ Terjadi kesalahan yang tidak terduga.[/red]")
            console.print(f"[dim]  Detail: {tb[:200]}[/dim]")
            error_occurred = True

        if response and not error_occurred:
            console.print("")
            console.print("")

        for ev in tool_events:
            fn_name = ev["name"]
            res = ev["content"]
            short = res[:80].replace("\n", " ") + ("..." if len(res) > 80 else "")
            status = "[red]✖[/red]" if ev.get("error") else "[dim]✓[/dim]"
            console.print(f"  {status} [dim]{fn_name} → {short}[/dim]")

        if tool_events:
            console.print("")

        _print_status_bar(agent, config)


def _print_status_bar(agent, config):
    cost = agent.cost_tracker
    rounds = cost.rounds
    total_cost = cost.total_cost
    effort = config.effort.upper() if config.effort else "MEDIUM"
    console.rule(
        f"[bold]{config.provider}/{config.model}[/bold] [dim]│[/dim] [dim]effort: {effort}[/dim] [dim]│[/dim] [dim]${total_cost:.4f}[/dim] [dim]│[/dim] [dim]{rounds} putaran[/dim]",
        style="cyan"
    )


def _enter_alt_screen():
    print("\033[?1049h\033[2J\033[H", end="", flush=True)


def _exit_alt_screen():
    print("\033[?1049l", end="", flush=True)


COMMON_MODELS = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "o3-mini", "o1-mini", "gpt-3.5-turbo"],
    "anthropic": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022", "claude-3-opus-20240229", "claude-3-haiku-20240307", "claude-3-5-haiku-20241022"],
    "google": ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.5-flash-8b"],
    "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama-3.2-90b-vision-preview", "mixtral-8x7b-32768", "gemma2-9b-it", "deepseek-r1-distill-llama-70b"],
    "xai": ["grok-2-1212", "grok-beta", "grok-vision-beta"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner", "deepseek-coder"],
    "mistral": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "open-mistral-nemo", "codestral-latest"],
    "together": ["meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo", "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo", "mistralai/Mixtral-8x22B-Instruct-v0.1", "Qwen/Qwen2.5-72B-Instruct-Turbo", "deepseek-ai/DeepSeek-V3"],
    "nvidia": ["meta/llama-3.1-70b-instruct", "meta/llama-3.1-8b-instruct", "mistralai/mistral-7b-instruct-v0.3", "google/gemma-2-27b-it", "nvidia/llama-3.1-nemotron-70b-instruct"],
    "openrouter": ["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "google/gemini-2.0-flash", "meta-llama/llama-3.1-70b-instruct", "deepseek/deepseek-chat", "mistralai/mistral-large"],
}


def _pick_provider(config, title="Pilih Provider"):
    PROVIDER_LIST = list(PROVIDER_DEFAULTS.keys())
    table = Table(title=title, box=box.SIMPLE, header_style="cyan")
    table.add_column("No", style="dim")
    table.add_column("Provider", style="cyan")
    table.add_column("Default Model", style="green")
    for i, name in enumerate(PROVIDER_LIST, 1):
        table.add_row(str(i), name, PROVIDER_DEFAULTS[name]["model"])
    console.print(table)

    choice = Prompt.ask("[yellow]Pilih nomor atau nama[/yellow]", default=config.provider)
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(PROVIDER_LIST):
            return PROVIDER_LIST[idx]
        return None
    return choice.lower() if choice.lower() in PROVIDER_DEFAULTS else None


def _pick_model(config):
    models = COMMON_MODELS.get(config.provider, [PROVIDER_DEFAULTS[config.provider]["model"]])
    table = Table(title=f"Model untuk {config.provider}", box=box.SIMPLE, header_style="cyan")
    table.add_column("No", style="dim")
    table.add_column("Model", style="green")
    for i, m in enumerate(models, 1):
        table.add_row(str(i), m)
    console.print(table)

    choice = Prompt.ask(f"[yellow]Pilih nomor atau nama model[/yellow]", default=config.model)
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            return models[idx]
        return None
    return choice


def _handle_slash_command(agent, cmd: str, config: Config, recreate_agent=None):
    parts = cmd.split()
    command = parts[0].lower()

    if command == "/clear":
        agent.reset()
        _print_welcome(config)
        console.print("[dim]Percakapan direset[/dim]")

    elif command == "/help":
        console.print(Panel("""[bold]Slash Commands[/bold]

  [cyan]/login[/cyan]         Set API key + pilih provider & model
  [cyan]/provider[/cyan]      Ganti provider AI
  [cyan]/model[/cyan]         Ganti model AI
  [cyan]/effort[/cyan]        Set effort: low/medium/high
  [cyan]/clear[/cyan]         Reset percakapan
  [cyan]/cost[/cyan]          Lihat pemakaian token & biaya
  [cyan]/tokens[/cyan]        Statistik konteks
  [cyan]/save[/cyan]          Simpan sesi ini
  [cyan]/sessions[/cyan]      Daftar/resume/delete sesi
  [cyan]/allow[/cyan]         Izinkan tool tanpa konfirmasi (proyek ini)
  [cyan]/deny[/cyan]          Tolak tool (proyek ini)
  [cyan]/project[/cyan]       Lihat config proyek
  [cyan]/export[/cyan]        Export chat ke file .md
  [cyan]/social[/cyan]        Cek status & connect social (Twitter, Telegram, Discord)
  [cyan]/update[/cyan]        Update Faresta Code ke versi terbaru
  [cyan]exit/quit[/cyan]      Keluar""", title="Help", box=box.ROUNDED, border_style="cyan"))

    elif command == "/login":
        _print_welcome(config)
        console.print(Panel("[bold cyan]Login — Setup Provider & API Key[/bold cyan]", box=box.MINIMAL, border_style="cyan"))
        console.print("")

        p = _pick_provider(config, "Pilih Provider")
        if not p:
            print_error("Provider tidak valid")
            _print_status_bar(agent, config)
            return

        defaults = PROVIDER_DEFAULTS[p]
        env_key = defaults["env_key"]

        console.print(f"[yellow]Env: {env_key}[/yellow]")
        config.provider = p
        config.model = defaults["model"]

        api = Prompt.ask(f"[yellow]API Key untuk {p}[/yellow]", password=True)
        while not api:
            print_warning("API Key wajib diisi")
            api = Prompt.ask(f"[yellow]API Key untuk {p}[/yellow]", password=True)

        config.api_key = api
        save_config(config)

        m = _pick_model(config)
        if m:
            config.model = m
        save_config(config)

        if recreate_agent:
            recreate_agent()
        _print_status_bar(agent, config)

    elif command == "/provider":
        _print_welcome(config)
        console.print(Panel("[bold cyan]Ganti Provider[/bold cyan]", box=box.MINIMAL, border_style="cyan"))
        console.print("")

        p = _pick_provider(config, "Pilih Provider")
        if not p:
            print_error("Provider tidak valid")
            _print_status_bar(agent, config)
            return

        defaults = PROVIDER_DEFAULTS[p]
        env_key = defaults["env_key"]

        import os
        has_key = bool(config.api_key) or bool(os.getenv(env_key))

        if not has_key:
            console.print(f"[yellow]Provider {p} butuh API Key ({env_key})[/yellow]")
            api = Prompt.ask(f"[yellow]API Key untuk {p}[/yellow]", password=True)
            while not api:
                print_warning("API Key wajib diisi")
                api = Prompt.ask(f"[yellow]API Key untuk {p}[/yellow]", password=True)
            config.api_key = api

        config.provider = p
        config.model = defaults["model"]

        m = _pick_model(config)
        if m:
            config.model = m
        save_config(config)

        if recreate_agent:
            recreate_agent()
        _print_status_bar(agent, config)

    elif command == "/model":
        _print_welcome(config)
        console.print(Panel(f"[bold cyan]Ganti Model — {config.provider}[/bold cyan]", box=box.MINIMAL, border_style="cyan"))
        console.print("")

        m = _pick_model(config)
        if m:
            config.model = m
            save_config(config)
            if recreate_agent:
                recreate_agent()
            console.print(f"[green]✓ Model: {config.model}[/green]")
        else:
            print_error("Model tidak valid")
        _print_status_bar(agent, config)

    elif command == "/cost":
        console.print(f"[cyan]biaya:[/cyan] {agent.cost_tracker.summary()}")
        _print_status_bar(agent, config)

    elif command == "/effort":
        choices = ["low", "medium", "high"]
        table = Table(title="Pilih Effort Level", box=box.SIMPLE, header_style="cyan")
        table.add_column("No", style="dim")
        table.add_column("Level", style="yellow")
        table.add_column("Deskripsi", style="green")
        table.add_row("1", "low",    "Respon cepat, lebih murah")
        table.add_row("2", "medium", "Seimbang (default)")
        table.add_row("3", "high",   "Lebih teliti, berpikir lebih lama")
        console.print(table)

        choice = Prompt.ask("[yellow]Pilih effort[/yellow]", default=config.effort)
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(choices):
                choice = choices[idx]
        if choice in choices:
            config.effort = choice
            save_config(config)
            _print_status_bar(agent, config)
        else:
            console.print("[red]Pilihan tidak valid. Pilih: low, medium, high[/red]")

    elif command == "/tokens":
        total_chars = sum(len(m.get("content", "")) for m in agent.messages)
        tool_count = len([m for m in agent.messages if m["role"] == "tool"])
        msg_count = len(agent.messages)
        console.print(f"[cyan]context:[/cyan] {msg_count} pesan, ~{total_chars} chars, {tool_count} tool calls, {agent.cost_tracker.rounds} putaran")
        _print_status_bar(agent, config)

    elif command == "/save":
        _save_session(agent)
        console.print(f"[green]✓ Sesi tersimpan: {agent.session_id}[/green]")
        _print_status_bar(agent, config)

    elif command == "/sessions":
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        sessions = sorted(SESSION_DIR.glob("*.json"))
        if not sessions:
            console.print("[dim]Belum ada sesi tersimpan[/dim]")
            _print_status_bar(agent, config)
            return
        table = Table(title="Sesi Tersimpan", box=box.SIMPLE, header_style="cyan")
        table.add_column("No", style="dim")
        table.add_column("ID", style="dim")
        table.add_column("Tanggal", style="yellow")
        table.add_column("Pesan")
        table.add_column("Biaya")
        for i, s in enumerate(sessions, 1):
            try:
                data = json.loads(s.read_text())
                msgs = len(data.get("messages", []))
                date = datetime.fromtimestamp(int(s.stem)).strftime("%Y-%m-%d %H:%M")
                cost = f"${data.get('total_cost', 0):.4f}"
                table.add_row(str(i), s.stem, date, str(msgs), cost)
            except Exception:
                pass
        console.print(table)
        console.print("[dim]Resume: faresta chat --resume <id>  |  Hapus: /delete <id>[/dim]")
        _print_status_bar(agent, config)

    elif command == "/delete":
        if len(parts) < 2:
            print_warning("Gunakan: /delete <session_id>")
            _print_status_bar(agent, config)
            return
        session_id = parts[1]
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            session_file.unlink()
            console.print(f"[green]✓ Session {session_id} dihapus[/green]")
        else:
            print_error(f"Session '{session_id}' tidak ditemukan")
        _print_status_bar(agent, config)

    elif command == "/export":
        path = parts[1] if len(parts) > 1 else f"faresta-chat-{agent.session_id}.md"
        _export_chat(agent, config, path)
        _print_status_bar(agent, config)

    elif command == "/social":
        import os as _os
        socials = {
            "🐦 Twitter/X": {
                "TWITTER_BEARER_TOKEN": _os.getenv("TWITTER_BEARER_TOKEN", ""),
                "TWITTER_API_KEY": _os.getenv("TWITTER_API_KEY", ""),
            },
            "✈ Telegram": {
                "TELEGRAM_BOT_TOKEN": _os.getenv("TELEGRAM_BOT_TOKEN", ""),
            },
            "💬 Discord": {
                "DISCORD_WEBHOOK_URL": _os.getenv("DISCORD_WEBHOOK_URL", ""),
            },
        }
        table = Table(title="Social Connections", box=box.SIMPLE, header_style="cyan")
        table.add_column("Platform", style="yellow")
        table.add_column("Status", style="green")
        table.add_column("Env Vars")
        for name, vars in socials.items():
            configured = all(v for v in vars.values())
            status = "[green]✓ Connected[/green]" if configured else "[dim]Not set[/dim]"
            env_list = ", ".join(vars.keys())
            table.add_row(name, status, env_list)
        console.print(table)
        console.print("[dim]Set env vars di shell sebelum menjalankan faresta, atau:\n  export TWITTER_BEARER_TOKEN=...\n  export TELEGRAM_BOT_TOKEN=...\n  export DISCORD_WEBHOOK_URL=...[/dim]")
        _print_status_bar(agent, config)

    elif command == "/update":
        _exit_alt_screen()
        import subprocess, sys, os
        install_dir = os.environ.get("FARESTA_DIR") or os.path.expanduser("~/.faresta")
        console.print("[cyan]Update Faresta Code...[/cyan]")
        git_ok = True
        try:
            subprocess.run(["git", "-C", install_dir, "pull", "--ff-only"], check=True, capture_output=True, timeout=30)
            console.print("[green]✓ Git pull berhasil[/green]")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode()[:200]
            print_warning(f"Git pull: {err}")
            git_ok = False
        except FileNotFoundError:
            print_warning("Git tidak ditemukan, skip pull")
            git_ok = False
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-e", install_dir, "--quiet"], check=True, capture_output=True, timeout=120)
            print_success("Update berhasil! Restart chat untuk menggunakan versi baru.")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode()[:300]
            print_error(f"Install gagal: {err}")
            if "permission" in err.lower() or "denied" in err.lower():
                console.print("[yellow]  Coba: sudo chown -R $(whoami) ~/.faresta[/yellow]")
                console.print("[yellow]  Atau: sudo chmod -R +x ~/.faresta/venv/bin/*[/yellow]")
            console.print("[dim]  Atau jalankan manual: python3 -m pip install -e ~/.faresta --user[/dim]")
        input("[Enter] untuk kembali...")
        _enter_alt_screen()
        _print_welcome(config)

    elif command in ("/project", "/project-config"):
        proj = agent.project_config
        console.print(Panel(f"""[bold]Project Config (faresta.json)[/bold]

  Provider:    {proj.default_provider or '(not set)'}
  Model:       {proj.default_model or '(not set)'}
  Allow:       {', '.join(proj.permissions.allow) if proj.permissions.allow else '-'}
  Deny:        {', '.join(proj.permissions.deny) if proj.permissions.deny else '-'}""", box=box.ROUNDED, border_style="cyan"))
        _print_status_bar(agent, config)

    elif command == "/allow":
        if len(parts) < 2:
            print_warning("Gunakan: /allow <tool_name>")
            _print_status_bar(agent, config)
            return
        tool_name = parts[1]
        proj = agent.project_config
        if tool_name in proj.permissions.deny:
            proj.permissions.deny.remove(tool_name)
        if tool_name not in proj.permissions.allow:
            proj.permissions.allow.append(tool_name)
        proj.save()
        agent.project_config = proj
        console.print(f"[green]✓ Tool '{tool_name}' diizinkan tanpa konfirmasi[/green]")
        _print_status_bar(agent, config)

    elif command == "/deny":
        if len(parts) < 2:
            print_warning("Gunakan: /deny <tool_name>")
            _print_status_bar(agent, config)
            return
        tool_name = parts[1]
        proj = agent.project_config
        if tool_name in proj.permissions.allow:
            proj.permissions.allow.remove(tool_name)
        if tool_name not in proj.permissions.deny:
            proj.permissions.deny.append(tool_name)
        proj.save()
        agent.project_config = proj
        console.print(f"[green]✓ Tool '{tool_name}' ditolak[/green]")
        _print_status_bar(agent, config)

    else:
        console.print(f"[red]Perintah '{command}' tidak dikenal. Ketik /help[/red]")
        _print_status_bar(agent, config)


def _export_chat(agent, config, path):
    lines = []
    lines.append(f"# Faresta Code Chat — {config.provider}/{config.model}")
    lines.append(f"")
    for msg in agent.messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user" and content:
            lines.append(f"## User\n\n{content}\n")
        elif role == "assistant" and content:
            lines.append(f"## Faresta\n\n{content}\n")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print_success(f"Chat diexport ke {path}")


def _save_session(agent):
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "session_id": agent.session_id,
        "messages": agent.messages,
        "total_input_tokens": agent.cost_tracker.total_input_tokens,
        "total_output_tokens": agent.cost_tracker.total_output_tokens,
        "total_cost": agent.cost_tracker.total_cost,
        "rounds": agent.cost_tracker.rounds,
        "timestamp": datetime.now().isoformat(),
    }
    session_file = SESSION_DIR / f"{agent.session_id}.json"
    session_file.write_text(json.dumps(data, indent=2))


@main.command()
def config_show():
    """Show current configuration."""
    config = load_config()
    proj = ProjectConfig.load()

    console.print("[bold cyan]Faresta Code Configuration[/bold cyan]")
    console.print(f"  Provider:     {config.provider}")
    console.print(f"  Model:        {config.model}")
    console.print(f"  Temperature:  {config.temperature}")
    console.print(f"  Max Tokens:   {config.max_tokens}")
    console.print(f"  Effort:       {config.effort}")
    console.print(f"  Tool Confirm: {config.tool_confirm}")
    console.print(f"  API Key:      {'[green]✓ Set[/green]' if config.api_key else '[red]✖ Not set[/red]'}")

    if proj.default_provider or proj.default_model:
        console.print("\n[bold cyan]Project Config (faresta.json)[/bold cyan]")
        console.print(f"  Provider: {proj.default_provider or '-'}")
        console.print(f"  Model:    {proj.default_model or '-'}")


@main.command()
@click.option("--provider", help="LLM provider")
@click.option("--model", help="Model name")
@click.option("--api-key", help="API key")
@click.option("--temperature", type=float, help="Temperature (0-2)")
@click.option("--max-tokens", type=int, help="Max tokens")
@click.option("--system-prompt", help="System prompt")
@click.option("--tool-confirm/--no-tool-confirm", help="Enable/disable tool confirmation")
@click.option("--effort", type=click.Choice(["low", "medium", "high"]), help="Effort level")
def config_set(provider, model, api_key, temperature, max_tokens, system_prompt, tool_confirm, effort):
    """Set configuration values."""
    config = load_config()
    if provider:
        config.provider = provider
    if model:
        config.model = model
    if api_key:
        config.api_key = api_key
    if temperature is not None:
        config.temperature = temperature
    if max_tokens is not None:
        config.max_tokens = max_tokens
    if system_prompt:
        config.system_prompt = system_prompt
    if tool_confirm is not None:
        config.tool_confirm = tool_confirm
    if effort:
        config.effort = effort

    save_config(config)
    print_success("Configuration saved")


@main.command()
@click.argument("action", type=click.Choice(["init", "show", "allow", "deny"]))
@click.argument("tool_name", required=False)
def project(action, tool_name):
    """Manage project-level faresta.json config."""
    proj = ProjectConfig.load()

    if action == "init":
        if not tool_name:
            proj.save()
            print_success(f"Created {Path.cwd() / 'faresta.json'}")
        else:
            proj.default_provider = tool_name
            proj.save()
            print_success(f"Created faresta.json with default provider: {tool_name}")

    elif action == "show":
        console.print(proj.model_dump_json(indent=2))

    elif action == "allow":
        if not tool_name:
            print_error("Tool name required")
            return
        if tool_name in proj.permissions.deny:
            proj.permissions.deny.remove(tool_name)
        if tool_name not in proj.permissions.allow:
            proj.permissions.allow.append(tool_name)
        proj.save()
        print_success(f"Tool '{tool_name}' allowed without confirmation")

    elif action == "deny":
        if not tool_name:
            print_error("Tool name required")
            return
        if tool_name in proj.permissions.allow:
            proj.permissions.allow.remove(tool_name)
        if tool_name not in proj.permissions.deny:
            proj.permissions.deny.append(tool_name)
        proj.save()
        print_success(f"Tool '{tool_name}' denied")


@main.command()
@click.argument("session_id", required=False)
def session(session_id):
    """List, show, or resume sessions."""
    if session_id:
        session_file = SESSION_DIR / f"{session_id}.json"
        if session_file.exists():
            data = json.loads(session_file.read_text())
            console.print(f"[bold cyan]Session: {session_id}[/bold cyan]")
            console.print(f"  Messages: {len(data.get('messages', []))}")
            console.print(f"  Cost: ${data.get('total_cost', 0):.4f}")
            console.print(f"  Rounds: {data.get('rounds', 0)}")
            console.print(f"  Resume with: [yellow]faresta chat --resume {session_id}[/yellow]")
        else:
            print_error(f"Session '{session_id}' not found")
        return

    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    sessions = sorted(SESSION_DIR.glob("*.json"))
    if not sessions:
        print_info("No saved sessions")
        return
    console.print("[bold cyan]Saved Sessions[/bold cyan]")
    for s in sessions:
        try:
            data = json.loads(s.read_text())
            msgs = len(data.get("messages", []))
            date = datetime.fromtimestamp(int(s.stem)).strftime("%Y-%m-%d %H:%M")
            cost = data.get("total_cost", 0)
            console.print(f"  {s.stem} — {date} ({msgs} msgs, ${cost:.4f})")
        except Exception:
            console.print(f"  {s.stem}")


if __name__ == "__main__":
    main()