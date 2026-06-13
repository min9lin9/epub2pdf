:description: Release cadence and checklist for epub2pdf.

# Release Process

This document complements `CONTRIBUTING.md` with a maintainer-level checklist and cadence.

## Cadence

| Release type | Trigger | Frequency |
|---|---|---|
| Patch | Bug fix or docs correction merged | As needed |
| Minor | New optional backend, small feature, or accumulated improvements | Monthly, if changes exist |
| Major | Milestone completion with breaking changes | Rare; with migration guide |
| Pre-release | Experimental feature or large refactor | As needed |

## Release checklist

1. Ensure `main` is green (CI, Security, Docker).
2. Update `src/epub2pdf_cli/__init__.py` and `pyproject.toml` version.
3. Update `CHANGELOG.md` under the new version.
4. Create a release PR if the change is more than a patch; otherwise proceed directly.
5. After merge, push a signed or annotated tag:
   ```bash
   git tag -a v0.3.1 -m "Release v0.3.1"
   git push origin v0.3.1
   ```
6. Verify workflows:
   - `release.yml` publishes to PyPI.
   - `docker.yml` publishes to GHCR.
7. Create a GitHub Release with auto-generated notes and edit as needed.
8. Close the milestone if applicable.

## Versioning

Follow [Semantic Versioning](https://semver.org/):

- `MAJOR` for incompatible CLI, API, or sidecar schema changes.
- `MINOR` for backward-compatible new features.
- `PATCH` for backward-compatible bug fixes.

## Rollback

If a release is broken:

1. Yank the broken version from PyPI if possible.
2. Publish a patch release immediately.
3. Document the incident in `CHANGELOG.md` and a GitHub Discussion.
