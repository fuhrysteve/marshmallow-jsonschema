from setuptools import setup, find_packages


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content


setup(
    name='marshmallow-jsonschema',
    version='0.1.0.dev0',
    description='JSON Schema Draft v4 (http://json-schema.org/) formatting with marshmallow',
    long_description=read('README.md'),
    author='Stephen Fuhry',
    author_email='fuhrysteve@gmail.com',
    url='https://github.com/fuhrysteve/marshmallow-jsonschema',
    packages=find_packages(exclude=("test*", )),
    package_dir={'marshmallow-jsonschema': 'marshmallow-jsonschema'},
    include_package_data=True,
    install_requires=['marshmallow>=2.3.0'],
    license=read('LICENSE'),
    zip_safe=False,
    keywords=('marshmallow-jsonschema marshmallow schema serialization '
              'jsonschema validation'),
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests'
)
