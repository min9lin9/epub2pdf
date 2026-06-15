: Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.3] - 2026-06-14

### Added
- `--sidecar-jsonl` option for `convert` and `batch` commands.
- New `epub2pdf_cli.jsonl` module that writes one AI-friendly JSON object per EPUB chapter.
- JSONL sidecar support in the MCP server tools (`convert_epub`, `batch_convert`).

## [0.3.4] - 2026-06-15

### Fixed
- Handle EPUB package documents that use the `opf:` prefix without declaring `xmlns:opf`. This makes conversion work for more real-world EPUBs, including Korean-language titles from Anna’s Archive.

## [0.3.2] - 2026-06-14

### Fixed
- Read `__version__` from package metadata to keep CLI `--version` in sync with releases.
- Remove unsupported `print-color-adjust` CSS properties from the default stylesheet to eliminate WeasyPrint warnings.

## [0.3.1] - 2026-06-14

### Fixed
- Include `weasyprint` in the default package dependencies so that `pip install epub2pdf-cli` works out of the box.
- Update missing-dependency hints to reference the PyPI package name (`epub2pdf-cli[{extra}]`).

## [0.3.0] - 2026-06-13

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

[Unreleased]: https://github.com/min9lin9/epub2pdf/compare/v0.3.4...HEAD
[0.3.4]: https://github.com/min9lin9/epub2pdf/compare/v0.3.3...v0.3.4
[0.3.3]: https://github.com/min9lin9/epub2pdf/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/min9lin9/epub2pdf/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/min9lin9/epub2pdf/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/min9lin9/epub2pdf/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/min9lin9/epub2pdf/releases/tag/v0.2.0
