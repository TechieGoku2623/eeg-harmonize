export PATH := $(HOME)/.local/bin:$(PATH)
UV ?= uv

.PHONY: setup lint test research eval demo record

setup:
	$(UV) sync --extra dev

lint:
	$(UV) run ruff check src tests research data/sample/build.py
	$(UV) run ruff format --check src tests research data/sample/build.py
	$(UV) run mypy

test:
	$(UV) run pytest

research:
	$(UV) run python research/phase0/run_all.py
	$(UV) run python research/phase3/run.py
	$(UV) run python research/phase0/render_docs.py

eval:
	$(UV) run python research/phase0/schema_coverage/run.py
	$(UV) run python research/phase0/resample_fidelity/run.py
	$(UV) run python research/phase0/annotation_overlap/run.py
	$(UV) run python research/phase3/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run python data/sample/build.py
	$(UV) run eegh inspect data/sample/clean.edf
	$(UV) run eegh convert --in data/sample/clean.edf
	@set +e; $(UV) run eegh convert --in data/sample/bad-units.edf; code=$$?; set -e; \
		if [ $$code -eq 0 ]; then echo "expected unit_scale failure"; exit 1; fi
	$(UV) run eegh convert --in data/sample/odd-channels.edf --report
	$(MAKE) eval

record:
	bash demo/record.sh
