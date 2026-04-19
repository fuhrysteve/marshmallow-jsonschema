# Contributing

## Local development setup

```bash
git clone https://github.com/fuhrysteve/marshmallow-jsonschema.git
cd marshmallow-jsonschema
make venv               # creates .venv and installs deps + the package in editable mode
source .venv/bin/activate
```

## Running the checks

```bash
pytest                                  # unit tests
black --check .                         # formatting (auto-fix: black .)
mypy marshmallow_jsonschema             # type check
tox                                     # full matrix (only if you have multiple Pythons installed)
```

The same three checks run in CI (`.github/workflows/{build,black,mypy}.yml`).

## Opening a PR

- Keep changes focused. A bug fix or one feature per PR; avoid bundling unrelated cleanups.
- Add or update tests for behavior changes.
- Update `CHANGES` under the `unreleased` heading if the change is user-visible.
- If you're changing the public API, note it explicitly in the PR description.

## Supported versions

The current release targets Python 3.9+ and marshmallow 3.13 through the 3.x line. marshmallow 4 is not yet supported.
