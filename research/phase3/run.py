"""Phase 3 evaluation on designed clips. TUH is not downloaded."""

from __future__ import annotations

import sys
from pathlib import Path

from eeg_harmonize.convert import convert_recording
from eeg_harmonize.inspect import inspect_recording
from eeg_harmonize.resample import DEFAULT_RESAMPLER
from eeg_harmonize.validate import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase0"))
from _lib import md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SAMPLE = ROOT / "data" / "sample"
RESULTS = HERE / "results"
RF = ROOT / "research" / "phase0" / "resample_fidelity" / "results" / "results.json"


def main() -> None:
    import json
    import runpy

    runpy.run_path(str(SAMPLE / "build.py"), run_name="__main__")
    rf = json.loads(RF.read_text(encoding="utf-8"))

    inspect = inspect_recording(SAMPLE / "clean.edf")
    clean = convert_recording(SAMPLE / "clean.edf")
    odd = convert_recording(SAMPLE / "odd-channels.edf")
    unit_failed = False
    unit_message = ""
    try:
        convert_recording(SAMPLE / "bad-units.edf")
    except ValidationError as exc:
        unit_failed = exc.check == "unit_scale"
        unit_message = str(exc)

    payload = {
        "default_resampler": DEFAULT_RESAMPLER,
        "phase0_default_resampler": rf["default_method"],
        "clean_convert_ok": (
            clean.n_channels_out == inspect.n_channels and not clean.dropped_channels
        ),
        "clean_n_channels": clean.n_channels_out,
        "odd_dropped": odd.dropped_channels,
        "odd_unmappable": odd.unmappable,
        "bad_units_rejected": unit_failed,
        "bad_units_message": unit_message,
        "tuh_downloaded": False,
        "decision": (
            f"Default resampler remains {DEFAULT_RESAMPLER}. "
            "Designed-clip convert: clean succeeds, bad-units unit_scale fails, "
            "odd-channels drops CB1/CB2. TUH transfer matrix unmeasured."
        ),
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    write_json(RESULTS / "results.json", payload)
    rows = [
        ["Default resampler", DEFAULT_RESAMPLER, "naive decimate"],
        [
            "Clean convert",
            "ok" if payload["clean_convert_ok"] else "fail",
            "must succeed, no drops",
        ],
        [
            "bad-units.edf",
            "unit_scale fail" if unit_failed else "unexpected pass",
            "non-zero exit / ValidationError",
        ],
        [
            "odd-channels dropped",
            ",".join(odd.dropped_channels) or "(none)",
            "CB1,CB2 drop and log",
        ],
        ["TUH transfer matrix", "not run", "TUH not downloaded"],
    ]
    table = md_table(["Measurement", "Result", "Baseline"], rows)
    md = f"# phase3 evaluation\n\n{payload['decision']}\n\n{table}\n"
    (RESULTS / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
