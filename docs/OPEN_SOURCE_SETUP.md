# Open Source Setup Guide for epub2pdf

This document records the decisions and checklist for operating `epub2pdf` as a public open-source repository.

---

## 0. Initial setup principles

### 0.1 Purpose of opening the repository

Make the CLI, Python API, MCP server, and agent skill wrappers available to the public so that users and contributors can improve EPUB-to-PDF conversion and PDF extraction together.

### 0.2 What is public now

- Source code under `src/epub2pdf_cli/`.
- CLI, API, batch pipeline, rendering engines, extraction backends.
- Docker image build files and GitHub Actions workflows.
- Codex/OpenCode skill wrappers under `integrations/`.

### 0.3 What is not public yet

- Private release tokens or signing keys.
- Any personal test files or copyrighted EPUBs/PDFs used in development.
- Maintainer-only infrastructure (PyPI credentials, GitHub environments).

### 0.4 Principles for external contributions

- Open an issue before proposing large changes.
- Every PR must pass CI and maintainer review.
- Documentation and tests are required alongside code changes.
- AI-assisted contributions are allowed but must be disclosed and human-reviewed.

### 0.5 AI-generated contribution policy

- Disclosure is required.
- The human contributor must understand and be able to explain every change.
- Large AI-generated refactors or dependency additions are rejected by default.
- See `CONTRIBUTING.md` and the `ai_contribution.yml` issue template.

### 0.6 "Contract, test, and review before merge" principle

Changes that break the CLI output format, sidecar schema, PDF text-layer guarantee, or base-install dependencies must be discussed, tested, and documented before merging.

---

## 1. Repository basics

| Item | Value |
|---|---|
| Repository name | `epub2pdf` (see name candidates in the release plan) |
| Owner | `min9lin9` |
| Visibility | Public |
| Default branch | `main` |
| License | MIT |
| Topics | `epub`, `pdf`, `cli`, `converter`, `mcp`, `ai-readable`, `python` |
| One-line description | Local CLI to convert EPUB files into searchable, AI-readable PDFs. |

---

## 2. Top-level directory structure

```text
.github/          GitHub templates, workflows, CODEOWNERS
docs/             Architecture and open-source setup documents
examples/         Example scripts and sample workflows (future)
integrations/     Codex and OpenCode skill wrappers
scripts/          Utility scripts (skill installer, label setup)
src/              Source code
tests/            Unit and integration tests
README.md         Project overview
LICENSE           MIT license
CHANGELOG.md      Release history
CONTRIBUTING.md   Contributor guide
CODE_OF_CONDUCT.md  Community standards
SECURITY.md       Vulnerability reporting
GOVERNANCE.md     Roles and decision making
ROADMAP.md        Project roadmap
```

---

## 3. Root documents

| File | Purpose |
|---|---|
| `README.md` | Quick start, installation, CLI reference, guarantees, limitations |
| `CONTRIBUTING.md` | Development setup, branch naming, PR standards, AI policy |
| `CODE_OF_CONDUCT.md` | Expected behavior, technical criticism, spam PR handling |
| `SECURITY.md` | Private vulnerability reporting, scope, disclosure policy |
| `GOVERNANCE.md` | Roles (Project Lead, Maintainer, Contributor, Reviewer) |
| `ROADMAP.md` | Phases from repository health to community operation |
| `CHANGELOG.md` | Versioned change history |
| `LICENSE` | MIT license |

---

## 4. GitHub settings

### 4.1 Default branch

`main`

### 4.2 `main` branch protection

Enable these rules:

- [ ] Require a pull request before merging.
- [ ] Require approvals: at least 1.
- [ ] Dismiss stale PR approvals when new commits are pushed.
- [ ] Require review from CODEOWNERS.
- [ ] Require status checks to pass:
  - `test` (CI unit tests)
  - `lint-and-type` (format, lint, type check)
  - `dependency-scan` (security)
  - `codeql` (security)
- [ ] Require branches to be up to date before merging.
- [ ] Restrict pushes that create files larger than 100 MB.
- [ ] Do not allow bypassing the above settings.
- [ ] Do not allow force pushes.
- [ ] Do not allow deletions.

### 4.3 Pull request settings

- Allow squash merging (preferred).
- Allow merge commits (optional).
- Allow rebase merging (optional).
- Auto-merge: disabled until the project has more maintainers.
- Draft PRs are encouraged for early feedback.

### 4.4 Issue and discussion settings

- Issues: enabled.
- Discussions: enabled for questions and ideas.
- Wiki: disabled (documentation lives in `docs/` and `README.md`).
- Projects: enabled for milestone tracking.

---

## 5. `.github/` directory

### 5.1 `PULL_REQUEST_TEMPLATE.md`

Includes summary, related issue, change type, test results, contract check, documentation update, AI usage, risk scope, and checklist.

### 5.2 `ISSUE_TEMPLATE/bug_report.yml`

Collects version, Python version, OS, command, expected/actual behavior, and a minimal reproducer.

### 5.3 `ISSUE_TEMPLATE/feature_request.yml`

Collects problem, solution, alternatives, and scope check.

### 5.4 `ISSUE_TEMPLATE/ai_contribution.yml`

Collects AI tools used, human review scope, changed files, tests, contract checks, explainable areas, and risks.

### 5.5 `ISSUE_TEMPLATE/documentation.yml`

Collects document location, reason for change, suggested wording, and related code.

### 5.6 `CODEOWNERS`

Default owner: `@min9lin9` for all tracked paths. Expand as more maintainers join.

### 5.7 `workflows/ci.yml`

Checks out code, installs dependencies, runs format/lint/type checks, unit tests with coverage gate, and build check.

### 5.8 `workflows/security.yml`

Runs dependency scan (`pip-audit`), secret scan (`trufflehog`), and CodeQL code scanning.

---

## 6. Label system

Run `python3 scripts/setup_labels.py` to create the initial label set, or create them manually.

### 6.1 `type:*`

- `type: bug`
- `type: feature`
- `type: docs`
- `type: refactor`
- `type: test`
- `type: security`

### 6.2 `status:*`

- `status: needs triage`
- `status: accepted`
- `status: in progress`
- `status: blocked`
- `status: needs review`
- `status: wontfix`

### 6.3 `area:*`

- `area: cli`
- `area: render`
- `area: extract`
- `area: pipeline`
- `area: mcp`
- `area: docker`
- `area: docs`
- `area: infra`

### 6.4 `difficulty:*`

- `difficulty: good first issue`
- `difficulty: help wanted`
- `difficulty: advanced`

### 6.5 `risk:*`

- `risk: breaking-change`
- `risk: security-sensitive`
- `risk: ai-generated`
- `risk: experimental`

---

## 7. Milestones

| Milestone | Goal |
|---|---|
| M0: Repository Health | All community files, templates, branch protection, and labels in place |
| M1: Architecture Stabilization | Renderer protocol, sidecar schema, contract tests finalized |
| M2: Contributor Onboarding | Dev setup docs, examples, good first issues |
| M3: Community Operation | Regular triage, release rhythm, maintainer rotation |

---

## 8. Architecture documents

Planned under `docs/architecture/`:

- `overview.md` — components and data flow
- `renderer-contract.md` — renderer protocol and engine responsibilities
- `extraction-contract.md` — PDF extraction backend contract
- `sidecar-schema.md` — JSON sidecar structure and compatibility rules
- `mcp-integration.md` — MCP server and agent integration design

---

## 9. AI contribution policy

- AI use is allowed.
- Disclosure is required in the PR template.
- Human must review every changed line.
- No unexplained code is accepted.
- Large AI-generated PRs are rejected by default.
- AI-generated dependency additions, security code, and refactors require extra review.

---

## 10. Testing and contract checks

- Unit tests: `pytest`
- Coverage gate: 60% minimum
- Lint/format: `ruff`
- Type check: `mypy`
- Build check: `python -m build`
- Contract checks: PDF text-layer validation, sidecar schema validation
- Docs consistency: README examples are tested where feasible

---

## 11. Security settings

- Enable GitHub secret scanning.
- Enable Dependabot alerts and security updates.
- Enable CodeQL code scanning.
- Add `SECURITY.md` vulnerability reporting policy.
- Store PyPI credentials only through trusted publishing, never in repository secrets.

---

## 12. Release operation

- Follow semantic versioning.
- Pre-releases for experimental features.
- Stable releases after contract tests pass.
- Tag format: `v0.3.0`.
- Update `CHANGELOG.md` before tagging.
- Trusted publishing to PyPI and GHCR via GitHub Actions.

---

## 13. Community operation

- Use GitHub Discussions for questions and ideas.
- Keep bug reports and feature requests in Issues.
- Recognize contributors in release notes.
- Avoid Discord until there is a critical mass of contributors.

---

## 14. Initial good first issues

- Fix README typos or outdated CLI examples.
- Add unit tests for `epub` parsing edge cases.
- Document WeasyPrint system library installation per OS.
- Add an example batch-conversion shell script.
- Improve error messages for missing system dependencies.

---

## 15. Initial PR plan

| PR | Contents |
|---|---|
| PR #1 | Repository health files: README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, GOVERNANCE, ROADMAP |
| PR #2 | GitHub templates: issue templates, PR template, CODEOWNERS, labels |
| PR #3 | CI baseline: format, lint, type check, tests, coverage, build |
| PR #4 | Security baseline: dependency scan, secret scan, CodeQL |
| PR #5 | Architecture docs: overview, renderer/extraction contracts, sidecar schema |

---

## 16. Completion criteria

- [ ] A newcomer can understand the project from the README.
- [ ] A contributor can find a good first issue.
- [ ] `main` is protected.
- [ ] PR and issue templates are active.
- [ ] CODEOWNERS is configured.
- [ ] CI passes on `main`.
- [ ] Security reporting path exists.
- [ ] AI contribution policy is documented.
- [ ] At least one `good first issue` is open.

---

## 17. Work order

1. Finalize repository name and create the public repository.
2. Push the updated files (README, LICENSE, templates, workflows).
3. Configure branch protection and required status checks.
4. Run `scripts/setup_labels.py`.
5. Create milestones M0–M3.
6. Enable security scanning in repository settings.
7. Open good first issues.
8. Announce public availability.

---

## 18. Operating principles

- Anyone can propose changes.
- Not every proposal is merged.
- Large features start with an issue.
- AI-generated code must be explainable by a human.
- Contract-breaking changes require discussion.
- Undocumented architectural changes are rejected.
- Security changes get separate review.
- Speed is less important than trust in the early stage.
