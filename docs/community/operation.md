:description: How the epub2pdf community operates: communication, triage, releases, and reviews.

# Community Operation

This document defines the day-to-day operation of the `epub2pdf` project. It is intended for contributors, reviewers, and maintainers.

## Communication channels

| Channel | Purpose | Link |
|---|---|---|
| GitHub Issues | Bug reports, feature requests, concrete tasks | https://github.com/min9lin9/epub2pdf/issues |
| GitHub Discussions | Questions, ideas, announcements, usage help | https://github.com/min9lin9/epub2pdf/discussions |
| Discord (future) | Real-time chat, office hours, casual questions | To be created when critical mass exists |

See [docs/community/discussions.md](discussions.md) for the onboarding flow and category guide.

Until there is a critical mass of contributors, **GitHub Discussions** is the primary real-time-ish channel.

## Issue triage

Triage happens weekly. Maintainers label incoming issues within 7 days:

1. Apply a `type:*` label.
2. Apply an `area:*` label.
3. Apply a `difficulty:*` label when the scope is clear.
4. Apply `status: needs triage` if the issue is not yet understood.
5. Remove `status: needs triage` once the next step is decided.

If an issue is unclear, ask the reporter for more information and mark it `status: needs triage`.

## Release rhythm

- **Patch releases** (bug fixes, docs): on demand, no fixed schedule.
- **Minor releases** (new optional backends, small features): once per month if there are merged changes.
- **Major releases** (breaking changes): only after a milestone is complete and a migration guide is published.
- **Pre-releases** (`a`, `b`, `rc`): for experimental features and large refactors.

Release steps are in `CONTRIBUTING.md`.

## Pull request review rotation

- The Project Lead assigns reviewers based on `CODEOWNERS` and area labels.
- If a reviewer is inactive for 7 days, another maintainer may take over.
- PRs from first-time contributors should receive a friendly review within 3 days.
- AI-generated PRs require explicit human review; do not rely on CI alone.

## Maintainer criteria

A contributor may be invited to become a Maintainer after:

- At least 5 merged, non-trivial PRs.
- Consistent, constructive code review participation.
- Demonstrated understanding of the project values and contribution guidelines.
- Willingness to participate in triage and releases.

Maintainer access may be revoked for repeated code-of-conduct violations, merging without required checks, or extended inactivity without notice.

## Contributor recognition

- Release notes credit external contributors by GitHub handle.
- Significant contributors are listed in `GOVERNANCE.md`.
- Good first issue helpers receive a thank-you in the monthly discussion summary.

## Decision log

Important decisions made outside GitHub issues (e.g., Discord voice chats, office hours) must be summarized in a GitHub Discussion or issue within 48 hours.
