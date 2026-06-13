# Extraction Contract

The extraction contract defines how `epub2pdf` pulls machine-readable content out of an existing PDF.

## Protocol

Every extractor must satisfy `epub2pdf_cli.pdf.extractors.base.Extractor`:

```python
class Extractor(Protocol):
    name: str

    def extract(
        self,
        input_path: Path,
        output_dir: Path,
        formats: Sequence[str],
        *,
        pages: str | None = None,
        password: str | None = None,
        options: dict[str, Any] | None = None,
        timings: dict[str, float] | None = None,
    ) -> list[str]:
        ...
```

- `name` is the stable identifier used in CLI `--engine` and reports.
- `extract` must create files in `output_dir` for every requested format.
- It must return the list of created file paths as strings.
- It must ignore unknown options silently (see options filtering below).

## Supported formats

| Format | Typical output file |
|---|---|
| `text` | `<stem>.txt` |
| `markdown` | `<stem>.md` |
| `html` | `<stem>.html` |
| `json` | `<stem>.json` |
| `markdown-with-html` | `<stem>.md` |
| `markdown-with-images` | `<stem>.md` (+ image assets) |
| `tagged-pdf` | `<stem>.pdf` |

## Options

`pdf/extract.py` builds an options dict from `PdfExtractConfig` and removes `None` values before passing them to the extractor. Extractors are free to ignore keys they do not support.

## Error handling

- Missing dependency → `StageError` with installation hint.
- Unsupported engine → `StageError` from `_select_extractor`.
- No output files created → `StageError` from `extract_pdf`.

## Backward compatibility

- New formats should be added to `PdfExtractFormat`.
- New optional extractor options must have defaults in `PdfExtractConfig`.
- Removing a format or extractor is a breaking change.
