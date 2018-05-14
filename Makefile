.PHONY: readme
readme:
	pandoc --from=markdown --to=rst --output=README.rst README.md

.PHONY: release
release: readme
	python setup.py sdist bdist_wheel
	twine upload dist/*.whl dist/*.tar.gz

.PHONY: test
test:
	nosetests --with-coverage --cover-package=fs -a "!slow" tests

.PHONY: slowtest
slowtest:
	nosetests --with-coverage --cover-erase --cover-package=fs tests

.PHONY: testall
testall:
	tox

.PHONY: docs
docs:
	cd docs && make html
	python -c "import os, webbrowser; webbrowser.open('file://' + os.path.abspath('./docs/build/html/index.html'))"

.PHONY: typecheck
typecheck:
	mypy -p fs --config setup.cfg
