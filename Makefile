PROJECT = marshmallow_jsonschema

PYTHON_VERSION ?= 3.12
VIRTUAL_ENV ?= .venv
PYTHON ?= $(VIRTUAL_ENV)/bin/python


REQUIREMENTS = requirements.txt
REQUIREMENTS_TEST = requirements-test.txt

SHELL := /bin/bash -euo pipefail

venv_init:
	if [ ! -d $(VIRTUAL_ENV) ]; then \
		python$(PYTHON_VERSION) -m venv --prompt="$(PROJECT)" $(VIRTUAL_ENV); \
	fi

venv:  venv_init
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS)
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS_TEST)
	$(VIRTUAL_ENV)/bin/pip install -e .

tox:
	tox

test:
	pytest

test_coverage:
	pytest --cov-report html --cov-config .coveragerc --cov $(PROJECT)

clean_build_and_dist:
	rm -rf build/ dist/

build_pkg: clean_build_and_dist
	pip install -U build
	python -m build

twine:
	pip install -U twine

pypitest: build_pkg twine
	twine upload -r testpypi dist/*

pypi: build_pkg twine
	twine upload -r pypi dist/*


clean_venv:
	rm -rf $(VIRTUAL_ENV)

clean_pyc:
	find . -name \*.pyc -delete

clean: clean_venv clean_pyc
