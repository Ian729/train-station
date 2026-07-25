#!/usr/bin/env bash
set -euo pipefail

echo "Hello from ${TRAIN_STATION_PROJECT:-demo-project}"
echo "Repository: ${TRAIN_STATION_REPO:-local-demo}"
mkdir -p artifacts
date -u +"%Y-%m-%dT%H:%M:%SZ" > artifacts/completed-at.txt
