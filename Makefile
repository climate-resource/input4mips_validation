# Makefile to help automate key steps

.DEFAULT_GOAL := help
# Will likely fail on Windows, but Makefiles are in general not Windows
# compatible so we're not too worried
TEMP_FILE := $(shell mktemp)

# A helper script to get short descriptions of each target in the Makefile
define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([\$$\(\)a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-30s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


.PHONY: help
help:  ## print short description of each target
	@python3 -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: checks
checks:  ## run all the linting checks of the codebase
	@echo "=== pre-commit ==="; pixi run -e all-dev pre-commit run --all-files || echo "--- pre-commit failed ---" >&2; \
		echo "=== mypy ==="; MYPYPATH=stubs pixi run -e all-dev mypy src || echo "--- mypy failed ---" >&2; \
		echo "======"

.PHONY: ruff-fixes
ruff-fixes:  ## fix the code using ruff
    # format before and after checking so that the formatted stuff is checked and
    # the fixed stuff is formatted
	pixi run -e all-dev ruff format src tests scripts docs/source/conf.py docs/source/notebooks/*.py
	pixi run -e all-dev ruff check src tests scripts docs/source/conf.py docs/source/notebooks/*.py --fix
	pixi run -e all-dev ruff format src tests scripts docs/source/conf.py docs/source/notebooks/*.py


.PHONY: test
test:  ## run the tests
	pixi run -e all-dev pytest src tests -r a -v --doctest-modules --cov=src

# Note on code coverage and testing:
# You must specify cov=src as otherwise funny things happen when doctests are
# involved.
# If you want to debug what is going on with coverage, we have found
# that adding COVERAGE_DEBUG=trace to the front of the below command
# can be very helpful as it shows you if coverage is tracking the coverage
# of all of the expected files or not.
# We are sure that the coverage maintainers would appreciate a PR that improves
# the coverage handling when there are doctests and a `src` layout like ours.

.PHONY: docs
docs: docs/cli/index.md  ## build the docs
	pixi run -e all-dev mkdocs build

.PHONY: docs-serve
docs-serve: docs/cli/index.md  ## serve the docs locally
	pixi run -e all-dev mkdocs serve

docs/cli/index.md: src/input4mips_validation/cli/__init__.py  ## auto-generate the typer app docs
	pixi run -e all-dev typer input4mips_validation.cli utils docs --output docs/cli/index.md --name input4mips-validation

.PHONY: changelog-draft
changelog-draft:  ## compile a draft of the next changelog
	pixi run -e all-dev towncrier build --draft

.PHONY: licence-check
licence-check:  ## Check that licences of the dependencies are suitable
	# Will likely fail on Windows, but Makefiles are in general not Windows
	# compatible so we're not too worried
	pdm export -o $(TEMP_FILE) --without=tests --without=docs --without=dev
	pdm run liccheck -r $(TEMP_FILE) -R licence-check.txt
	rm $(TEMP_FILE)

.PHONY: virtual-environment
virtual-environment:  ## update virtual environment, create a new one if it doesn't already exist
	pixi install
	pixi run -e all-dev pre-commit install
	# Make sure pdm lock file is up to date too
	pdm lock --strategy=inherit_metadata --dev --group :all
