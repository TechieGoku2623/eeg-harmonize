from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARNESSES = (
    ROOT / "data" / "sample" / "build.py",
    HERE / "schema_coverage" / "run.py",
    HERE / "resample_fidelity" / "run.py",
    HERE / "annotation_overlap" / "run.py",
    HERE / "render_docs.py",
)


def main() -> None:
    for script in HARNESSES:
        print(f"\n=== {script.relative_to(ROOT)} ===\n")
        subprocess.run([sys.executable, str(script)], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
