:description: Issue and pull request triage guide for maintainers.

# Triage Guide

This guide helps maintainers keep the issue and PR backlog healthy.

## Issue triage

New issues should be triaged within 7 days.

### Step 1: Apply type and area labels

- `type: bug` — something is broken
- `type: feature` — new capability
- `type: docs` — documentation
- `type: refactor` / `type: test` / `type: security`
- `area: cli`, `area: render`, `area: extract`, `area: pipeline`, `area: mcp`, `area: docker`, `area: docs`, `area: infra`

### Step 2: Apply difficulty labels when clear

- `difficulty: good first issue` — suitable for newcomers
- `difficulty: help wanted` — community help appreciated
- `difficulty: advanced` — requires deep context

### Step 3: Set status

- `status: needs triage` — not yet understood
- `status: accepted` — accepted, waiting for implementation
- `status: in progress` — someone is working on it
- `status: blocked` — blocked by another issue or decision
- `status: wontfix` — explicitly out of scope

### Step 4: Assign milestones

- Attach accepted issues to the relevant milestone (M0–M3 or future).

## Pull request triage

- Ensure the PR template is filled out.
- Verify the PR has the correct `type:*` and `risk:*` labels.
- Request changes if CI is failing or documentation is missing.
- Assign reviewers based on `CODEOWNERS` and area labels.

## Closing stale items

- Issues with `status: needs triage` and no response for 30 days may be closed with a note.
- PRs with requested changes and no activity for 30 days may be closed.
- Always explain why an item is being closed.
