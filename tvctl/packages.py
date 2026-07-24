from __future__ import annotations

from dataclasses import dataclass

from tvctl import adb


@dataclass(frozen=True)
class PackageState:
    name: str
    installed: bool
    enabled: bool


def is_installed(package_name: str) -> bool:
    result = adb.shell("pm", "path", package_name)
    return result.return_code == 0 and bool(result.stdout.strip())


def is_disabled(package_name: str) -> bool:
    result = adb.shell("pm", "list", "packages", "-d")
    package_line = f"package:{package_name}"
    return package_line in result.stdout.splitlines()


def get_state(package_name: str) -> PackageState:
    installed = is_installed(package_name)

    if not installed:
        return PackageState(
            name=package_name,
            installed=False,
            enabled=False,
        )

    return PackageState(
        name=package_name,
        installed=True,
        enabled=not is_disabled(package_name),
    )


def disable(package_name: str) -> adb.ADBResult:
    return adb.shell(
        "pm",
        "disable-user",
        "--user",
        "0",
        package_name,
    )


def enable(package_name: str) -> adb.ADBResult:
    return adb.shell(
        "pm",
        "enable",
        package_name,
    )
