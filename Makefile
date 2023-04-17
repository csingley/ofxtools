test:
	coverage erase
	black --check .
	mypy ofxtools
	mypy tests
	python `which pytest` --cov=ofxtools tests/

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +;
	find -name '.*~' -exec rm {} \;
	rm -rf reg-settings.py
	rm -rf MANIFEST dist build *.egg-info
	rm -rf coverage.xml

install:
	make clean
	make uninstall
	pip install .

uninstall:
	pip uninstall -y ofxtools

lint:
	pylint ofxtools/*.py

lint-tests:
	pylint tests/*.py

html:
	sphinx-build -b html docs docs/_build

.PHONY:	test clean lint lint-tests install uninstall html
