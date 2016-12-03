#!/bin/sh
nosetests --with-coverage --cover-package=fs -a "!slow" tests
rm .coverage
