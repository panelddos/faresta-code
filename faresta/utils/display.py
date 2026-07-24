from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.syntax import Syntax
from rich import box

console = Console()


def print_welcome():
    title = "[bold cyan]Faresta Code[/bold cyan] — AI Coding Assistant"
    subtitle = "[dim]Multi-provider LLM CLI • Agentic mode with tools[/dim]"
    console.print(Panel(f"{title}\n{subtitle}", box=box.ROUNDED, border_style="cyan"))


def print_markdown(text: str):
    console.print(Markdown(text))


def print_error(msg: str):
    console.print(f"[red]✖ {msg}[/red]")


def print_info(msg: str):
    console.print(f"[dim]ℹ {msg}[/dim]")


def print_success(msg: str):
    console.print(f"[green]✓ {msg}[/green]")


def print_warning(msg: str):
    console.print(f"[yellow]⚠ {msg}[/yellow]")


def input_user(prompt: str = "You") -> str:
    return Prompt.ask(f"[bold yellow]{prompt}[/bold yellow]")
