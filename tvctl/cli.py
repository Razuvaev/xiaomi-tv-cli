import typer
from rich.console import Console

app = typer.Typer(
    name="tvctl",
    help="Diagnose and optimize Xiaomi Android TV devices over ADB.",
    no_args_is_help=True,
)

console = Console()


@app.command()
def version() -> None:
    """Show the installed tvctl version."""
    console.print("[bold cyan]xiaomi-tv-cli[/bold cyan] [green]0.1.0[/green]")


@app.command()
def hello() -> None:
    """Check that the CLI is installed correctly."""
    console.print("[bold green]✓ Xiaomi TV CLI is ready[/bold green]")


if __name__ == "__main__":
    app()
