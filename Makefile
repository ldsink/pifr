fmt:
	pdm run ruff format src
	pdm run ruff check --fix src

publish:
	pdm publish --verbose

debug: fmt
	pdm build
	pipx uninstall pifr
	pipx install --force dist/pifr-0.0.0-py3-none-any.whl
	pifr --help
	pifr list