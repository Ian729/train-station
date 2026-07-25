import subprocess
from pathlib import Path

from train_station.models import Project
from train_station.runner import run_project


def make_repo(tmp_path: Path, script: str) -> Path:
    repo = tmp_path / "source"
    (repo / ".trainstation").mkdir(parents=True)
    (repo / ".trainstation/run.sh").write_text(script, encoding="utf-8")
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=repo, check=True, capture_output=True)
    return repo


def test_run_project_success(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, "#!/usr/bin/env bash\nset -e\ntest \"$TRAIN_STATION_PROJECT\" = demo\n")
    result = run_project(Project(name="demo", repo=str(repo)), tmp_path / "workspaces")
    assert result.status == "succeeded"
    assert result.exit_code == 0


def test_run_project_failure(tmp_path: Path) -> None:
    repo = make_repo(tmp_path, "#!/usr/bin/env bash\nexit 7\n")
    result = run_project(Project(name="demo", repo=str(repo)), tmp_path / "workspaces")
    assert result.status == "failed"
    assert result.exit_code == 7
