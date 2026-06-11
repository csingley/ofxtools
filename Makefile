test:
	ruff check
	mypy
	pytest

clean:
	find . -name "*.py[co]" -o -name __pycache__ -exec rm -rf {} +;
	find -name '.*~' -exec rm {} \;
	rm -rf MANIFEST dist build *.egg-info coverage.xml

install:
	pip install -e ".[net,dev]"

uninstall:
	pip uninstall -y ofxtools

lint:
	ruff check ofxtools

.PHONY:	test clean lint install uninstall
