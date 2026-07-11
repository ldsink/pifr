fmt:
	uvx ruff format src
	uvx ruff check --fix src
	@npx prettier --write --print-width 150 "*.{md,yml,yaml}" "**/*.{md,yml,yaml}" --no-error-on-unmatched-pattern

publish:
	uv build
	uv publish --verbose

debug: fmt
	uv run pifr $(filter-out $@,$(MAKECMDGOALS))

patch: fmt
	uv run bump-my-version bump patch pyproject.toml

%:
	@:
