"""Canonical-field presence matrix. Decides required vs optional."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from eeg_harmonize.schema import CANONICAL_FIELDS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
INV = json.loads((HERE / "probe_set" / "inventories.json").read_text(encoding="utf-8"))
CORPORA = list(INV["inventories"].keys())


def main() -> None:
    required: list[str] = []
    optional: list[str] = []
    rows: list[list[str]] = []
    decisions: dict[str, str] = {}
    for field in CANONICAL_FIELDS:
        presences = [INV["inventories"][corpus][field.name] for corpus in CORPORA]
        never = sum(1 for p in presences if p == "never")
        rare = sum(1 for p in presences if p == "rare")
        if never + rare >= 2:
            decision = "optional"
            optional.append(field.name)
        else:
            decision = "required"
            required.append(field.name)
        decisions[field.name] = decision
        rows.append([field.name, *presences, decision])

    payload = {
        "corpora": CORPORA,
        "required_fields": required,
        "optional_fields": optional,
        "decisions": decisions,
        "source_note": INV["note"],
        "sources": INV["sources"],
        "full_corpus_scan": "unmeasured",
        "full_corpus_scan_measurement": (
            "After TUH DUA + PhysioNet downloads, walk one file per corpus and "
            "fill presence from actual headers/sidecars. That replaces this inventory."
        ),
    }
    results = HERE / "results"
    write_json(results / "results.json", payload)
    table = md_table(["field", *CORPORA, "decision"], rows)
    md = (
        "# schema_coverage results\n\n"
        f"Required ({len(required)}): {', '.join(required)}\n\n"
        f"Optional ({len(optional)}): {', '.join(optional)}\n\n"
        "A field is optional if it is never or rare in two or more corpora.\n\n"
        f"{table}\n"
    )
    (results / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
