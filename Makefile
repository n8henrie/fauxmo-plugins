SHELL := /bin/bash
PYTHON = /usr/bin/env python3
PWD = $(shell pwd)
GREP := $(shell command -v ggrep || command -v grep)
SED := $(shell command -v gsed || command -v sed)

.PHONY: clean-pyc clean help travis github update-reqs

help:
	@$(GREP) --only-matching --word-regexp '^[^[:space:].]*:' Makefile | $(SED) 's|:[:space:]*||'

clean: clean-pyc clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/

lint:
	flake8 . tests

test:
	pytest tests

test-all:
	tox

.venv:
	$(PYTHON) -m venv .venv
	./.venv/bin/pip install --upgrade pip wheel setuptools

update-reqs:
	@$(GREP) --invert-match --no-filename '^#' requirements*.txt | \
		$(SED) 's|==.*$$||g' | \
		xargs ./.venv/bin/python -m pip install --upgrade; \
	for reqfile in requirements*.txt; do \
		echo "Updating $${reqfile}..."; \
		./.venv/bin/python -c 'print("\n{:#^80}".format("  Updated reqs below  "))' >> "$${reqfile}"; \
		for lib in $$(./.venv/bin/pip freeze --all --isolated --quiet | $(GREP) '=='); do \
			if $(GREP) "^$${lib%%=*}==" "$${reqfile}" >/dev/null; then \
				echo "$${lib}" >> "$${reqfile}"; \
			fi; \
		done; \
	done;

github:
	hub create

travis:
	[ -f .travis.yml ] && travis enable || travis init
