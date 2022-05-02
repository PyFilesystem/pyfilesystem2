#!/usr/bin/env python

import os

with open(os.path.join("fs", "_version.py")) as f:
    exec(f.read())

from setuptools import setup

setup(version=__version__)
