.PHONY: install test validate eval compare samples ci workbench

RUN_AT ?= 2026-11-03T12:00:00Z

install:
	pip install -e ".[dev]"

test:
	pytest -q

validate:
	sa knowledge validate

eval:
	sa eval

compare:
	sa eval-compare --baseline release:1.0.0 --candidate pack

samples:
	rm -rf samples
	for d in examples/northwind/requisitions/*/; do sa diagnose $$d --knowledge env:production --out samples --run-at $(RUN_AT); done
	for d in examples/northwind/requisitions/REQ-SRE-0142 examples/northwind/requisitions/REQ-LH-0217; do sa discover $$d --knowledge env:production --out samples; done
	sa portfolio examples --knowledge env:production --out samples --run-at $(RUN_AT)
	sa eval --knowledge env:production --out samples/eval.md
	sa eval-compare --baseline release:1.0.0 --candidate release:1.1.0 --out samples/knowledge-1.0.0-to-1.1.0.md

ci: validate test eval

workbench:
	sa workbench
