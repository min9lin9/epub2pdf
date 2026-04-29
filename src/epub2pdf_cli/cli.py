from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Sequence

from epub2pdf_cli import __version__
from epub2pdf_cli.config import ConvertConfig, InspectConfig, PdfExtractConfig
from epub2pdf_cli.errors import Epub2PdfError
from epub2pdf_cli.service import convert_epub, extract_pdf, inspect_epub

PDF_EXTRACT_FORMATS = (
    "markdown",
    "json",
    "text",
    "html",
    "markdown-with-html",
    "markdown-with-images",
    "tagged-pdf",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="epub2pdf", description="Convert EPUB files into machine-readable PDFs.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    convert_parser = subparsers.add_parser("convert", help="Render an EPUB into PDF.")
    convert_parser.add_argument("input", help="Path to the input .epub file.")
    convert_parser.add_argument("-o", "--output", help="Path to the output PDF. Defaults to the input basename with .pdf.")
    convert_parser.add_argument("--engine", choices=("playwright", "weasyprint"), default="playwright")
    convert_parser.add_argument("--sidecar-json", help="Write structured conversion output JSON to this path.")
    convert_parser.add_argument("--sidecar-html", help="Write the normalized merged HTML to this path.")
    convert_parser.add_argument("--page-size", choices=("A4", "Letter"), default="A4")
    convert_parser.add_argument("--margin-mm", type=int, default=12)
    convert_parser.add_argument("--cover", choices=("first", "none"), default="first")
    convert_parser.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    convert_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect EPUB metadata, manifest, spine, and TOC.")
    inspect_parser.add_argument("input", help="Path to the input .epub file.")
    inspect_parser.add_argument("--json", help="Write inspection output JSON to this path. Defaults to stdout.")
    inspect_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    pdf_parser = subparsers.add_parser("pdf-extract", help="Extract Markdown/JSON/HTML from a PDF with opendataloader-pdf.")
    pdf_parser.add_argument("input", help="Path to the input .pdf file.")
    pdf_parser.add_argument("-o", "--output-dir", help="Directory for extracted files. Defaults to <pdf-stem>_extracted.")
    pdf_parser.add_argument(
        "--format",
        default="markdown,json",
        help="Comma-separated output formats. Default: markdown,json.",
    )
    pdf_parser.add_argument("--pages", help='Pages to extract, for example "1,3,5-7".')
    pdf_parser.add_argument("--password", help="Password for encrypted PDF files.")
    pdf_parser.add_argument("--use-struct-tree", action="store_true", help="Use tagged PDF structure tree when available.")
    pdf_parser.add_argument("--sanitize", action="store_true", help="Sanitize emails, phone numbers, IPs, cards, and URLs.")
    pdf_parser.add_argument("--keep-line-breaks", action="store_true", help="Preserve original text line breaks.")
    pdf_parser.add_argument("--include-header-footer", action="store_true", help="Include page headers and footers.")
    pdf_parser.add_argument("--detect-strikethrough", action="store_true", help="Detect strikethrough text in Markdown/HTML.")
    pdf_parser.add_argument("--table-method", choices=("default", "cluster"), help="Table detection method.")
    pdf_parser.add_argument("--reading-order", choices=("off", "xycut"), default="xycut", help="Reading order algorithm.")
    pdf_parser.add_argument("--markdown-page-separator", help="Separator between Markdown pages; supports %%page-number%%.")
    pdf_parser.add_argument("--html-page-separator", help="Separator between HTML pages; supports %%page-number%%.")
    pdf_parser.add_argument("--image-output", choices=("off", "embedded", "external"), default="external")
    pdf_parser.add_argument("--image-dir", help="Directory for extracted images.")
    pdf_parser.add_argument("--threads", help="Worker thread count for native extraction.")
    pdf_parser.add_argument("--force", action="store_true", help="Overwrite existing extraction outputs.")
    pdf_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    _configure_logging(getattr(args, "verbose", False))

    try:
        if args.command == "convert":
            input_path = Path(args.input)
            output_path = Path(args.output) if args.output else input_path.with_suffix(".pdf")
            report = convert_epub(
                ConvertConfig(
                    input_path=input_path,
                    output_path=output_path,
                    engine=args.engine,
                    sidecar_json_path=Path(args.sidecar_json) if args.sidecar_json else None,
                    sidecar_html_path=Path(args.sidecar_html) if args.sidecar_html else None,
                    page_size=args.page_size,
                    margin_mm=args.margin_mm,
                    cover=args.cover,
                    force=args.force,
                    verbose=args.verbose,
                )
            )
            print(str(output_path))
            logging.getLogger(__name__).debug("Conversion report: %s", json.dumps(report, ensure_ascii=False))
            return 0

        if args.command == "inspect":
            report = inspect_epub(
                InspectConfig(
                    input_path=Path(args.input),
                    json_path=Path(args.json) if args.json else None,
                )
            )
            if not args.json:
                json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
                sys.stdout.write("\n")
            return 0

        if args.command == "pdf-extract":
            input_path = Path(args.input)
            output_dir = Path(args.output_dir) if args.output_dir else input_path.with_name(f"{input_path.stem}_extracted")
            report = extract_pdf(
                PdfExtractConfig(
                    input_path=input_path,
                    output_dir=output_dir,
                    formats=_parse_pdf_formats(args.format),
                    pages=args.pages,
                    password=args.password,
                    use_struct_tree=args.use_struct_tree,
                    sanitize=args.sanitize,
                    keep_line_breaks=args.keep_line_breaks,
                    include_header_footer=args.include_header_footer,
                    detect_strikethrough=args.detect_strikethrough,
                    table_method=args.table_method,
                    reading_order=args.reading_order,
                    markdown_page_separator=args.markdown_page_separator,
                    html_page_separator=args.html_page_separator,
                    image_output=args.image_output,
                    image_dir=Path(args.image_dir) if args.image_dir else None,
                    threads=args.threads,
                    force=args.force,
                    verbose=args.verbose,
                )
            )
            for output in report["outputs"]:
                print(output)
            return 0
    except Epub2PdfError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code

    parser.error(f"Unsupported command: {args.command}")
    return 2


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def _parse_pdf_formats(raw: str) -> list[str]:
    formats = [part.strip() for part in raw.split(",") if part.strip()]
    if not formats:
        raise Epub2PdfError("At least one --format value is required.", exit_code=2)
    invalid = [fmt for fmt in formats if fmt not in PDF_EXTRACT_FORMATS]
    if invalid:
        allowed = ", ".join(PDF_EXTRACT_FORMATS)
        raise Epub2PdfError(f"Unsupported PDF extract format(s): {', '.join(invalid)}. Allowed: {allowed}", exit_code=2)
    return formats
