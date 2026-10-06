# annotation_overlap results

Unified flat enum is not achievable (mean off-diagonal Jaccard 0.013 < 0.25 threshold). Keep a small controlled set plus an unmappable bucket; store the raw label.

## Jaccard

| corpus | TUSZ | CHB-MIT | Sleep-EDF | TUAR | BIDS-EEG |
| --- | --- | --- | --- | --- | --- |
| TUSZ | 1.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| CHB-MIT | 0.000 | 1.000 | 0.000 | 0.000 | 0.125 |
| Sleep-EDF | 0.000 | 0.000 | 1.000 | 0.000 | 0.000 |
| TUAR | 0.000 | 0.000 | 0.000 | 1.000 | 0.000 |
| BIDS-EEG | 0.000 | 0.125 | 0.000 | 0.000 | 1.000 |

## Controlled-set coverage

| corpus | n terms | mapped | unmapped | mapped fraction |
| --- | --- | --- | --- | --- |
| TUSZ | 11 | 11 | 0 | 1.000 |
| CHB-MIT | 2 | 2 | 0 | 1.000 |
| Sleep-EDF | 8 | 7 | 1 | 0.875 |
| TUAR | 6 | 6 | 0 | 1.000 |
| BIDS-EEG | 7 | 4 | 3 | 0.571 |
