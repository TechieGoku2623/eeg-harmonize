"""Default resampler is scipy.signal.resample_poly (Phase 0 decision)."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.signal import resample_poly

DEFAULT_RESAMPLER = "resample_poly"


def resample_signal(
    samples: NDArray[np.float64],
    src_hz: float,
    dst_hz: float,
) -> NDArray[np.float64]:
    """Resample one channel with resample_poly. No-op when rates match."""

    if src_hz == dst_hz:
        return np.asarray(samples, dtype=np.float64)
    up = int(dst_hz)
    down = int(src_hz)
    gcd = int(np.gcd(up, down))
    return np.asarray(resample_poly(samples, up // gcd, down // gcd), dtype=np.float64)
