from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tvctl import packages
from tvctl.profiles import Profile, load_profile


@dataclass(frozen=True)
class DoctorPackageResult:
    name: str
    title: str
    category: str
    installed: bool
    enabled: bool

    @property
    def optimized(self) -> bool:
        return not self.installed or not self.enabled


@dataclass(frozen=True)
class DoctorReport:
    profile: Profile
    packages: tuple[DoctorPackageResult, ...]

    @property
    def optimized_count(self) -> int:
        return sum(result.optimized for result in self.packages)

    @property
    def score(self) -> int:
        if not self.packages:
            return 100

        return round(self.optimized_count / len(self.packages) * 100)


def run(profile_path: Path) -> DoctorReport:
    profile = load_profile(profile_path)
    results: list[DoctorPackageResult] = []

    for profile_package in profile.packages:
        state = packages.get_state(profile_package.name)

        results.append(
            DoctorPackageResult(
                name=profile_package.name,
                title=profile_package.title,
                category=profile_package.category,
                installed=state.installed,
                enabled=state.enabled,
            )
        )

    return DoctorReport(
        profile=profile,
        packages=tuple(results),
    )
