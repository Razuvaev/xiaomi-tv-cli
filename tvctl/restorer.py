from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tvctl import packages
from tvctl.profiles import Profile, ProfilePackage, load_profile


@dataclass(frozen=True)
class RestoreResult:
    package: ProfilePackage
    success: bool
    message: str


def get_disabled_packages(profile: Profile) -> tuple[ProfilePackage, ...]:
    disabled_packages: list[ProfilePackage] = []

    for profile_package in profile.packages:
        state = packages.get_state(profile_package.name)

        if state.installed and not state.enabled:
            disabled_packages.append(profile_package)

    return tuple(disabled_packages)


def run(profile_path: Path) -> tuple[RestoreResult, ...]:
    profile = load_profile(profile_path)
    results: list[RestoreResult] = []

    for profile_package in get_disabled_packages(profile):
        result = packages.enable(profile_package.name)
        output = result.output.lower()

        success = result.return_code == 0 and (
            "new state: enabled" in output or "package" in output
        )

        results.append(
            RestoreResult(
                package=profile_package,
                success=success,
                message=result.output or "No ADB output.",
            )
        )

    return tuple(results)
