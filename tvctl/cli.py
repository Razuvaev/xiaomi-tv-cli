from __future__ import annotations

import ipaddress

import typer
from rich.console import Console
from rich.table import Table

from tvctl import adb

app = typer.Typer(
    name="tvctl",
    help="Diagnose and optimize Xiaomi Android TV devices over ADB.",
    no_args_is_help=True,
)

console = Console()


def validate_ip_address(ip_address: str) -> str:
    try:
        return str(ipaddress.ip_address(ip_address))
    except ValueError as error:
        raise typer.BadParameter("Enter a valid IPv4 or IPv6 address.") from error


@app.command()
def version() -> None:
    """Show the installed tvctl version."""
    console.print("[bold cyan]xiaomi-tv-cli[/bold cyan] [green]0.1.0[/green]")


@app.command()
def hello() -> None:
    """Check that the CLI is installed correctly."""
    console.print("[bold green]✓ Xiaomi TV CLI is ready[/bold green]")


@app.command()
def connect(
    ip_address: str = typer.Argument(
        ...,
        callback=validate_ip_address,
        help="TV IP address, for example 192.168.1.40.",
    ),
    port: int = typer.Option(5555, min=1, max=65535, help="ADB TCP port."),
) -> None:
    """Connect to a TV over Wi-Fi using ADB."""
    target = f"{ip_address}:{port}"

    console.print(f"[cyan]Connecting to {target}...[/cyan]")

    try:
        result = adb.connect(ip_address, port)
    except adb.ADBError as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    output = result.output.lower()

    if "already connected" in output:
        console.print(f"[bold green]✓ Already connected to {target}[/bold green]")
        return

    if "connected to" in output:
        console.print(f"[bold green]✓ Connected to {target}[/bold green]")
        return

    if "failed to authenticate" in output:
        console.print(
            "[yellow]⚠ Approve the debugging request on the TV, "
            "then run the command again.[/yellow]"
        )
        raise typer.Exit(code=2)

    console.print(f"[bold red]✗ Could not connect to {target}[/bold red]")

    if result.output:
        console.print(result.output)

    raise typer.Exit(code=result.return_code or 1)

@app.command()
def status() -> None:
    """Show information about the connected Android TV device."""
    try:
        devices_result = adb.devices()
    except adb.ADBError as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    connected_devices = []

    for line in devices_result.stdout.splitlines()[1:]:
        columns = line.split()

        if len(columns) >= 2 and columns[1] == "device":
            connected_devices.append(columns[0])

    if not connected_devices:
        console.print("[yellow]⚠ No connected Android TV devices found.[/yellow]")
        console.print("Run [cyan]tvctl connect <IP>[/cyan] first.")
        raise typer.Exit(code=1)

    if len(connected_devices) > 1:
        console.print("[yellow]⚠ Multiple ADB devices are connected.[/yellow]")
        console.print("Disconnect unnecessary devices and run the command again.")
        raise typer.Exit(code=1)

    try:
        model = adb.get_property("ro.product.model") or "Unknown"
        manufacturer = adb.get_property("ro.product.manufacturer") or "Unknown"
        android_version = adb.get_property("ro.build.version.release") or "Unknown"
        sdk_version = adb.get_property("ro.build.version.sdk") or "Unknown"
        launcher = adb.get_home_launcher()
    except adb.ADBError as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    table = Table(title="Android TV Status", show_header=False)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Device", connected_devices[0])
    table.add_row("Manufacturer", manufacturer)
    table.add_row("Model", model)
    table.add_row("Android", android_version)
    table.add_row("SDK", sdk_version)
    table.add_row("Home launcher", launcher)

    console.print(table)    


if __name__ == "__main__":
    app()
