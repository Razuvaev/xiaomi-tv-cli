from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class ADBError(RuntimeError):
    pass


@dataclass(frozen=True)
class ADBResult:
    return_code: int
    stdout: str
    stderr: str

    @property
    def output(self) -> str:
        return "\n".join(part for part in (self.stdout, self.stderr) if part).strip()


def get_executable() -> str | None:
    if getattr(sys, "frozen", False):
        bundled_adb = Path(sys.executable).resolve().parent / ("adb.exe" if sys.platform == "win32" else "adb")
        if bundled_adb.is_file():
            return str(bundled_adb)

    return shutil.which("adb")


def is_installed() -> bool:
    return get_executable() is not None


def run(*arguments: str, timeout: float = 15) -> ADBResult:
    adb_executable = get_executable()

    if adb_executable is None:
        if sys.platform == "darwin":
            install_hint = "Install it with: brew install --cask android-platform-tools"
        else:
            install_hint = "Install Android Platform Tools or place adb next to tvctl."

        raise ADBError(f"ADB is not installed. {install_hint}")

    try:
        process = subprocess.run(
            [adb_executable, *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise ADBError(f"ADB command timed out after {timeout:g} seconds.") from error
    except OSError as error:
        raise ADBError(f"Failed to execute ADB: {error}") from error

    return ADBResult(
        return_code=process.returncode,
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
    )


def connect(ip_address: str, port: int = 5555) -> ADBResult:
    return run("connect", f"{ip_address}:{port}", timeout=20)


def disconnect(ip_address: str, port: int = 5555) -> ADBResult:
    return run("disconnect", f"{ip_address}:{port}")


def devices() -> ADBResult:
    return run("devices")

def shell(*arguments: str, timeout: float = 15) -> ADBResult:
    return run("shell", *arguments, timeout=timeout)


def get_property(name: str) -> str:
    result = shell("getprop", name)

    if result.return_code != 0:
        raise ADBError(result.output or f"Failed to read property: {name}")

    return result.stdout.strip()


def get_home_launcher() -> str:
    result = shell(
        "cmd",
        "package",
        "resolve-activity",
        "--brief",
        "-a",
        "android.intent.action.MAIN",
        "-c",
        "android.intent.category.HOME",
    )

    if result.return_code != 0:
        raise ADBError(result.output or "Failed to resolve the HOME launcher.")

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else "Unknown"    
