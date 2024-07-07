python_src := src tests integration_tests

.PHONY: help
help:
	# Taken from https://marmelab.com/blog/2016/02/29/auto-documented-makefile.html.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: check-format
check-format:  ## Check code quality.
	ruff check --select I --diff ${python_src}
	ruff format --check --diff ${python_src}

.PHONY: check-lint
check-lint:  ## Check code quality.
	ruff check ${python_src}
	dmypy run -- ${python_src}

.PHONY: check-test
check-test:  ## Check tests.
	pytest

.PHONY: check
check: check-test check-lint check-format  ## Check everything.

.PHONY: format
format:  ## Format everything.
	ruff check --select I --fix ${python_src}
	ruff format ${python_src}
