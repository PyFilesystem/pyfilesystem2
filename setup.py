#!/usr/bin/env python

from setuptools import setup, find_packages

with open('fs/_version.py') as f:
    exec(f.read())

classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Topic :: System :: Filesystems',
]

with open('README.txt', 'r') as f:
    long_desc = f.read()

# TODO: pin requirements
install_requires = [
    "enum34",
    "pytz",
    "scandir",
    "setuptools",
    "six",
]

setup(
    author="Will McGugan",
    author_email="will@willmcgugan.com",
    classifiers=classifiers,
    description="Filesystem abstraction layer",
    install_requires=install_requires,
    license="BSD",
    long_description=long_desc,
    name='fs',
    packages=find_packages(),
    platforms=['any'],
    test_suite="nose.collector",
    tests_require=['mock', 'pytz'],
    url="http://pypi.python.org/pypi/fs/",
    version=__version__,
)
