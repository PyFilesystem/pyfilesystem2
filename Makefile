readme:
	pandoc --from=markdown --to=rst --output=README.rst README.md

release: readme
	python setup.py sdist bdist_wheel upload

test:
	nosetests --with-coverage --cover-package=fs -a "!slow" tests
	rm .coverage

slowtest:
	nosetests --with-coverage --cover-erase --cover-package=fs tests
	rm .coverage

