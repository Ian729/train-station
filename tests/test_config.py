from pathlib import Path

import pytest

from train_station.config import load_projects


def test_load_minimal_registry(tmp_path: Path) -> None:
    config = tmp_path / "projects.yaml"
    config.write_text(
        "version: 1\nprojects:\n  - name: demo\n    repo: https://github.com/acme/demo.git\n",
        encoding="utf-8",
    )
    projects = load_projects(config)
    assert len(projects) == 1
    assert projects[0].entrypoint == ".trainstation/run.sh"
    assert projects[0].revision == "main"


def test_reject_duplicate_names(tmp_path: Path) -> None:
    config = tmp_path / "projects.yaml"
    config.write_text(
        "version: 1\nprojects:\n"
        "  - name: demo\n    repo: https://github.com/acme/a.git\n"
        "  - name: demo\n    repo: https://github.com/acme/b.git\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate project name"):
        load_projects(config)


def test_reject_entrypoint_escape(tmp_path: Path) -> None:
    config = tmp_path / "projects.yaml"
    config.write_text(
        "version: 1\nprojects:\n"
        "  - name: demo\n    repo: https://github.com/acme/demo.git\n    entrypoint: ../run.sh\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="entrypoint must stay inside"):
        load_projects(config)
