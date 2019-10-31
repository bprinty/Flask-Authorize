#
# Makefile for python package
#
# ------------------------------------------------------


# config
# ------
PYTHON     = python3
PAKCAGE    = flask_authorize
PROJECT    = `$(PYTHON) -c 'print(__import__("flask_authorize").__pkg__)'`
VERSION    = `$(PYTHON) -c 'print(__import__("flask_authorize").__version__)'`


# targets
# -------
.PHONY: docs clean tag

.PHONY: help docs info clean init

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


info: ## list info about package
	@echo "$(PROJECT), version $(VERSION)$(BRANCH)"
	@echo last updated: `git log | grep --color=never 'Date:' | head -1 | sed 's/Date:   //g'`


clean: ## remove build and test artifacts
	rm -fr build dist .eggs .pytest_cache docs/_build .coverage
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +
	find . -name '*.py[co]' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +


lint: ## check style with flake8
	flake8 lib tests


test: ## run tests for package
	$(PYTHON) -m pytest tests


tag: ## tag repository for release
	VER=$(VERSION) && if [ `git tag | grep "$$VER" | wc -l` -ne 0 ]; then git tag -d $$VER; fi
	VER=$(VERSION) && git tag $$VER -m "$(PROJECT), release $$VER"


docs: ## generate sphinx documentation
	cd docs && make html


build: clean ## build package
	$(PYTHON) setup.py sdist
	$(PYTHON) setup.py bdist_wheel
	ls -l dist


release: build tag ## release package by pushing tags to github/pypi
	VER=$(VERSION) && git push origin :$$VER || echo 'Remote tag available'
	VER=$(VERSION) && git push origin $$VER
	twine upload --skip-existing dist/*


install: clean ## install package using setuptools
	$(PYTHON) setup.py install
