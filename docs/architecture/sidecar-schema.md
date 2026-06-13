# Sidecar Schema

All pipeline commands emit a JSON report with a `schema_version` field. The current schema version is `1.0`, defined in `src/epub2pdf_cli/config.py`.

## Versioning rules

- The major version changes when a required top-level field is removed or renamed.
- The minor version changes when new optional fields are added.
- Consumers must ignore unknown fields.
- Consumers must not assume presence of optional fields added in newer minor versions.

## `convert` report

```json
{
  "schema_version": "1.0",
  "source": {"path": "...", "sha256": "..."},
  "output": {"path": "...", "engine": "weasyprint", "validation": {...}, "timings": {...}},
  "html": {"chapters": [...], "assets": [...], "warnings": [...]},
  "converted_at": "2026-06-13T00:00:00+00:00"
}
```

## `batch` report

```json
{
  "schema_version": "1.0",
  "engine": "weasyprint",
  "workers": 1,
  "output_dir": "...",
  "total_time": 1.234,
  "successes": 2,
  "failures": 0,
  "results": [...],
  "completed_at": "2026-06-13T00:00:00+00:00"
}
```

Each item in `results` is either a `convert` report or an error object:

```json
{
  "schema_version": "1.0",
  "source": {"path": "..."},
  "output": {"path": "...", "error": "..."},
  "error": "...",
  "exit_code": 1
}
```

## `inspect` report

```json
{
  "schema_version": "1.0",
  "source": {"path": "...", "rootfile": "..."},
  "metadata": {...},
  "manifest": [...],
  "spine": [...],
  "toc": [...],
  "chapters": [...],
  "warnings": []
}
```

## `pdf-extract` report

```json
{
  "schema_version": "1.0",
  "source": {"path": "...", "sha256": "...", "extracted_at": "..."},
  "formats": ["markdown", "json"],
  "output_dir": "...",
  "outputs": ["..."],
  "engine": "pypdfium2",
  "mode": "local",
  "timings": {...}
}
```
