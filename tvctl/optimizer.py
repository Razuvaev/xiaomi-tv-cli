from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tvctl import packages
from tvctl.profiles import Profile, ProfilePackage, load_profile


@dataclass(frozen=True)
class OptimizationResult:
    package: ProfilePackage
    success: bool
    message: str


def get_enabled_packages(profile: Profile) -> tuple[ProfilePackage, ...]:
    enabled_packages: list[ProfilePackage] = []

    for profile_package in profile.packages:
        state = packages.get_state(profile_package.name)

        if state.installed and state.enabled:
            enabled_packages.append(profile_package)

    return tuple(enabled_packages)


def run(profile_path: Path) -> tuple[OptimizationResult, ...]:
    profile = load_profile(profile_path)
    results: list[OptimizationResult] = []

    for profile_package in get_enabled_packages(profile):
        result = packages.disable(profile_package.name)
        output = result.output.lower()

        success = result.return_code == 0 and (
            "disabled-user" in output or "new state: disabled" in output
        )

        results.append(
            OptimizationResult(
                package=profile_package,
                success=success,
                message=result.output or "No ADB output.",
            )
        )

    return tuple(results)
