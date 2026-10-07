#!/usr/bin/env bash
set +e
eegh convert --in data/sample/odd-channels.edf --report --summary
exit $?
