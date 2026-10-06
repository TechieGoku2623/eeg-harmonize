# Data

Phase 0 commits designed EDF clips only (`data/sample/`). No TUH, CHB-MIT, or
Sleep-EDF bytes.

## TUH EEG / TUSZ / TUAR

Access requires the NEDC data-use agreement at
https://isip.piconepress.com/projects/nedc/html/tuh_eeg/. Submit the current
form, wait for rsync credentials (often several business days to a couple of
weeks; wait time here is unmeasured), and sync into gitignored bronze storage.
Do not commit TUH files. Do not start this download in CI.

## CHB-MIT and Sleep-EDF Expanded

PhysioNet open downloads (ODC-BY). Cite Goldberger et al. and the dataset
papers. Files are multi-hour and are not committed.

## OpenNeuro BIDS-EEG

Per-dataset license, usually CC0 or CC-BY. The generic BIDS adapter in Phase
2 covers many datasets with one plugin.

License and quality notes for each source are in
`docs/phase-0/research-memo.md` §3.
