"""CLI: demo-plan, inspect, convert, validate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from eeg_harmonize import SAFETY_DISCLAIMER, __version__
from eeg_harmonize.config import get_settings
from eeg_harmonize.convert import ConvertReport, convert_recording, validate_recording
from eeg_harmonize.inspect import inspect_recording
from eeg_harmonize.logging import configure_logging
from eeg_harmonize.validate import ValidationError


def _print_eval_summary() -> None:
    path = get_settings().repo_root / "docs" / "EVALUATION.md"
    n = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# Evaluation"):
            continue
        console.print(line[:100])
        if line.strip():
            n += 1
        if n >= 14:
            break


app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console(width=100)


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
    console.print(
        "\n`eegh convert` / `eegh inspect` run on committed designed clips. No TUH download."
    )


def _print_inspect(path: Path) -> None:
    report = inspect_recording(path)
    console.print(f"[bold]inspect[/bold]  {report.path}")
    console.print(f"montage:     {report.montage_system}")
    console.print(f"sfreq:       {report.sfreq} Hz")
    console.print(f"reference:   {report.reference_scheme}")
    console.print(f"channels:    {report.n_channels}  {', '.join(report.channel_names)}")
    console.print(f"duration:    {report.duration_sec:.3f} s")
    console.print(f"ann. vocab:  {', '.join(report.annotation_vocabulary) or '(none)'}")
    if report.annotation_unmappable:
        console.print(f"unmappable:  {', '.join(report.annotation_unmappable)}")
    if report.dropped_noncanonical:
        dropped = ", ".join(report.dropped_noncanonical)
        console.print(f"non-10-20:   {dropped} (would drop on convert)")
    console.print(f"present:     {', '.join(report.present_fields)}")
    console.print(f"missing:     {', '.join(report.missing_fields)}")
    console.print()
    console.print(SAFETY_DISCLAIMER)


def _print_convert(report: ConvertReport, *, show_report: bool, summary: bool = False) -> None:
    console.print(f"[bold]convert[/bold]  {report.source_path}")
    console.print(f"sfreq:       {report.sfreq} Hz")
    console.print(f"channels:    {report.n_channels_in} → {report.n_channels_out}")
    console.print(f"resampler:   {report.resampler}")
    if report.dropped_channels:
        console.print(
            f"dropped:     {', '.join(report.dropped_channels)}  "
            "(no 10-20 equivalent; never renamed)"
        )
    else:
        console.print("dropped:     (none)")
    if report.unmappable:
        console.print(f"unmappable:  {', '.join(report.unmappable)}")
    console.print("provenance:")
    for step in report.provenance.operations:
        console.print(f"  - {step}")
    if report.output_path:
        console.print(f"wrote:       {report.output_path}")
    if show_report:
        table = Table(title="annotation map")
        table.add_column("raw")
        table.add_column("controlled")
        table.add_column("bucket")
        for item in report.annotations:
            table.add_row(
                item.raw,
                item.controlled or "",
                "unmappable" if item.unmappable else "controlled",
            )
        if report.annotations:
            console.print(table)
        if not summary:
            console.print(f"present:     {', '.join(report.present_fields)}")
            console.print(f"missing:     {', '.join(report.missing_fields)}")
    console.print()
    console.print(SAFETY_DISCLAIMER)


@app.command("inspect")
def inspect_cmd(edf: Annotated[Path, typer.Argument(exists=True)]) -> None:
    """Print montage, sfreq, reference, channels, vocab, and canonical field coverage."""

    _print_inspect(edf)


@app.command("convert")
def convert_cmd(
    source: Annotated[Path, typer.Option("--in", exists=True, help="Input EDF")],
    out: Annotated[Path | None, typer.Option("--out", help="Optional JSON or parquet")] = None,
    report: Annotated[
        bool,
        typer.Option("--report", help="Print dropped channels and annotation map"),
    ] = False,
    summary: Annotated[
        bool,
        typer.Option("--summary", help="Skip present/missing field dump"),
    ] = False,
) -> None:
    """Apply transforms and print the provenance chain. Hard-fails on unit_scale."""

    try:
        result = convert_recording(source, out=out)
    except ValidationError as exc:
        console.print(f"[red]{exc.check}: {exc}[/red]")
        console.print(SAFETY_DISCLAIMER)
        raise typer.Exit(code=1) from exc
    _print_convert(result, show_report=report, summary=summary)


@app.command("eval")
def eval_cmd(
    summary: bool = typer.Option(True, "--summary/--full"),
) -> None:
    """Print the published Phase 3 table (same numbers as `make eval`)."""

    _print_eval_summary()
    if not summary:
        console.print("Full harness output: make eval")
    console.print()
    console.print(SAFETY_DISCLAIMER)


@app.command("validate")
def validate_cmd(edf: Annotated[Path, typer.Argument(exists=True)]) -> None:
    """Run unit and channel checks. Same hard fail as convert."""

    try:
        result = validate_recording(edf)
    except ValidationError as exc:
        console.print(f"[red]{exc.check}: {exc}[/red]")
        console.print(SAFETY_DISCLAIMER)
        raise typer.Exit(code=1) from exc
    console.print(
        f"validate ok  channels={result.n_channels_out} dropped={result.dropped_channels}"
    )
    console.print(SAFETY_DISCLAIMER)
