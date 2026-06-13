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

The current tool set is intentionally narrow:

- `convert_epub_to_pdf(input_path, output_path, ...)`
- `extract_pdf(input_path, output_dir, ...)`

Each tool validates arguments and returns a JSON sidecar report.

## Security model

- The MCP server runs with the same file-system permissions as the invoking process.
- It does not accept arbitrary HTML or remote URLs; only local file paths.
- It does not start a network listener.
- `epub2pdf[mcp]` extra dependency is required.

## Error handling

Tool failures are returned as MCP `CallToolResult` content with `isError=True`. The sidecar `schema_version` is always included so callers can parse the response.
