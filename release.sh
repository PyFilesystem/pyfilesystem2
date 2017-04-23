#!/bin/sh
./makereadme.sh
python setup.py sdist bdist_wheel upload
