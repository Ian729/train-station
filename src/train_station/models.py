from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_ENTRYPOINT = ".trainstation/run.sh"


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    repo: str
    revision: str = "main"
    enabled: bool = True
    entrypoint: str = DEFAULT_ENTRYPOINT

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("project name must not be empty")

        parsed = urlparse(self.repo)
        is_https = parsed.scheme == "https" and bool(parsed.netloc)
        is_ssh = self.repo.startswith("git@") and ":" in self.repo
        is_local = parsed.scheme in {"", "file"} and Path(parsed.path).exists()
        if not (is_https or is_ssh or is_local):
            raise ValueError(f"unsupported repo URL for {self.name!r}: {self.repo}")

        entry = Path(self.entrypoint)
        if entry.is_absolute() or ".." in entry.parts:
            raise ValueError(f"entrypoint must stay inside the repository: {self.entrypoint}")
