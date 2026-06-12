# epub2pdf Product Plan: Toward a 9.8+ Open-Source Project

## 1. Vision & Positioning

**One-line mission**
> The fastest, most reliable, and AI-friendly way to turn EPUBs into searchable, machine-readable PDFs — locally, offline, and at any scale.

**Why this matters**
- EPUB → PDF is a universal need (publishing, academia, archival, LLM/RAG pipelines).
- Existing tools are either GUI-heavy, cloud-locked, or depend on Chromium/Java.
- A CLI-first, renderer-pluggable, benchmark-driven tool fills a clear gap.

**Target rating definition**
"9.8+" means external users choose this tool repeatedly because it is:
- **Reliable**: works on real-world EPUBs out of the box.
- **Fast**: batch processing is orders of magnitude faster than one-off browser rendering.
- **Transparent**: benchmarks, changelogs, and architecture are public.
- **Respectful**: clear docs, no telemetry without consent, predictable releases.

## 2. Target Users & Personas

| Persona | Pain | How epub2pdf wins |
|---|---|---|
| **Technical writer / publisher** | Needs PDFs from EPUBs for distribution. | Stable CLI, sidecars, batch conversion. |
| **Data engineer / ML pipeline** | Ingests EPUBs into RAG/LLM systems. | Markdown/HTML/JSON sidecars, extraction APIs. |
| **Librarian / archivist** | Converts large collections reproducibly. | Parallel batch, deterministic output, hashes in reports. |
| **Open-source contributor** | Wants to fix a focused problem. | Clean layered architecture, tests, good-first-issues. |
| **CI/CD operator** | Needs headless conversion in pipelines. | Docker image, no browser by default, exit codes. |

## 3. Success Metrics (9.8+ Bar)

### Quantitative
- **Test coverage ≥ 90%** (unit + integration).
- **CI pass rate ≥ 99%** on `main`.
- **Mean time to first success ≤ 2 minutes** from `pip install` to first PDF.
- **Batch throughput**: ≥ 10 medium EPUBs/minute on 4 cores with Playwright pool.
- **Crash rate**: zero unhandled exceptions on supported inputs.
- **PyPI/conda downloads** and GitHub stars tracked monthly.

### Qualitative
- Issue response time < 48 hours.
- PR review time < 72 hours.
- Every release has a migration guide.
- No breaking change without a deprecation cycle.

## 4. Product Pillars

### Pillar A — Reliability
- Render any valid EPUB 2/3 to a text-searchable PDF.
- Graceful degradation for malformed/corrupt EPUBs (warnings, not crashes).
- Deterministic output: same input → same bytes on the same version.
- Extensive fixture library: synthetic + real-world EPUBs.

### Pillar B — Performance
- WeasyPrint default for zero external-browser dependency.
- Playwright browser pool for throughput-oriented users.
- Parallel batch with process-level workers.
- Public benchmark dashboard (`scripts/benchmark.py`, `scripts/real_world_benchmark.py`).

### Pillar C — Developer Experience (DX)
- One-line install: `pip install epub2pdf`.
- Clear error messages with actionable next steps.
- Sidecars (JSON/HTML/Markdown) for downstream automation.
- Stable CLI and Python API.
- Progress bars and verbose logs for long-running batch jobs.

### Pillar D — Community & Sustainability
- Contributor Covenant Code of Conduct.
- `CONTRIBUTING.md` with setup, testing, and review guidelines.
- Issue/PR templates.
- Public roadmap and release notes.
- Optional sponsorship / GitHub Sponsors for sustained maintenance.

### Pillar E — Security & Trust
- No network calls unless explicitly requested (e.g., benchmark downloads).
- Opt-in telemetry only.
- SBOM and dependency scanning in CI.
- Signed releases and PyPI trusted publishing.

## 5. Roadmap

### Phase 0 — Foundation (Now → 2 weeks)
- [ ] Merge current feature set (batch, API, benchmarks) and tag `v0.3.0`.
- [ ] Add `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates.
- [ ] Publish to PyPI with trusted publishing.
- [ ] Add Docker image and installation one-liner.
- [ ] Lock dependency versions and add `requirements-lock.txt`.

### Phase 1 — Hardening (2–6 weeks)
- [ ] Achieve ≥ 90% test coverage.
- [ ] Fuzz/corpus-test with 50+ real EPUBs from Project Gutenberg.
- [ ] Add regression tests for every reported bug.
- [ ] Introduce progress bars for `batch`.
- [ ] Add `--dry-run` mode.
- [ ] Stabilize Python API and document breaking changes policy.

### Phase 2 — Scale & Observability (6–12 weeks)
- [ ] Add a `watch` mode for hot-folder conversion.
- [ ] Plugin system for custom renderers/extractors.
- [ ] Built-in conversion report server/JSONL log.
- [ ] Performance regression gate in CI (fail if benchmark degrades > 10%).
- [ ] Conda / Homebrew / apt packages.

### Phase 3 — Ecosystem (3–6 months)
- [ ] GitHub Action for `epub2pdf` in CI pipelines.
- [ ] Pre-commit hook.
- [ ] Optional cloud-friendly streaming for S3/GCS inputs.
- [ ] Translated documentation (Korean, English at minimum).
- [ ] Community benchmark leaderboard.

## 6. Quality Bar

### Testing
- Unit tests for every pure function.
- Integration tests for every CLI command.
- Renderer parity tests: WeasyPrint and Playwright must produce text-equivalent PDFs.
- Memory tests for large EPUBs (e.g., > 1000 pages).
- Fuzz tests: corrupt zip, missing files, invalid CSS.

### Benchmarking
- Run `scripts/benchmark.py` on every PR that touches rendering.
- Store benchmark results in `docs/benchmarks/` per release.
- Alert on regression in wall-clock time or memory.

### Security
- `bandit` and `pip-audit` in CI.
- No execution of user-provided strings.
- Sandboxed renderer subprocess option.

## 7. Distribution & Packaging

| Channel | Goal |
|---|---|
| PyPI | Primary install: `pip install epub2pdf` |
| Docker | `ghcr.io/min9lin9/epub2pdf` for CI/CD |
| Homebrew | `brew install epub2pdf` for macOS users |
| apt | `.deb` via GitHub Releases for Linux users |
| conda-forge | For data-science ecosystems |

## 8. Community & Governance

- **Decision making**: Maintainer consensus for architecture; community input via RFC issues.
- **Communication**: GitHub Discussions for questions, Issues for bugs/features.
- **Releases**: SemVer; monthly minor releases, weekly patch releases if needed.
- **Maintainer ladder**: contributor → triager → maintainer.

## 9. Monetization (Sustainability, Not Paywall)

- GitHub Sponsors for individuals.
- Corporate sponsorship tier for priority support / roadmap input.
- Consulting or hosted CI integration as optional revenue, never required for core features.

## 10. Risks & Mitigation

| Risk | Mitigation |
|---|---|
| WeasyPrint system-library friction | Provide Docker image and install scripts per OS. |
| Playwright security concerns | Keep browser pool optional; document sandboxing. |
| Contributor burnout | Clear onboarding, automated releases, sponsor funding. |
| Scope creep | Strict core scope (EPUB ↔ PDF); reject non-core features politely. |
| Benchmark flakiness | Pin dependencies; run on dedicated CI runner. |

## 11. Immediate Action Items

1. Create `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates.
2. Tag `v0.3.0` and publish to PyPI.
3. Add Docker build to CI.
4. Add coverage reporting to CI (codecov).
5. Write `docs/ARCHITECTURE.md` explaining the layered design.
6. Set up GitHub Sponsors and Discussions.
7. Announce on relevant communities (HN, Reddit r/selfhosted, Python Discord).
