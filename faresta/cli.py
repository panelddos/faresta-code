import sys
import json
import click
from pathlib import Path
from datetime import datetime
from rich.prompt import Prompt
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
    print_info, print_success, input_user,
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
        )

    if config.provider in COMPATIBLE_PROVIDERS:
        return create_provider(
            name=config.provider,
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    known = ", ".join(list(providers.keys()) + list(COMPATIBLE_PROVIDERS.keys()))
    print_error(f"Unknown provider '{config.provider}'. Available: {known}")
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


@main.command()
@click.option("-p", "--provider", help="LLM provider (openai, anthropic, google)")
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
            print_success(f"Resumed session {resume} ({len(agent.messages)} messages)")
        else:
            print_error(f"Session '{resume}' not found")
            agent.add_system_prompt()
    else:
        agent.add_system_prompt()

    print_welcome()
    print_info(f"Provider: {config.provider} | Model: {config.model}")
    print_info(f"Tools: {len(agent.registry)} registered")
    if not config.api_key:
        print_warning("API key belum di-set! Ketik /login untuk setup")
    print_info("Type 'exit' or 'quit' to end")
    print_info("Slash commands: /login, /model, /provider, /clear, /help, /cost, /tokens, /save, /sessions, /project-config")
    print()

    def recreate_agent():
        nonlocal llm, agent
        llm = get_provider(config)
        history = agent.messages if agent.messages and agent.messages[0].get("role") != "system" else []
        agent = Agent(llm, config)
        agent.add_system_prompt()
        print_success(f"Provider aktif: {config.provider} / {config.model}")

    while True:
        user_input = input_user()
        if user_input.lower() in ("exit", "quit"):
            _save_session(agent)
            print_info("Goodbye!")
            break

        if user_input.strip().startswith("/"):
            _handle_slash_command(agent, user_input.strip(), config, recreate_agent)
            continue

        if not user_input.strip():
            continue

        with console.status("[bold cyan]Thinking...[/bold cyan]", spinner="dots"):
            try:
                response = agent.run(user_input)
            except Exception as e:
                print_error(str(e))
                continue

        if response:
            print_markdown(response)

        tool_count = len([m for m in agent.messages if m["role"] == "tool"])
        if tool_count > 0:
            print_info(f"Tools used this round")
        print()


def _handle_slash_command(agent, cmd: str, config: Config, recreate_agent=None):
    parts = cmd.split()
    command = parts[0].lower()
    args = parts[1:]

    if command == "/clear":
        agent.reset()
        print_success("Context cleared")

    elif command == "/help":
        console.print("[bold cyan]Faresta Code Commands[/bold cyan]")
        console.print("  [yellow]/login[/yellow]       Set API key, provider, and model interactively")
        console.print("  [yellow]/provider[/yellow]    Switch provider (openai, anthropic, google, groq, xai, nvidia, deepseek, mistral, together, openrouter)")
        console.print("  [yellow]/model[/yellow]       Change model (e.g. /model gpt-4o, /model claude-sonnet-4-20250514)")
        console.print("  [yellow]/clear[/yellow]       Reset conversation context")
        console.print("  [yellow]/cost[/yellow]        Show token usage and cost")
        console.print("  [yellow]/tokens[/yellow]      Show token count in current context")
        console.print("  [yellow]/save[/yellow]        Save current session")
        console.print("  [yellow]/sessions[/yellow]    List saved sessions")
        console.print("  [yellow]/project-config[/yellow]  Show project config (faresta.json)")
        console.print("  [yellow]exit/quit[/yellow]    End session")

    elif command == "/login":
        provider_list = "openai, anthropic, google, groq, xai, nvidia, deepseek, mistral, together, openrouter"
        p = Prompt.ask(f"[yellow]Pilih provider[/yellow]", default=config.provider)
        if p in PROVIDER_DEFAULTS:
            config.provider = p
            api = Prompt.ask(f"[yellow]API Key untuk {p}[/yellow]", password=True)
            if api:
                config.api_key = api
            save_config(config)
            print_success(f"Provider: {p} | API Key: {'✓ tersimpan' if api else '(pakai env var yang sudah ada)'}")
            if recreate_agent:
                recreate_agent()
            print_info(f"Sekarang pakai: {config.provider} / {config.model}")
        else:
            print_error(f"Provider '{p}' tidak dikenal. Pilih: {provider_list}")

    elif command == "/provider":
        provider_list = "openai, anthropic, google, groq, xai, nvidia, deepseek, mistral, together, openrouter"
        p = Prompt.ask(f"[yellow]Ganti provider[/yellow]", default=config.provider)
        if p in PROVIDER_DEFAULTS:
            config.provider = p
            defaults = PROVIDER_DEFAULTS[p]
            config.model = defaults["model"]
            save_config(config)
            print_success(f"Provider diganti ke: {p} / {config.model}")
            if recreate_agent:
                recreate_agent()
        else:
            print_error(f"Provider '{p}' tidak dikenal. Pilih: {provider_list}")

    elif command == "/model":
        defaults = PROVIDER_DEFAULTS.get(config.provider, {})
        if args:
            model = args[0]
        else:
            model = Prompt.ask(f"[yellow]Nama model untuk {config.provider}[/yellow]", default=defaults.get("model", ""))
        if model:
            config.model = model
            save_config(config)
            print_success(f"Model diganti ke: {model}")
            if recreate_agent:
                recreate_agent()

    elif command == "/cost":
        print_info(agent.cost_tracker.summary())

    elif command == "/tokens":
        total_chars = sum(len(m.get("content", "")) for m in agent.messages)
        tool_count = len([m for m in agent.messages if m["role"] == "tool"])
        msg_count = len(agent.messages)
        console.print(f"[cyan]Context stats:[/cyan] {msg_count} messages, ~{total_chars} chars, {tool_count} tool results, {agent.cost_tracker.rounds} rounds")

    elif command == "/save":
        _save_session(agent)
        print_success(f"Session saved: {agent.session_id}")

    elif command == "/sessions":
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
                console.print(f"  {s.stem} — {date} ({msgs} messages)")
            except Exception:
                console.print(f"  {s.stem}")

    elif command == "/project-config":
        proj = agent.project_config
        console.print("[bold cyan]Project Config (faresta.json)[/bold cyan]")
        console.print(f"  Default provider: {proj.default_provider or '(not set)'}")
        console.print(f"  Default model:    {proj.default_model or '(not set)'}")
        console.print(f"  Permissions:      allow={proj.permissions.allow}, deny={proj.permissions.deny}")
        console.print(f"  Test command:     {proj.test_command or '(auto-detect)'}")

    else:
        print_error(f"Unknown command: {command}. Type /help for commands.")


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
def config_set(provider, model, api_key, temperature, max_tokens, system_prompt, tool_confirm):
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