#!/usr/bin/env bash
set +e
eegh convert --in data/sample/clean.edf --out /tmp/eeg-out.parquet
exit $?
