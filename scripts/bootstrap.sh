.PHONY: bootstrap lint test
bootstrap:
	poetry install
	poetry run pre-commit install
lint:
	poetry run pre-commit run --all-files
test:
	poetry run pytest -q
