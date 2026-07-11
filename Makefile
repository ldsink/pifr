fmt:
	uv run ruff format src
	uv run ruff check --fix src

publish:
	uv build
	uv publish --verbose

debug: fmt
	uv build
	pipx uninstall pifr
	pipx install --force dist/*.whl
	pifr pull --verbose ldsink docker.n8n.io/n8nio/n8n:1.79.3

patch: fmt
	uv run bump-my-version bump patch pyproject.toml
