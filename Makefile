test:
	flake8 stacker_blueprints
	nosetests \
		--with-coverage \
		--cover-html \
		--cover-package=stacker_blueprints \
		--cover-erase \
		--cover-branches \
		--cover-inclusive
		# ./tests
