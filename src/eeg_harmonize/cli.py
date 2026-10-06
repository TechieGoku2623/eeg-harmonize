"""Phase 0 CLI: designed-sample plan only. convert/validate land in Phase 2."""

from __future__ import annotations

import json

import typer
from rich.console import Console

from eeg_harmonize import SAFETY_DISCLAIMER, __version__
from eeg_harmonize.config import get_settings
from eeg_harmonize.logging import configure_logging

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=140)


@app.callback()
def _main() -> None:
    configure_logging()


@app.command("version")
def version() -> None:
    console.print(f"eeg-harmonize {__version__}")


@app.command("demo-plan")
def demo_plan() -> None:
    """Print the five designed clips and the path each exercises."""

    manifest = json.loads((get_settings().sample_dir / "manifest.json").read_text(encoding="utf-8"))
    console.print("[bold]eeg-harmonize designed sample clips[/bold]\n")
    for item in manifest["clips"]:
        console.print(f"[bold]{item['file']}[/bold]")
        console.print(f"  path:     {item['path_exercised']}")
        console.print(f"  expected: {item['expected_behavior']}\n")
    console.print()
    console.print(SAFETY_DISCLAIMER)
    console.print("\n`eegh convert` / `eegh inspect` are Phase 2. This listing is the dry-run.")
