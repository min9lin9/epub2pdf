# Renderer Contract

The renderer contract defines how `epub2pdf` turns normalized HTML into a PDF file.

## Protocol

Every renderer must satisfy `epub2pdf_cli.render.protocol.Renderer`:

```python
class Renderer(Protocol):
    name: str

    def render(self, html: str, options: RenderOptions) -> None:
        ...
```

- `name` is a stable identifier used in CLI flags and reports.
- `render` receives a single merged HTML string and `RenderOptions`.
- `render` must write the PDF to `options.output_path`.
- On failure, raise `StageError` with a clear message.

## RenderOptions

```python
@dataclass(frozen=True)
class RenderOptions:
    output_path: Path
    page_size: Literal["A4", "Letter"]
    margin_mm: int
    cover: Literal["first", "none"]
    title: str = ""
```

- `output_path` is an absolute or resolved path. Parent directories already exist.
- `margin_mm` is non-negative. The renderer must reject negative values.
- `page_size` must be respected unless CSS `@page` rules override it.

## Engine registry

`epub2pdf_cli.render.ENGINES` maps `name -> type[Renderer]`.
Optional engines are registered lazily; if their dependencies are missing, they are omitted from `ENGINES`.

## Error handling

- Missing dependency → `StageError` with installation hint.
- Rendering failure → `StageError` with engine name.
- Timeouts (Playwright) → `StageError` with timeout duration.

## Backward compatibility

- New fields added to `RenderOptions` must have defaults.
- Existing renderers must continue to work without modification.
- Removing or renaming an engine is a breaking change.
