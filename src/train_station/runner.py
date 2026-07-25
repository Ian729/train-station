from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import Project


@dataclass(slots=True)
class RunResult:
    project: str
    repo: str
    revision: str
    status: str
    exit_code: int | None
    duration_seconds: float
    workspace: str
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_project(project: Project, workspace_root: Path, *, keep_workspace: bool = False) -> RunResult:
    started = time.monotonic()
    workspace = workspace_root / _safe_name(project.name)
    shutil.rmtree(workspace, ignore_errors=True)
    workspace.parent.mkdir(parents=True, exist_ok=True)

    result = RunResult(
        project=project.name,
        repo=project.repo,
        revision=project.revision,
        status="failed",
        exit_code=None,
        duration_seconds=0.0,
        workspace=str(workspace),
    )

    try:
        _clone(project, workspace)
        entrypoint = workspace / project.entrypoint
        if not entrypoint.is_file():
            raise FileNotFoundError(f"entrypoint not found: {project.entrypoint}")

        mode = entrypoint.stat().st_mode
        entrypoint.chmod(mode | stat.S_IXUSR)

        env = os.environ.copy()
        env.update(
            {
                "TRAIN_STATION_PROJECT": project.name,
                "TRAIN_STATION_REPO": project.repo,
                "TRAIN_STATION_REVISION": project.revision,
                "TRAIN_STATION_WORKSPACE": str(workspace),
            }
        )
        completed = subprocess.run(
            ["bash", str(entrypoint)],
            cwd=workspace,
            env=env,
            check=False,
        )
        result.exit_code = completed.returncode
        result.status = "succeeded" if completed.returncode == 0 else "failed"
    except Exception as exc:
        result.error = str(exc)
    finally:
        result.duration_seconds = round(time.monotonic() - started, 3)
        if not keep_workspace:
            shutil.rmtree(workspace, ignore_errors=True)

    return result


def write_results(path: Path, results: list[RunResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": {
            "total": len(results),
            "succeeded": sum(r.status == "succeeded" for r in results),
            "failed": sum(r.status == "failed" for r in results),
            "skipped": sum(r.status == "skipped" for r in results),
        },
        "results": [r.to_dict() for r in results],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _clone(project: Project, workspace: Path) -> None:
    subprocess.run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            project.revision,
            "--",
            project.repo,
            str(workspace),
        ],
        check=True,
    )


def _safe_name(name: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "-_." else "-" for ch in name).strip("-.")
    if not safe:
        raise ValueError(f"project name cannot form a workspace name: {name!r}")
    return safe
