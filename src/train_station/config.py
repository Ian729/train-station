from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Project


def load_projects(path: Path) -> list[Project]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("registry root must be a mapping")

    version = raw.get("version", 1)
    if version != 1:
        raise ValueError(f"unsupported registry version: {version}")

    rows = raw.get("projects", [])
    if not isinstance(rows, list):
        raise ValueError("projects must be a list")

    projects: list[Project] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"projects[{index}] must be a mapping")
        project = _parse_project(row)
        project.validate()
        if project.name in seen:
            raise ValueError(f"duplicate project name: {project.name}")
        seen.add(project.name)
        projects.append(project)
    return projects


def _parse_project(row: dict[str, Any]) -> Project:
    allowed = {"name", "repo", "revision", "enabled", "entrypoint"}
    unknown = set(row) - allowed
    if unknown:
        raise ValueError(f"unknown project fields: {', '.join(sorted(unknown))}")

    try:
        name = str(row["name"])
        repo = str(row["repo"])
    except KeyError as exc:
        raise ValueError(f"missing required project field: {exc.args[0]}") from exc

    return Project(
        name=name,
        repo=repo,
        revision=str(row.get("revision", "main")),
        enabled=bool(row.get("enabled", True)),
        entrypoint=str(row.get("entrypoint", ".trainstation/run.sh")),
    )
