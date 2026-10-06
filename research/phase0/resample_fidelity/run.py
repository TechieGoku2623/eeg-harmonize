"""Signal fidelity loss per resampling strategy. Seed 0."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.signal import resample, resample_poly, welch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lib import md_table, write_json  # noqa: E402

HERE = Path(__file__).resolve().parent
SEED = 0
SRC_HZ = 256
DST_HZ = 128
DURATION = 8.0


def _signal(n: int, rng: np.random.Generator) -> NDArray[np.float64]:
    t = np.arange(n) / SRC_HZ
    return (
        1.0 * np.sin(2 * np.pi * 8 * t)
        + 0.6 * np.sin(2 * np.pi * 20 * t)
        + 0.4 * np.sin(2 * np.pi * 40 * t)
        + 0.5 * np.sin(2 * np.pi * 80 * t)
        + 0.05 * rng.normal(size=n)
    ).astype(np.float64)


def _alias_power(x: NDArray[np.float64], hz: float) -> float:
    freqs, psd = welch(x, fs=hz, nperseg=min(256, x.size))
    # Energy sitting near the new Nyquist is leftover / aliased 80 Hz.
    band = (freqs >= 50.0) & (freqs <= hz / 2.0)
    return float(np.mean(psd[band])) if np.any(band) else float("nan")


def _metrics(
    reference: NDArray[np.float64], estimated: NDArray[np.float64], hz: float
) -> dict[str, float]:
    n = min(reference.size, estimated.size)
    ref = reference[:n]
    est = estimated[:n]
    corr = float(np.corrcoef(ref, est)[0, 1])
    rmse = float(np.sqrt(np.mean((ref - est) ** 2)))
    return {"corr": corr, "rmse": rmse, "alias_power": _alias_power(est, hz)}


def main() -> None:
    rng = np.random.default_rng(SEED)
    n = int(SRC_HZ * DURATION)
    src = _signal(n, rng)
    t_src = np.arange(n) / SRC_HZ
    n_out = n * DST_HZ // SRC_HZ
    t_dst = np.arange(n_out) / DST_HZ
    # Reference: same mixture without the 80 Hz term, sampled at 128 Hz.
    reference = (
        1.0 * np.sin(2 * np.pi * 8 * t_dst)
        + 0.6 * np.sin(2 * np.pi * 20 * t_dst)
        + 0.4 * np.sin(2 * np.pi * 40 * t_dst)
    )

    methods = {
        "fourier_resample": resample(src, n_out),
        "resample_poly": resample_poly(src, DST_HZ, SRC_HZ),
        "linear_interp": np.interp(t_dst, t_src, src),
        "naive_decimate": src[:: SRC_HZ // DST_HZ],
    }
    rows: list[list[str]] = []
    scored: dict[str, dict[str, float]] = {}
    for name, estimated in methods.items():
        est = np.asarray(estimated, dtype=np.float64)
        stats = _metrics(reference, est, DST_HZ)
        scored[name] = stats
        rows.append(
            [name, f"{stats['corr']:.6f}", f"{stats['rmse']:.6f}", f"{stats['alias_power']:.6e}"]
        )

    # Lowest alias power among methods that keep corr >= 0.95.
    eligible = {k: v for k, v in scored.items() if v["corr"] >= 0.95}
    winner = min(eligible, key=lambda k: eligible[k]["alias_power"]) if eligible else "none"
    payload = {
        "seed": SEED,
        "src_hz": SRC_HZ,
        "dst_hz": DST_HZ,
        "duration_sec": DURATION,
        "methods": scored,
        "default_method": winner,
        "decision": (
            f"Default resampler = {winner}. Criterion: corr>=0.95 vs the "
            "80 Hz-removed reference, then minimum Welch power in 50–64 Hz."
        ),
    }
    results = HERE / "results"
    write_json(results / "results.json", payload)
    table = md_table(["method", "corr vs 8/20/40 Hz ref", "rmse", "alias power 50-64 Hz"], rows)
    md = f"# resample_fidelity results\n\n{payload['decision']}\n\n{table}\n"
    (results / "results.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
