#!/bin/sh
nosetests -vv --with-coverage --cover-package=fs tests
rm .coverage
