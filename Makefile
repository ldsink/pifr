debug:
	pdm build
	pipx install --force dist/pifr-0.0.0-py3-none-any.whl
	pifr --name Wink