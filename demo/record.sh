#!/usr/bin/env bash
# Write asciinema v2 JSONL casts from real command output. No TUH. No credentials.
set -euo pipefail
export PATH="${HOME}/.local/bin:${PATH}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p demo
uv run python data/sample/build.py >/dev/null

python3 - <<'PY'
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

ROOT = Path(".").resolve()


def run(cmd: list[str], check: bool = True) -> str:
    env = dict(**{k: v for k, v in __import__("os").environ.items()})
    env["PATH"] = str(Path.home() / ".local" / "bin") + ":" + env.get("PATH", "")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False, env=env)
    body = proc.stdout + proc.stderr
    if not body.endswith("\n"):
        body += "\n"
    return f"$ {' '.join(cmd)}\n{body}"


def write_cast(path: Path, chunks: list[str]) -> None:
    header = {
        "version": 2,
        "width": 120,
        "height": 40,
        "timestamp": int(time.time()),
        "env": {"SHELL": "/bin/bash", "TERM": "xterm-256color"},
    }
    t = 0.05
    lines = [json.dumps(header, separators=(",", ":"))]
    for chunk in chunks:
        for part in chunk.splitlines(keepends=True):
            lines.append(json.dumps([round(t, 4), "o", part], separators=(",", ":")))
            t += 0.03
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


write_cast(
    ROOT / "demo/01-inspect-and-convert.cast",
    [
        run(["uv", "run", "eegh", "inspect", "data/sample/clean.edf"]),
        run(["uv", "run", "eegh", "convert", "--in", "data/sample/clean.edf"]),
    ],
)
write_cast(
    ROOT / "demo/02-validation-failures.cast",
    [
        run(["uv", "run", "eegh", "convert", "--in", "data/sample/bad-units.edf"], check=False),
        run(["uv", "run", "eegh", "convert", "--in", "data/sample/odd-channels.edf", "--report"]),
    ],
)
write_cast(
    ROOT / "demo/03-fidelity-benchmark.cast",
    [run(["make", "eval"])],
)
print("wrote demo/*.cast")
PY
