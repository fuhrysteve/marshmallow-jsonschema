PROJECT = marshmallow_jsonschema

PYTHON_VERSION ?= 3.8
VIRTUAL_ENV ?= .venv
PYTHON ?= $(VIRTUAL_ENV)/bin/python


REQUIREMENTS = requirements.txt
REQUIREMENTS_TEST = requirements-test.txt
REQUIREMENTS_TOX = requirements-tox.txt

SHELL := /bin/bash -euo pipefail

venv_init:
	pip install virtualenv
	if [ ! -d $(VIRTUAL_ENV) ]; then \
		virtualenv -p python$(PYTHON_VERSION) --prompt="($(PROJECT))" $(VIRTUAL_ENV); \
	fi

venv:  venv_init
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS)
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS_TEST)
	$(VIRTUAL_ENV)/bin/pip install -r $(REQUIREMENTS_TOX)

tox:
	tox

test:
	pytest

test_coverage:
	pytest --cov-report html --cov-config .coveragerc --cov $(PROJECT)

install_pandoc:
	sudo apt install pandoc
	pip install pypandoc

sdist:
	python setup.py sdist

bdist_wheel:
	pip install wheel
	python setup.py bdist_wheel

twine:
	pip install twine

pypitest: sdist bdist_wheel twine
	twine upload -r pypitest dist/*

pypi: sdist bdist_wheel twine
	twine upload -r pypi dist/*


clean_venv:
	rm -rf $(VIRTUAL_ENV)

clean_pyc:
	find . -name \*.pyc -delete

clean: clean_venv clean_pyc
