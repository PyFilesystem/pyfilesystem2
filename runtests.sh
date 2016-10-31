#!/bin/sh
nosetests --processes=4 --with-coverage  --cover-package=fs -a "!slow" tests
rm .coverage
