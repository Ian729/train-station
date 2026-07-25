# Train Station

Train Station is a small runtime designed to live **inside an ephemeral CI pipeline**.
The pipeline wakes it up; Train Station reads a registry, clones each enabled project,
and executes the project's standard entrypoint:

```text
.trainstation/run.sh
```

Projects own their environment setup. The entrypoint may run directly on the host,
build a Docker image, start Docker Compose, invoke an AI agent, or do anything else
available in the pipeline runner.

## Design principles

- **Every project is executable.**
- **Standardize the interface, not the implementation.**
- **No permanent server or database.**
- **The CI provider supplies scheduling and a temporary runner.**
- **The project entrypoint owns setup, execution, and project-specific cleanup.**

## Registration

The minimal registry contains only a project name and Git repository URL:

```yaml
version: 1
projects:
  - name: daily-report
    repo: https://github.com/example/daily-report.git
```

Optional fields:

```yaml
  - name: daily-report
    repo: https://github.com/example/daily-report.git
    revision: main
    enabled: true
    entrypoint: .trainstation/run.sh
```

## Project contract

A registered repository provides:

```text
.trainstation/run.sh
```

Example:

```bash
#!/usr/bin/env bash
set -euo pipefail

docker compose up --build --abort-on-container-exit --exit-code-from runner
```

Train Station injects these environment variables:

- `TRAIN_STATION_PROJECT`
- `TRAIN_STATION_REPO`
- `TRAIN_STATION_REVISION`
- `TRAIN_STATION_WORKSPACE`

The script's exit code is the project's result.

## Install and run

```bash
python -m pip install .
train-station validate
train-station list
train-station depart
```

Run selected projects:

```bash
train-station depart --project daily-report --project backup
```

Results are written to:

```text
artifacts/train-station-results.json
```

## GitHub Actions

The included workflow wakes Train Station every ten minutes and also supports manual dispatch.
GitHub Actions only supplies the clock and runner; the runtime reads `projects.yaml` dynamically.

## Docker environments

Train Station deliberately does not interpret Docker configuration. A project can build and
tear down its own environment inside `.trainstation/run.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

project="train-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
cleanup() {
  docker compose -p "$project" down --volumes --remove-orphans || true
}
trap cleanup EXIT INT TERM

docker compose -p "$project" up \
  --build \
  --abort-on-container-exit \
  --exit-code-from runner
```

This keeps Train Station's protocol small while allowing each project to fully control its runtime.

## Development

```bash
python -m pip install -e '.[dev]'
pytest
```
