:description: How to write third-party renderer and extractor plugins for epub2pdf.

# Plugin Ecosystem

`epub2pdf` supports third-party plugins through Python package entry points. This lets users install additional renderers and extractors without modifying the core code.

## Entry point groups

| Group | What it registers | Example |
|---|---|---|
| `epub2pdf.renderers` | `Renderer` implementations | `myplugin = myplugin.renderer:MyRenderer` |
| `epub2pdf.extractors` | `Extractor` implementations | `myplugin = myplugin.extractor:MyExtractor` |

## How it works

When `epub2pdf` starts, it loads all entry points in these groups and adds them to the internal registries (`render.ENGINES` and `pdf.extract.EXTRACTORS`). If a plugin fails to import, it is skipped.

## Plugin package example

`pyproject.toml`:

```toml
[project]
name = "my-epub2pdf-plugin"
version = "0.1.0"

[project.entry-points."epub2pdf.renderers"]
myrenderer = "my_plugin.renderer:MyRenderer"

[project.entry-points."epub2pdf.extractors"]
myextractor = "my_plugin.extractor:MyExtractor"
```

`my_plugin/renderer.py`:

```python
from epub2pdf_cli.render.protocol import Renderer
from epub2pdf_cli.render.options import RenderOptions

class MyRenderer(Renderer):
    name = "myrenderer"

    def render(self, html: str, options: RenderOptions) -> None:
        ...
```

`my_plugin/extractor.py`:

```python
from pathlib import Path
from collections.abc import Sequence
from typing import Any
from epub2pdf_cli.pdf.extractors.base import Extractor

class MyExtractor(Extractor):
    name = "myextractor"

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

## Backward compatibility

- New optional fields in `RenderOptions` or `PdfExtractConfig` must have defaults.
- Removing or renaming a plugin's `name` is a breaking change for users who reference it in CLI flags.
