test:
	coverage erase
	black --check .
	mypy ofxtools
	mypy tests
	python `which nosetests` -dsv --nologcapture --with-coverage --cover-package ofxtools tests/*.py

clean:
	find . -name '*\.pyc' -exec rm '{}' \;
	find . -name '.*~' -exec rm '{}' \;
	#find -regex '.*\.pyc' -exec rm {} \;
	#find -regex '.*~' -exec rm {} \;
	rm -rf reg-settings.py
	rm -rf MANIFEST dist build *.egg-info
	rm -f coverage.xml

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
