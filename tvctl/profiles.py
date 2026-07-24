from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


class ProfileError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProfilePackage:
    name: str
    title: str
    category: str


@dataclass(frozen=True)
class Profile:
    name: str
    description: str
    packages: tuple[ProfilePackage, ...]


def load_profile(path: Path) -> Profile:
    if not path.exists():
        raise ProfileError(f"Profile not found: {path}")

    try:
        content = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ProfileError(f"Failed to read profile: {path}") from error

    if not isinstance(content, dict):
        raise ProfileError("Profile root must be a YAML object.")

    name = content.get("name")
    description = content.get("description", "")
    package_items = content.get("packages")

    if not isinstance(name, str) or not name.strip():
        raise ProfileError("Profile must contain a non-empty name.")

    if not isinstance(description, str):
        raise ProfileError("Profile description must be a string.")

    if not isinstance(package_items, list):
        raise ProfileError("Profile packages must be a list.")

    packages: list[ProfilePackage] = []

    for index, item in enumerate(package_items):
        if not isinstance(item, dict):
            raise ProfileError(f"Package at index {index} must be an object.")

        package_name = item.get("name")
        title = item.get("title")
        category = item.get("category")

        if not all(isinstance(value, str) and value.strip() for value in (
            package_name,
            title,
            category,
        )):
            raise ProfileError(
                f"Package at index {index} must contain name, title and category."
            )

        packages.append(
            ProfilePackage(
                name=package_name,
                title=title,
                category=category,
            )
        )

    return Profile(
        name=name,
        description=description,
        packages=tuple(packages),
    )
