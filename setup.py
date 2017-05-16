#!/usr/bin/env python

from setuptools import setup, find_packages

with open('fs/_version.py') as f:
    exec(f.read())

CLASSIFIERS = [
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Topic :: System :: Filesystems',
]

with open('README.rst', 'rt') as f:
    DESCRIPTION = f.read()

REQUIREMENTS = [
    "appdirs~=1.4.0",
    "pytz",
    "setuptools",
    "six~=1.10.0",
]

setup(
    author="Will McGugan",
    author_email="will@willmcgugan.com",
    classifiers=CLASSIFIERS,
    description="Python's filesystem abstraction layer",
    install_requires=REQUIREMENTS,
    extras_require={
        "scandir :python_version < '3.5'": ['scandir~=1.5'],
        ":python_version < '3.4'": ['enum34~=1.1.6']
    },
    license="BSD",
    long_description=DESCRIPTION,
    name='fs',
    packages=find_packages(exclude=("tests",)),
    platforms=['any'],
    test_suite="nose.collector",
    tests_require=['appdirs', 'mock', 'pytz', 'pyftpdlib'],
    url="https://github.com/PyFilesystem/pyfilesystem2",
    version=__version__,
)
