"""Vocabulary overlap and controlled-set coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def main() -> None:
    raw = json.loads((HERE / "probe_set" / "vocabularies.json").read_text(encoding="utf-8"))
    mapping: dict[str, dict[str, str | None]] = raw["mapping"]
    corpora = list(mapping.keys())
    vocab = {name: set(mapping[name].keys()) for name in corpora}

    jaccard: dict[str, dict[str, float]] = {}
    j_rows: list[list[str]] = []
    for left in corpora:
        jaccard[left] = {}
        row = [left]
        for right in corpora:
            value = _jaccard(vocab[left], vocab[right])
            jaccard[left][right] = value
            row.append(f"{value:.3f}")
        j_rows.append(row)

    coverage: dict[str, dict[str, float | int]] = {}
    c_rows: list[list[str]] = []
    for name, table in mapping.items():
        mapped = sum(1 for target in table.values() if target is not None)
        unmapped = sum(1 for target in table.values() if target is None)
        frac = mapped / len(table)
        coverage[name] = {
            "n": len(table),
            "mapped": mapped,
            "unmapped": unmapped,
            "mapped_fraction": frac,
        }
        c_rows.append([name, str(len(table)), str(mapped), str(unmapped), f"{frac:.3f}"])

    mean_offdiag = float(np_mean([jaccard[a][b] for a in corpora for b in corpora if a < b]))
    unified = mean_offdiag >= 0.25
    payload = {
        "jaccard": jaccard,
        "coverage": coverage,
        "mean_offdiagonal_jaccard": mean_offdiag,
        "unified_flat_enum_achievable": unified,
        "decision": (
            "Unified flat enum is "
            + ("achievable" if unified else "not achievable")
            + f" (mean off-diagonal Jaccard {mean_offdiag:.3f} < 0.25 threshold). "
            "Keep a small controlled set plus an unmappable bucket; store the raw label."
        ),
    }
    results = HERE / "results"
    write_json(results / "results.json", payload)
    j_table = md_table(["corpus", *corpora], j_rows)
    c_table = md_table(["corpus", "n terms", "mapped", "unmapped", "mapped fraction"], c_rows)
    md = (
        "# annotation_overlap results\n\n"
        f"{payload['decision']}\n\n"
        "## Jaccard\n\n"
        f"{j_table}\n\n"
        "## Controlled-set coverage\n\n"
        f"{c_table}\n"
    )
    (results / "results.md").write_text(md, encoding="utf-8")
    print(md)


def np_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


if __name__ == "__main__":
    main()
