# Security Policy

## Reporting a vulnerability

If you believe you have found a security issue in `epub2pdf`, please report it privately instead of opening a public issue or discussion.

- **GitHub Private Vulnerability Reporting**: Enable in repository settings (preferred).
- **Email fallback**: Open a GitHub Discussion and ask a maintainer for a private contact method. Do not include sensitive details in public channels.

We aim to respond within **5 business days**. If you do not receive a response, please follow up after 7 days.

## What belongs in a security report

A good report includes:

- Affected version or commit.
- Steps to reproduce, or a minimal file/command that triggers the issue.
- Expected vs. actual behavior.
- Impact assessment (data exposure, code execution, denial of service, etc.).
- Suggested fix, if you have one.

## Issues that should NOT be opened publicly

- Vulnerabilities in PDF or EPUB parsing that could lead to code execution or information disclosure.
- Bypasses of input sanitization, file path restrictions, or sandboxing.
- Leaked API keys, tokens, or credentials anywhere in the repository or release artifacts.
- Dependency vulnerabilities that affect users of `epub2pdf`.

## Scope

The security policy covers:

- The `epub2pdf` CLI, Python API, MCP server, and agent skill wrappers.
- Official Docker images published to `ghcr.io/min9lin9/epub2pdf`.
- PyPI release artifacts for `epub2pdf`.
- GitHub Actions workflows in this repository.

Out of scope:

- Security issues in third-party rendering engines unless they directly affect how `epub2pdf` invokes them.
- Personal misuse of converted PDFs or EPUBs.

## Disclosure policy

- We will investigate and patch confirmed vulnerabilities in a coordinated manner.
- Fixes are released as soon as practical, with a clear changelog entry.
- Reporters will be credited unless they request anonymity.
- We follow responsible disclosure and ask reporters to wait at least **90 days** before publicly disclosing details, unless both parties agree otherwise.

## Security hardening notes

- `epub2pdf` is intentionally a local CLI. It does not expose a network interface by default.
- `pdf-extract` opens user-provided files locally. Treat untrusted files with the same caution as any document-processing tool.
- The optional Playwright/Chromium backend downloads a browser binary. Keep it updated and run it in isolated environments when handling untrusted EPUBs.
- The optional Docling backend may pull additional ML models. Review Docling's security documentation before enabling it in sensitive environments.
