# annotation_overlap

## What is measured

Jaccard overlap of published annotation vocabularies across TUSZ, CHB-MIT,
Sleep-EDF, TUAR, and a BIDS-EEG example set, plus the fraction of each
vocabulary that maps into a proposed controlled set.

## Why it decides something

If pairwise Jaccard is near zero and the unmappable fraction is high, a
unified flat enum is not achievable. The schema then needs an `unmappable`
bucket and per-corpus vocab modules, not a required shared term list.

## How to run

```bash
uv run python research/phase0/annotation_overlap/run.py
```

Vocabularies are committed from published annotation manuals, not sampled
from files.
