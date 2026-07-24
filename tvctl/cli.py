from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tvctl import adb, discovery, doctor, optimizer, restorer
from tvctl.profiles import ProfileError

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

@app.command(name="doctor")
def doctor_command(
    profile: Annotated[
        Path,
        typer.Option(
            "--profile",
            "-p",
            help="Path to an optimization profile.",
        ),
    ] = Path("profiles/safe.yaml"),
) -> None:
    """Check optimization status and show a health score."""
    try:
        report = doctor.run(profile)
    except (adb.ADBError, ProfileError) as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    table = Table(title=f"{report.profile.name} profile")
    table.add_column("Status")
    table.add_column("Component")
    table.add_column("Category")
    table.add_column("Package", style="dim")

    for result in report.packages:
        if not result.installed:
            status = "[dim]— Not installed[/dim]"
        elif result.enabled:
            status = "[yellow]⚠ Enabled[/yellow]"
        else:
            status = "[green]✓ Disabled[/green]"

        table.add_row(
            status,
            result.title,
            result.category,
            result.name,
        )

    console.print(table)

    score_color = "green" if report.score >= 90 else "yellow" if report.score >= 60 else "red"

    console.print(
        Panel(
            f"[bold {score_color}]{report.score} / 100[/bold {score_color}]\n"
            f"{report.optimized_count} of {len(report.packages)} components optimized",
            title="Optimization score",
        )
    )

    if report.score < 100:
        console.print("Run [cyan]tvctl optimize[/cyan] to apply this profile.")

@app.command()
def optimize(
    profile: Annotated[
        Path,
        typer.Option(
            "--profile",
            "-p",
            help="Path to an optimization profile.",
        ),
    ] = Path("profiles/safe.yaml"),
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Apply changes without asking for confirmation.",
        ),
    ] = False,
) -> None:
    """Disable unnecessary packages from an optimization profile."""
    try:
        loaded_profile = optimizer.load_profile(profile)
        enabled_packages = optimizer.get_enabled_packages(loaded_profile)
    except (adb.ADBError, ProfileError) as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    if not enabled_packages:
        console.print("[bold green]✓ Nothing to optimize. Profile is already applied.[/bold green]")
        return

    table = Table(title=f"{loaded_profile.name} optimization")
    table.add_column("Component")
    table.add_column("Category")
    table.add_column("Package", style="dim")

    for profile_package in enabled_packages:
        table.add_row(
            profile_package.title,
            profile_package.category,
            profile_package.name,
        )

    console.print(table)
    console.print(f"[yellow]{len(enabled_packages)} packages will be disabled.[/yellow]")

    if not yes and not typer.confirm("Continue?"):
        console.print("[yellow]Optimization cancelled.[/yellow]")
        raise typer.Exit()

    try:
        results = optimizer.run(profile)
    except (adb.ADBError, ProfileError) as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    failed_count = 0

    for result in results:
        if result.success:
            console.print(f"[green]✓ Disabled {result.package.title}[/green]")
        else:
            failed_count += 1
            console.print(f"[red]✗ Failed to disable {result.package.title}[/red]")
            console.print(f"[dim]{result.message}[/dim]")

    if failed_count:
        console.print(f"[bold red]Completed with {failed_count} errors.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ Optimization completed successfully.[/bold green]")

@app.command()
def restore(
    profile: Annotated[
        Path,
        typer.Option(
            "--profile",
            "-p",
            help="Path to an optimization profile.",
        ),
    ] = Path("profiles/safe.yaml"),
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Restore packages without asking for confirmation.",
        ),
    ] = False,
) -> None:
    """Enable packages previously disabled by an optimization profile."""
    try:
        loaded_profile = restorer.load_profile(profile)
        disabled_packages = restorer.get_disabled_packages(loaded_profile)
    except (adb.ADBError, ProfileError) as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    if not disabled_packages:
        console.print("[bold green]✓ Nothing to restore.[/bold green]")
        return

    table = Table(title=f"{loaded_profile.name} restore")
    table.add_column("Component")
    table.add_column("Category")
    table.add_column("Package", style="dim")

    for profile_package in disabled_packages:
        table.add_row(
            profile_package.title,
            profile_package.category,
            profile_package.name,
        )

    console.print(table)
    console.print(f"[yellow]{len(disabled_packages)} packages will be enabled.[/yellow]")

    if not yes and not typer.confirm("Continue?"):
        console.print("[yellow]Restore cancelled.[/yellow]")
        raise typer.Exit()

    try:
        results = restorer.run(profile)
    except (adb.ADBError, ProfileError) as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    failed_count = 0

    for result in results:
        if result.success:
            console.print(f"[green]✓ Enabled {result.package.title}[/green]")
        else:
            failed_count += 1
            console.print(f"[red]✗ Failed to enable {result.package.title}[/red]")
            console.print(f"[dim]{result.message}[/dim]")

    if failed_count:
        console.print(f"[bold red]Completed with {failed_count} errors.[/bold red]")
        raise typer.Exit(code=1)

    console.print("[bold green]✓ Restore completed successfully.[/bold green]")    

@app.command()
def discover(
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            min=1,
            max=65535,
            help="ADB TCP port.",
        ),
    ] = discovery.DEFAULT_ADB_PORT,
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            min=0.05,
            max=5,
            help="Connection timeout for each IP address.",
        ),
    ] = discovery.DEFAULT_TIMEOUT,
) -> None:
    """Find Android TV devices with wireless ADB enabled."""
    try:
        network = discovery.get_default_network()
    except discovery.DiscoveryError as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    console.print(f"[cyan]Scanning {network} on port {port}...[/cyan]")

    try:
        devices = discovery.discover(
            network=network,
            port=port,
            timeout=timeout,
        )
        if devices:
            console.print("[cyan]Reading device information...[/cyan]")
            devices = discovery.identify_devices(devices)
    except discovery.DiscoveryError as error:
        console.print(f"[bold red]✗ {error}[/bold red]")
        raise typer.Exit(code=1) from error

    if not devices:
        console.print("[yellow]⚠ No devices with wireless ADB found.[/yellow]")
        console.print(
            "Make sure the TV is awake and USB debugging is enabled."
        )
        raise typer.Exit(code=1)

    table = Table(title=f"Found {len(devices)} device(s)")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Manufacturer")
    table.add_column("Model")
    table.add_column("Android")
    table.add_column("IP address", style="green")

    for index, device in enumerate(devices, start=1):
        table.add_row(
            str(index),
            device.manufacturer,
            device.model,
            device.android_version,
            device.ip_address,
        )

    console.print(table)    


if __name__ == "__main__":
    app()
