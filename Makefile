fmt:
	pdm run ruff format src
	pdm run ruff check --fix src

publish:
	pdm publish --verbose

debug: fmt
	pdm build
	pipx uninstall pifr
	pipx install --force dist/*.whl
	pifr pull --verbose ldsink docker.n8n.io/n8nio/n8n:1.79.3

patch: fmt
	pdm run bump-my-version bump patch pyproject.toml
