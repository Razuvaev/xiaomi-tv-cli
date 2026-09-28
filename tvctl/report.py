from __future__ import annotations

from datetime import datetime
from pathlib import Path

from tvctl import adb

PROPERTIES = {
    "Manufacturer": "ro.product.manufacturer",
    "Brand": "ro.product.brand",
    "Model": "ro.product.model",
    "Device": "ro.product.device",
    "Product": "ro.product.name",
    "Board": "ro.product.board",
    "Android": "ro.build.version.release",
    "SDK": "ro.build.version.sdk",
    "Build": "ro.build.display.id",
    "Fingerprint": "ro.build.fingerprint",
}


def _packages(*arguments: str) -> list[str]:
    result = adb.shell("pm", "list", "packages", *arguments, timeout=30)

    if result.return_code != 0:
        raise adb.ADBError(result.output or "Failed to retrieve package list.")

    return sorted(
        line.removeprefix("package:").strip()
        for line in result.stdout.splitlines()
        if line.startswith("package:")
    )


def create_report(output: Path) -> Path:
    properties = {title: adb.get_property(name) or "Unknown" for title, name in PROPERTIES.items()}

    try:
        launcher = adb.get_home_launcher()
    except adb.ADBError:
        launcher = "Unknown"

    installed = _packages()
    disabled = _packages("-d")
    system = _packages("-s")
    third_party = _packages("-3")

    lines = [
        "tvctl Android TV diagnostic report",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "",
        "=== Device ===",
        *(f"{title}: {value}" for title, value in properties.items()),
        f"Home launcher: {launcher}",
        "",
        f"=== Installed packages ({len(installed)}) ===",
        *installed,
        "",
        f"=== Disabled packages ({len(disabled)}) ===",
        *disabled,
        "",
        f"=== System packages ({len(system)}) ===",
        *system,
        "",
        f"=== Third-party packages ({len(third_party)}) ===",
        *third_party,
        "",
    ]

    output.write_text("\n".join(lines), encoding="utf-8")
    return output
