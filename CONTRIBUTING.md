# Contributing to epub2pdf

Thank you for considering a contribution! This document will get you started.

## Before you contribute

- Read the [README](README.md), [Code of Conduct](CODE_OF_CONDUCT.md), and [Security Policy](SECURITY.md).
- Check existing issues and pull requests to avoid duplicates.
- For security-sensitive issues, follow the private reporting process in `SECURITY.md`.

## When to open an issue first

Open an issue before a pull request if you are proposing:

- A new CLI command or subcommand.
- A new rendering engine or extraction backend.
- Breaking changes to the sidecar schema, CLI flags, or public API.
- Refactoring that affects multiple packages or public interfaces.
- Changes to the Docker image base, entry point, or default behavior.

## When a pull request is fine without an issue

Small, well-scoped changes can usually skip the issue step:

- Bug fixes with a clear reproduction.
- Documentation fixes and clarifications.
- Additional tests for existing behavior.
- Typo fixes, dependency patch updates, or CI hygiene.

## Development setup

```bash
# Clone the repository
git clone https://github.com/min9lin9/epub2pdf.git
cd epub2pdf

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode with all optional dependencies
python3 -m pip install -e '.[all,dev,playwright,weasyprint]'
python3 -m playwright install chromium
```

## Running tests

```bash
PYTHONPATH=src python3 -m pytest -q
```

With coverage gate:

```bash
PYTHONPATH=src python3 -m pytest -q --cov=epub2pdf_cli --cov-fail-under=60
```

## Code quality

We use `ruff` for linting/formatting and `mypy` for type checking. Run both before committing:

```bash
python3 -m ruff check src tests
python3 -m mypy src
```

## Branch naming

Use lowercase, hyphen-separated names with a type prefix:

- `fix/<short-description>` for bug fixes
- `feature/<short-description>` for new features
- `docs/<short-description>` for documentation
- `refactor/<short-description>` for refactorings
- `test/<short-description>` for test-only changes
- `deps/<dependency-name>` for dependency updates

Example: `fix/weasyprint-margin-calculation`.

## Commit messages

- Use the imperative mood (`Add`, `Fix`, `Refactor`, `Update`).
- Keep the first line under 72 characters.
- Add a body when the change needs explanation, especially for breaking changes.
- Reference issues and PRs where relevant.

Example:

```text
Fix pypdfium2 extraction for encrypted PDFs

The extraction path did not pass the user-provided password to
pypdfium2. This change threads the password through the adapter and
adds a regression test.

Closes #123
```

## Pull request standards

Every PR must:

1. Pass CI (format, lint, type check, tests, coverage gate, build check).
2. Include tests for new behavior.
3. Update relevant documentation (`README.md`, `docs/`, or inline docstrings).
4. Fill out the PR template, including the change type, test results, and AI usage disclosure.
5. Be reviewed and approved by at least one maintainer.

## Documentation changes

- Update `README.md` if the change affects installation, quick start, CLI flags, or guarantees.
- Add or update `docs/` pages for architecture, protocol, or extension changes.
- Update `CHANGELOG.md` under the unreleased section.

## AI-generated contributions

AI-assisted contributions are allowed, but the human contributor is responsible for them.

- Disclose AI usage in the PR description using the PR template checkbox.
- Review every changed line yourself. Do not submit code you cannot explain.
- Do not let AI add new dependencies, security-sensitive code, or large refactors without extra scrutiny.
- Keep AI-generated PRs small and focused. Large AI-generated refactors will be rejected.
- If a change was suggested by AI, you must be able to justify it in review.

## Proposing large changes

1. Open an issue describing the problem, proposed solution, and alternatives.
2. Wait for maintainer feedback before writing code.
3. If accepted, open a draft PR early and keep changes incremental.
4. Expect review rounds. Large changes may require multiple reviewers.

## Release process

1. Update `src/epub2pdf_cli/__init__.py` and `pyproject.toml` to the new version.
2. Update `CHANGELOG.md`.
3. Push a signed tag: `git tag -s v0.3.0 -m "Release v0.3.0"`.
4. Push the tag: `git push origin v0.3.0`.
5. The `release.yml` workflow will publish to PyPI via trusted publishing.
6. The `docker.yml` workflow will push the image to GHCR.

Before the first release, enable trusted publishing on PyPI:
- Go to **Account settings → Publishing** on PyPI.
- Add a pending publisher for the project `epub2pdf-cli` (or let it be created on first upload).
- Use repository `min9lin9/epub2pdf` and workflow `release.yml`.
- Make sure a `pypi` environment exists in the repository settings.

## Reporting bugs

Please include:
- The exact command you ran.
- The EPUB or a minimal reproducer (if possible).
- The output of `epub2pdf --version`.
- Your OS and Python version.
- Whether the issue is reproducible with `--no-validate` or a different engine.

## Questions?

Use [GitHub Discussions](https://github.com/min9lin9/epub2pdf/discussions) for questions and ideas.
