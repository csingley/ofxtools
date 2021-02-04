test:
	coverage erase
	black --check .
	mypy ofxtools
	mypy tests
	python `which nosetests` -dsv --nologcapture --with-coverage --cover-package ofxtools tests/*.py

clean:
	# find -name '.*\.pyc' -exec rm {} \;
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +;
	find -name '.*~' -exec rm {} \;
	rm -rf reg-settings.py
	rm -rf MANIFEST dist build *.egg-info
	rm coverage.xml

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

WORKDIR=python/lib/python3.6/site-packages
deploy:
	mkdir -p ${WORKDIR}
	cp -R ofxtools ${WORKDIR}
	zip -r python.zip python
	aws lambda publish-layer-version \
		--layer-name ofxtools \
		--zip-file fileb://python.zip \
		--compatible-runtimes python3.6 python3.7 python3.8
	rm -rf python
	rm -rf python.zip

.PHONY:	test clean lint lint-tests install uninstall html
