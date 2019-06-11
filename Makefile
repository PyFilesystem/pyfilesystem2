
.PHONY: release
release: cleandist
	python3 setup.py sdist bdist_wheel
	twine upload dist/*.whl dist/*.tar.gz

.PHONY: cleandist
cleandist:
	rm -f dist/*.whl dist/*.tar.gz

.PHONY: cleandocs
cleandocs:
	$(MAKE) -C docs clean

.PHONY: clean
clean: cleandist cleandocs

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
	$(MAKE) -C docs html
	python -c "import os, webbrowser; webbrowser.open('file://' + os.path.abspath('./docs/build/html/index.html'))"

.PHONY: typecheck
typecheck:
	mypy -p fs --config setup.cfg
