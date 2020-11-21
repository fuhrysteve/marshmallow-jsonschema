import os

from setuptools import setup, find_packages


PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def read(fname):
    with open(fname) as fp:
        return fp.read()


try:
    import pypandoc

    long_description = pypandoc.convert("README.md", "rst")
except (IOError, ImportError, OSError):
    long_description = read("README.md")


REQUIREMENTS_FILE = "requirements.txt"
REQUIREMENTS = open(os.path.join(PROJECT_DIR, REQUIREMENTS_FILE)).readlines()

REQUIREMENTS_TESTS_FILE = "requirements-test.txt"
REQUIREMENTS_TESTS = open(
    os.path.join(PROJECT_DIR, REQUIREMENTS_TESTS_FILE)
).readlines()

REQUIREMENTS_TOX_FILE = "requirements-tox.txt"
REQUIREMENTS_TOX = open(os.path.join(PROJECT_DIR, REQUIREMENTS_TOX_FILE)).readlines()

EXTRAS_REQUIRE = {
    "enum": ["marshmallow-enum"],
    "union": ["marshmallow-union"],
}


setup(
    name="marshmallow-jsonschema",
    version="0.11.0",
    description="JSON Schema Draft v4 (http://json-schema.org/)"
    " formatting with marshmallow",
    long_description=long_description,
    author="Stephen Fuhry",
    author_email="fuhrysteve@gmail.com",
    url="https://github.com/fuhrysteve/marshmallow-jsonschema",
    packages=find_packages(exclude=("test*",)),
    package_dir={"marshmallow-jsonschema": "marshmallow-jsonschema"},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    tests_require=REQUIREMENTS_TESTS + REQUIREMENTS_TOX,
    extras_require=EXTRAS_REQUIRE,
    license=read("LICENSE"),
    zip_safe=False,
    keywords=(
        "marshmallow-jsonschema marshmallow schema serialization "
        "jsonschema validation"
    ),
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    test_suite="tests",
)
