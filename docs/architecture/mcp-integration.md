# MCP Integration

`epub2pdf` exposes a subset of its functionality as an MCP (Model Context Protocol) server. This lets compatible AI agents invoke conversion and extraction tools.

## Server entry point

```bash
python3 -m epub2pdf_cli.mcp_server
# or
epub2pdf-mcp
```

The server reads MCP requests from stdin and writes responses to stdout.

## Tools

| Tool | Purpose |
|---|---|
| `convert_epub` | Convert a single EPUB to PDF. |
| `batch_convert` | Convert multiple EPUBs in parallel. |
| `inspect_epub` | Return EPUB metadata, manifest, spine, and TOC. |
| `extract_pdf` | Extract Markdown, JSON, text, HTML, or tables from a PDF. |
| `validate_pdf` | Validate a PDF file (page count, text layer). |
| `list_engines` | List available render/extract engines on the host. |

Each tool validates arguments and returns a JSON sidecar report.

## Security model

- The MCP server runs with the same file-system permissions as the invoking process.
- It does not accept arbitrary HTML or remote URLs; only local file paths.
- It does not start a network listener.
- Each tool spawns the `epub2pdf` CLI in a subprocess and returns when it finishes; no long-lived browser or model process is kept open.
- `epub2pdf[mcp]` extra dependency is required.

## Error handling

Tool failures are returned as MCP `CallToolResult` content with `isError=True`. The sidecar `schema_version` is always included so callers can parse the response.
