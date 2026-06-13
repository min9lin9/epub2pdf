# Governance

This document describes how the `epub2pdf` project is governed and how decisions are made.

## Roles

### Project Lead

- Owns the overall direction, roadmap priorities, and release schedule.
- Has final say on architectural decisions and breaking changes.
- Currently: the repository owner (`min9lin9`).

### Maintainers

- Review and merge pull requests.
- Triage issues and discussions.
- Enforce the code of conduct and contribution guidelines.
- Ensure CI, tests, and security checks pass before merging.

### Contributors

- Anyone who opens an issue, discussion, or pull request.
- Contributors do not need permission to propose changes; maintainers decide whether to accept them.

### Reviewers

- Contributors with domain expertise who are asked to review specific areas (rendering, extraction, Docker, documentation, etc.).
- Review approval is not the same as merge permission.

## Decision making

- **Routine changes**: bug fixes, documentation updates, small features. A maintainer reviews and merges after CI passes.
- **Significant changes**: new engines, new CLI commands, breaking changes, major refactorings. Require an issue and discussion before a PR is opened. The Project Lead makes the final decision.
- **Disputes**: If reviewers disagree, the Project Lead resolves the dispute. Decisions are documented in the issue or PR thread.

## Review rotation

- CODEOWNERS and area labels determine the default reviewer for a PR.
- The Project Lead may reassign reviewers to balance load or match expertise.
- If a PR has no review activity for 7 days, any maintainer may step in.
- Reviewers should respond to first-time contributors within 3 business days.

## Maintainer appointment

A contributor may be invited to become a Maintainer after:

- At least 5 merged, non-trivial PRs or equivalent documentation/architecture work.
- Consistent, constructive code review participation over at least 2 months.
- Demonstrated understanding of the project values and contribution guidelines.
- Willingness to participate in weekly triage and monthly release rhythm.

## Maintainer removal

Maintainer access may be revoked for:

- Repeated violation of the code of conduct.
- Merging changes that bypass required checks without documented justification.
- Extended inactivity without prior notice.

## Transparency

- Roadmap, milestones, and significant decisions are tracked in GitHub issues, milestones, and `ROADMAP.md`.
- Maintainer meetings, if held, will have notes posted as a discussion or issue summary.
