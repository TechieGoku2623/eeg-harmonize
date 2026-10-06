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

eval:
	$(UV) run python research/phase0/schema_coverage/run.py
	$(UV) run python research/phase0/resample_fidelity/run.py
	$(UV) run python research/phase0/annotation_overlap/run.py
	$(UV) run python research/phase0/render_docs.py

demo:
	$(UV) run eegh demo-plan

record:
	@echo "Asciinema recordings are a Phase 3 deliverable."
