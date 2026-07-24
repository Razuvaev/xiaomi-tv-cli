from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


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


def is_installed() -> bool:
    return shutil.which("adb") is not None


def run(*arguments: str, timeout: float = 15) -> ADBResult:
    if not is_installed():
        raise ADBError(
            "ADB is not installed. Install it with: brew install android-platform-tools"
        )

    try:
        process = subprocess.run(
            ["adb", *arguments],
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
