# Roadmap

This roadmap is a living document. Priorities may shift based on community feedback and maintainer capacity.

## Phase 0: Repository Health

- [x] README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, GOVERNANCE, ROADMAP
- [x] Issue and PR templates
- [x] CODEOWNERS
- [x] CI with tests, lint, type check, coverage gate
- [x] PyPI trusted publishing and Docker image publishing
- [x] Public repository visibility
- [x] Good first issues published

## Phase 1: Core Architecture Stabilization

- [x] Finalize renderer protocol and engine plugin interface.
- [x] Standardize sidecar schema and document backward-compatibility rules.
- [x] Improve contract tests for EPUB-to-PDF text fidelity.
- [x] Add deterministic regression tests for batch conversion.
- [x] Refactor pipeline so `inspect`, `convert`, and `pdf-extract` share the same configuration model.

## Phase 2: Contributor Onboarding

- [x] Document development environment setup for macOS, Linux, and Docker.
- [x] Add examples: custom renderer plugin, custom extraction backend, batch script.
- [x] Add good first issues for documentation, tests, and small features.
- [ ] Improve error messages and logging for first-time users.

## Phase 3: Extended Backends and Integrations

- [ ] Evaluate OCR backend for image-only EPUBs and scanned PDFs.
- [ ] Improve table extraction across `docling`, `pdfplumber`, and `opendataloader`.
- [ ] Add more MCP tools and clarify permission model.
- [ ] Consider a plugin ecosystem for third-party renderers and extractors.

## Phase 4: Community and Ecosystem

- [x] Monthly issue triage and release rhythm.
- [x] Maintainer rotation and review guidelines.
- [ ] Discord or GitHub Discussions onboarding flow.

## What we will NOT do

- Turn `epub2pdf` into a hosted SaaS or long-lived server.
- Accept raster-only output as the default; searchable text remains the core guarantee.
- Add DRM handling or EPUB decryption features.
