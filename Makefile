# ~
#
# Makefile for Flask-Authorize
#
# ------------------------------------------------


#
# config
#
PROJECT      := $(shell uv run python -c 'print(__import__("flask_authorize").__pkg__)')
VERSION      := $(shell uv run python -c 'print(__import__("flask_authorize").__version__)')
ARGS         :=
REQUIREMENTS := uv


#
# targets
#
.ONESHELL:
.PHONY: help deps info clean lint test build release sync docs

help: ## show available commands
	@echo ""
	@echo "Usage: make <command> [options]"
	@echo ""
	@echo "Project: \033[35m$(PROJECT) $(VERSION)\033[0m"
	@echo ""
	@echo "Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Requirements:"
	@make deps


deps: ## check for required tools
	@for dep in $(REQUIREMENTS); do \
		printf "  \033[36m%-18s\033[0m %s\n" "$$dep" "$$(which $$dep 2>/dev/null || echo 'not found')"; \
	done


info: ## list info about package
	@echo "$(PROJECT), version $(VERSION)"
	@echo last updated: `git log | grep --color=never 'Date:' | head -1 | sed 's/Date:   //g'`


clean: ## remove build and test artifacts
	rm -rf build dist .eggs .pytest_cache docs/_build .coverage
	find . -name '*.egg-info' -exec rm -rf {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.py[co]' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +


lint: ## check style with flake8
	uv run flake8 flask_authorize tests


test: ## run tests for package
	uv run pytest tests


build: clean ## build sdist and wheel
	uv build
	ls -l dist


release: build ## release package by pushing tags to github/pypi
	VER=$(VERSION) && git push origin :$$VER || echo 'Remote tag available'
	VER=$(VERSION) && git push origin $$VER
	uv publish


sync: ## create venv and install all dependencies
	uv sync --all-groups


docs: ## generate sphinx documentation
	cd docs && make html
