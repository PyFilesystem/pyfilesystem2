#!/bin/sh
nosetests --with-coverage --cover-package=fs tests
rm .coverage
