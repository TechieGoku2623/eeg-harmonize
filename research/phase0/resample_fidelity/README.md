# resample_fidelity

## What is measured

Time-domain correlation, RMSE, and high-frequency alias leakage when a known
synthetic mixture (8/20/40/80 Hz + noise at 256 Hz) is downsampled to 128 Hz
by Fourier resample, polyphase resample, linear interpolation, and naive
decimation.

## Why it decides something

The default resampling method is expensive to reverse once provenance records
cite it. Alias leakage of the 80 Hz component (above the new Nyquist of 64 Hz)
is the deciding metric; low-frequency correlation must stay high.

## How to run

```bash
uv run python research/phase0/resample_fidelity/run.py
```

Seed 0. No corpus files are read.
