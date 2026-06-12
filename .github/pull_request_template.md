## Summary

Briefly describe the change and why it was made.

## Related Issue

Fixes #(issue number) or relates to #(issue number).

## Change Type

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring
- [ ] Test improvement
- [ ] Dependency update
- [ ] Breaking change

## Test Results

Commands run:

```bash
PYTHONPATH=src python3 -m pytest -q --cov=epub2pdf_cli --cov-fail-under=60
python3 -m ruff check src tests
python3 -m mypy src
```

Paste the output or attach a screenshot.

## Contract / Behavior Check

- [ ] CLI output format unchanged unless intended.
- [ ] Sidecar schema unchanged unless version bumped.
- [ ] PDF text-layer guarantee preserved for textual EPUBs.
- [ ] No new required dependencies for the base install.

## Documentation

- [ ] README updated (if user-facing).
- [ ] `docs/` updated (if architecture changed).
- [ ] CHANGELOG.md updated under the unreleased section.

## AI Usage

- [ ] No AI assistance was used for this PR.
- [ ] AI assistance was used. I personally reviewed and tested every changed line and can explain the design decisions.

If AI was used, list the tool(s) and the scope of AI-generated changes:

## Risk Scope

- [ ] Low: isolated bug fix or docs update.
- [ ] Medium: new optional feature or refactor with existing tests.
- [ ] High: breaking change, new backend, security-sensitive code, or large refactor.

## Checklist

- [ ] Tests added or updated.
- [ ] CI passes (format, lint, type check, tests, coverage gate).
- [ ] No new warnings introduced.
- [ ] Breaking changes are clearly marked in CHANGELOG.md.
