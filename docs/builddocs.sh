#!/bin/sh
make html
python -c "import os, webbrowser; webbrowser.open('file://' + os.path.abspath('./build/html/index.html'))"
watchmedo shell-command ../ --patterns "*.rst;*.py" --recursive --command="rm -rf build;make html;"
