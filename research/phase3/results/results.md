# phase3 evaluation

Default resampler remains resample_poly. Designed-clip convert: clean succeeds, bad-units unit_scale fails, odd-channels drops CB1/CB2. TUH transfer matrix unmeasured.

| Measurement | Result | Baseline |
| --- | --- | --- |
| Default resampler | resample_poly | naive decimate |
| Clean convert | ok | must succeed, no drops |
| bad-units.edf | unit_scale fail | non-zero exit / ValidationError |
| odd-channels dropped | CB1,CB2 | CB1,CB2 drop and log |
| TUH transfer matrix | not run | TUH not downloaded |
