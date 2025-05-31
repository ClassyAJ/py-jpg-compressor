import logging
from rich.console import Console
from rich.logging import RichHandler

console = Console(stderr=True)

logging.basicConfig(
    level="INFO",
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
)
logger: logging.Logger = logging.getLogger(name="image_tool")


def print_error(message: str) -> None:
    """prints errors"""
    console.print(f"[bold red]Error:[/bold red] {message}")


def print_warning(message: str) -> None:
    """prints warnings"""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def print_info(message: str) -> None:
    """prints infos"""
    logger.info(message)


def print_success(message: str) -> None:
    """prints successes"""
    console.print(f"[bold green]Success:[/bold green] {message}")


def print_rule(title: str) -> None:
    """prints rule style string with borders"""
    console.rule(title=f"[bold cyan]{title}[/bold cyan]")
