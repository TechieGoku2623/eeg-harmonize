# resample_fidelity results

Default resampler = resample_poly. Criterion: corr>=0.95 vs the 80 Hz-removed reference, then minimum Welch power in 50–64 Hz.

| method | corr vs 8/20/40 Hz ref | rmse | alias power 50-64 Hz |
| --- | --- | --- | --- |
| fourier_resample | 0.999213 | 0.034711 | 1.766422e-05 |
| resample_poly | 0.999190 | 0.035269 | 1.391647e-05 |
| linear_interp | 0.925986 | 0.356322 | 3.882625e-05 |
| naive_decimate | 0.925986 | 0.356322 | 3.882625e-05 |
