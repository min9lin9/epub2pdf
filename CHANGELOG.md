: Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Parallel `batch` CLI command with `--workers` support.
- `Epub2Pdf` Python API with browser pooling and `batch_convert(max_workers=...)`.
- `--no-validate` flag for faster conversion pipelines.
- `--sidecar-json` flag for `pdf-extract`.
- Per-stage timings for `convert` and `pdf-extract` pipelines.
- Real-world benchmark script with Project Gutenberg fixtures and memory profiling.
- Public product plan, architecture docs, and community templates.
- PyPI trusted publishing workflow.
- Docker image and GitHub Container Registry workflow.
- CI coverage reporting with Codecov upload.
- Dependabot configuration for pip and GitHub Actions.

### Changed
- Default renderer is now WeasyPrint; Playwright is optional.
- Default PDF extractor is now pypdfium2 (no Java required by default).

## [0.2.0] - 2026-06-12

### Added
- Refactored layered architecture (epub, html, render, pdf, pipeline).
- Markdown sidecar generation.
- Stage timing instrumentation.
- Synthetic benchmark script.

### Changed
- Replaced default Chromium/Java backends with WeasyPrint/pypdfium2.
