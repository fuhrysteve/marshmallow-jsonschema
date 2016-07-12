

installcheck:
	pip install -U .[reco]
	pip install strict-rfc3339 jsonschema coveralls coverage

check:
	py.test -v

coverage:
	coverage erase
	coverage run --source marshmallow_jsonschema -m py.test -v

pypitest:
	python setup.py sdist upload -r pypitest

pypi:
	python setup.py sdist upload -r pypi
