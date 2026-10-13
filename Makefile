.PHONY: fmt test publish debug patch

fmt:
	uvx ruff format src tests
	uvx ruff check --fix src tests
	@npx prettier --write --print-width 150 "*.{md,yml,yaml}" "**/*.{md,yml,yaml}" --no-error-on-unmatched-pattern

test: fmt
	uv run --group dev --locked pytest tests

publish: test
	uv build
	uv publish --verbose

debug: fmt
	uv run pifr $(filter-out $@,$(MAKECMDGOALS))

patch: fmt
	uv run bump-my-version bump patch pyproject.toml

%:
	@:
