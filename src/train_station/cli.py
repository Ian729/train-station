from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import load_projects
from .runner import RunResult, run_project, write_results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="train-station")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a project registry")
    validate.add_argument("--config", type=Path, default=Path("projects.yaml"))

    list_cmd = sub.add_parser("list", help="List registered projects")
    list_cmd.add_argument("--config", type=Path, default=Path("projects.yaml"))

    depart = sub.add_parser("depart", help="Run all enabled registered projects")
    depart.add_argument("--config", type=Path, default=Path("projects.yaml"))
    depart.add_argument("--workspace", type=Path, default=Path(".train-station/workspaces"))
    depart.add_argument("--results", type=Path, default=Path("artifacts/train-station-results.json"))
    depart.add_argument("--project", action="append", default=[], help="Run only named project; repeatable")
    depart.add_argument("--keep-workspace", action="store_true")
    depart.add_argument("--fail-fast", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        projects = load_projects(args.config)
    except (OSError, ValueError) as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        print(f"valid registry: {len(projects)} project(s)")
        return 0

    if args.command == "list":
        for project in projects:
            state = "enabled" if project.enabled else "disabled"
            print(f"{project.name}\t{state}\t{project.repo}\t{project.revision}\t{project.entrypoint}")
        return 0

    selected = set(args.project)
    unknown = selected - {project.name for project in projects}
    if unknown:
        print(f"unknown project(s): {', '.join(sorted(unknown))}", file=sys.stderr)
        return 2

    results: list[RunResult] = []
    for project in projects:
        if selected and project.name not in selected:
            continue
        if not project.enabled:
            results.append(
                RunResult(project.name, project.repo, project.revision, "skipped", None, 0.0, "")
            )
            continue

        print(f"::group::Train {project.name}", flush=True)
        result = run_project(project, args.workspace, keep_workspace=args.keep_workspace)
        print(f"status={result.status} exit_code={result.exit_code} duration={result.duration_seconds}s")
        if result.error:
            print(f"error={result.error}", file=sys.stderr)
        print("::endgroup::", flush=True)
        results.append(result)
        if args.fail_fast and result.status == "failed":
            break

    write_results(args.results, results)
    return 1 if any(result.status == "failed" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
