

installcheck:
	pip install -U .[reco]
	pip install strict-rfc3339 jsonschema coveralls

check:
	py.test -v
