import sys
import click
from .config import load_config, save_config, Config
from .llm.base import LLMProvider
from .llm.openai_provider import OpenAIProvider
from .llm.anthropic_provider import AnthropicProvider
from .llm.google_provider import GoogleProvider
from .utils.display import (
    console, print_welcome, print_markdown, print_error,
    print_info, print_success, input_user,
)


def get_provider(config: Config) -> LLMProvider:
    if not config.api_key:
        print_error(f"No API key found for provider '{config.provider}'. Set FARESTA_API_KEY or {config.provider.upper()}_API_KEY.")
        sys.exit(1)

    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "google": GoogleProvider,
    }
    cls = providers.get(config.provider)
    if not cls:
        print_error(f"Unknown provider '{config.provider}'. Use: openai, anthropic, google")
        sys.exit(1)

    return cls(
        api_key=config.api_key,
        model=config.model,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )


@click.group()
@click.version_option(version="0.1.0", prog_name="faresta")
def main():
    pass


@main.command()
@click.argument("question", required=False)
@click.option("-p", "--provider", help="LLM provider (openai, anthropic, google)")
@click.option("-m", "--model", help="Model name")
def ask(question, provider, model):
    """Ask a single question and get an answer."""
    config = load_config()
    if provider:
        config.provider = provider
    if model:
        config.model = model

    llm = get_provider(config)
    msgs = [{"role": "system", "content": config.system_prompt}]

    if not question:
        question = input_user("Question")

    msgs.append({"role": "user", "content": question})
    console.print("[dim]Faresta:[/dim] ", end="")
    full = ""
    for chunk in llm.chat(msgs):
        print(chunk, end="", flush=True)
        full += chunk
    print()
    print()
    print_info(f"Provider: {config.provider} | Model: {config.model}")


@main.command()
@click.option("-p", "--provider", help="LLM provider (openai, anthropic, google)")
@click.option("-m", "--model", help="Model name")
def chat(provider, model):
    """Start an interactive chat session."""
    config = load_config()
    if provider:
        config.provider = provider
    if model:
        config.model = model

    llm = get_provider(config)
    messages = [{"role": "system", "content": config.system_prompt}]

    print_welcome()
    print_info(f"Provider: {config.provider} | Model: {config.model}")
    print_info("Type 'exit' or 'quit' to end, '/clear' to clear history")
    print()

    while True:
        user_input = input_user()
        if user_input.lower() in ("exit", "quit"):
            print_info("Goodbye!")
            break
        if user_input.strip() == "/clear":
            messages = [{"role": "system", "content": config.system_prompt}]
            print_success("History cleared")
            continue
        if not user_input.strip():
            continue

        messages.append({"role": "user", "content": user_input})
        console.print("[dim]Faresta:[/dim] ")

        full = ""
        try:
            for chunk in llm.chat(messages):
                print(chunk, end="", flush=True)
                full += chunk
        except Exception as e:
            print_error(str(e))
            messages.pop()
            continue

        messages.append({"role": "assistant", "content": full})
        print()
        print()


@main.command()
def config_show():
    """Show current configuration."""
    config = load_config()
    console.print("[bold cyan]Faresta Code Configuration[/bold cyan]")
    console.print(f"  Provider:     {config.provider}")
    console.print(f"  Model:        {config.model}")
    console.print(f"  Temperature:  {config.temperature}")
    console.print(f"  Max Tokens:   {config.max_tokens}")
    console.print(f"  API Key:      {'[green]✓ Set[/green]' if config.api_key else '[red]✖ Not set[/red]'}")


@main.command()
@click.option("--provider", help="LLM provider")
@click.option("--model", help="Model name")
@click.option("--api-key", help="API key")
@click.option("--temperature", type=float, help="Temperature (0-2)")
@click.option("--max-tokens", type=int, help="Max tokens")
@click.option("--system-prompt", help="System prompt")
def config_set(provider, model, api_key, temperature, max_tokens, system_prompt):
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

    save_config(config)
    print_success("Configuration saved")


if __name__ == "__main__":
    main()
