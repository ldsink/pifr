# Repository Guidelines

## Project Structure & Module Organization

`pifr` is a small Python command-line tool for pulling Docker images through an SSH host. Package code lives in `src/pifr/`. `main.py` defines the Click command group and the `list`, `pull`, and `push` commands; keep command implementations in `src/pifr/commands/`. `host.py` reads and displays SSH configuration, while `ssh.py` runs the remote Docker workflow. Project metadata, dependencies, Ruff settings, and the CLI entry point are in `pyproject.toml`; `Makefile` contains common release and local-debug tasks. Tests live in `tests/`.

## Documentation Guidelines

When updating a README, update all language versions in the same change (currently `README.md` and `README.zh-CN.md`). Keep their sections, instructions, command examples, and links consistent in meaning, and preserve the language-switch links in each file.

## Build, Test, and Development Commands

Use Python 3.10+ and uv for the development environment.

- `uv sync --group dev` installs the locked runtime and development dependencies.
- `uv run pifr --help` runs the CLI from the working tree; use `uv run pifr list` to inspect SSH hosts.
- `make fmt` formats `src/` and `tests/` and applies safe Ruff fixes.
- `make test` formats code and runs the pytest suite.
- `uvx ruff check src` verifies linting without changing files.
- `uv build` creates wheel and source distributions in `dist/`.
- `make debug <args>` formats code then runs `uv run pifr <args>` from the working tree, e.g. `make debug pull host image` or `make debug -- --help` for flags.

## Coding Style & Naming Conventions

Follow the existing Python style: four-space indentation, type annotations on public functions, `snake_case` for functions and variables, `PascalCase` for classes such as `HostInfo`, and concise Click command functions. Prefer `pathlib.Path` for filesystem work and keep terminal output in Click/Rich helpers. Ruff targets Python 3.13, uses a 150-character line limit, and enforces import ordering and security-oriented rules. Run `make fmt` before committing.

## Testing Guidelines

Use pytest for focused tests under `tests/` named `test_<feature>.py`. Avoid tests that require a real SSH host or Docker daemon; mock subprocess and filesystem boundaries instead. Run `make test` and exercise affected CLI paths with `uv run pifr --help` or a safe `list` invocation.

## Commit & Pull Request Guidelines

Recent history follows Conventional Commit-style prefixes: `feat:`, `fix:`, `docs:`, `chore:`, and `ci:`. Write imperative, scoped summaries, for example `fix: handle empty SSH host entries`. Keep commits focused. Pull requests should explain the user-visible change, note validation performed, link any relevant issue, and include terminal output or screenshots when CLI output changes. Do not commit generated `dist/`, virtual-environment, or cache artifacts.

- Branch names must not contain `/`; use `-` to separate words (for example `feat-add-ssh-timeout`, not `feat/add-ssh-timeout`).
- Each commit or pull request should implement exactly one feature or fix exactly one bug; do not modify unrelated code unless it is necessary to complete the change.
