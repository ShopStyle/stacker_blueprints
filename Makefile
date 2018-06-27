.PHONY: all lint test

all: lint test

lint:
	flake8 stacker_blueprints

test:
	nosetests \
		--with-coverage \
		--cover-html \
		--cover-package=stacker_blueprints \
		--cover-erase \
		--cover-branches \
		--cover-inclusive
