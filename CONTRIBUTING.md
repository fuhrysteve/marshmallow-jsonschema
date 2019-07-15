Setting Up for Local Development
********************************

1. Fork marshmallow_jsonschema on Github.

::

    $ git clone https://github.com/fuhrysteve/marshmallow-jsonschema.git
    $ cd marshmallow_jsonschema

2. Create a virtual environment and install all dependencies

::

    $ make venv

3. Install the pre-commit hooks, which will format and lint your git staged files.

::

    # The pre-commit CLI was installed above
    $ pre-commit install --allow-missing-config


Running tests
*************

To run all tests: ::

    $ pytest

To run syntax checks: ::

    $ tox -e lint

(Optional) To run tests in all supported Python versions in their own virtual environments (must have each interpreter installed): ::

    $ tox
