from __future__ import annotations

import argparse
import json
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from epub2pdf_cli import __version__
from epub2pdf_cli.config import (
    BatchConfig,
    ConvertConfig,
    InspectConfig,
    PdfExtractConfig,
    PdfExtractFormat,
)
from epub2pdf_cli.errors import Epub2PdfError, ExitCode
from epub2pdf_cli.pdf import validate_pdf
from epub2pdf_cli.pdf.extract import EXTRACTORS
from epub2pdf_cli.pipeline import batch_convert, convert_epub, extract_pdf, inspect_epub
from epub2pdf_cli.render import ENGINES

PDF_EXTRACT_FORMATS: tuple[PdfExtractFormat, ...] = (
    "markdown",
    "json",
    "text",
    "html",
    "tables",
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
    convert_parser.add_argument("--engine", choices=("playwright", "weasyprint"), default="weasyprint", help="Rendering backend. Default: weasyprint.")
    convert_parser.add_argument("--sidecar-json", help="Write structured conversion output JSON to this path.")
    convert_parser.add_argument("--sidecar-html", help="Write the normalized merged HTML to this path.")
    convert_parser.add_argument("--sidecar-markdown", help="Write a Markdown version of the EPUB to this path.")
    convert_parser.add_argument("--page-size", choices=("A4", "Letter"), default="A4")
    convert_parser.add_argument("--margin-mm", type=int, default=12)
    convert_parser.add_argument("--cover", choices=("first", "none"), default="first")
    convert_parser.add_argument("--no-validate", action="store_true", help="Skip PDF validation after rendering.")
    convert_parser.add_argument("--force", action="store_true", help="Overwrite the output file if it already exists.")
    convert_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    batch_parser = subparsers.add_parser("batch", help="Convert multiple EPUBs in parallel.")
    batch_parser.add_argument("inputs", nargs="+", help="Paths to input .epub files.")
    batch_parser.add_argument("-o", "--output-dir", required=True, help="Directory for output PDFs.")
    batch_parser.add_argument("--engine", choices=("playwright", "weasyprint"), default="weasyprint", help="Rendering backend. Default: weasyprint.")
    batch_parser.add_argument("-j", "--workers", type=int, default=1, help="Number of parallel worker processes. Default: 1.")
    batch_parser.add_argument("--sidecar-json", action="store_true", help="Write a JSON report next to each PDF.")
    batch_parser.add_argument("--sidecar-html", action="store_true", help="Write merged HTML next to each PDF.")
    batch_parser.add_argument("--sidecar-markdown", action="store_true", help="Write Markdown next to each PDF.")
    batch_parser.add_argument("--page-size", choices=("A4", "Letter"), default="A4")
    batch_parser.add_argument("--margin-mm", type=int, default=12)
    batch_parser.add_argument("--cover", choices=("first", "none"), default="first")
    batch_parser.add_argument("--no-validate", action="store_true", help="Skip PDF validation after rendering.")
    batch_parser.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    batch_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    inspect_parser = subparsers.add_parser("inspect", help="Inspect EPUB metadata, manifest, spine, and TOC.")
    inspect_parser.add_argument("input", help="Path to the input .epub file.")
    inspect_parser.add_argument("--json", help="Write inspection output JSON to this path. Defaults to stdout.")
    inspect_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    pdf_parser = subparsers.add_parser("pdf-extract", help="Extract Markdown/JSON/HTML from a PDF.")
    pdf_parser.add_argument("input", help="Path to the input .pdf file.")
    pdf_parser.add_argument("-o", "--output-dir", help="Directory for extracted files. Defaults to <pdf-stem>_extracted.")
    pdf_parser.add_argument("--engine", choices=("pypdfium2", "docling", "pdfplumber", "opendataloader", "ocr"), default="pypdfium2", help="Extraction backend. Default: pypdfium2.")
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
    pdf_parser.add_argument("--threads", type=int, help="Worker thread count for native extraction.")
    pdf_parser.add_argument("--sidecar-json", help="Write structured extraction report JSON to this path.")
    pdf_parser.add_argument("--force", action="store_true", help="Overwrite existing extraction outputs.")
    pdf_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    validate_parser = subparsers.add_parser("validate", help="Validate a PDF file.")
    validate_parser.add_argument("input", help="Path to the input .pdf file.")
    validate_parser.add_argument("--no-expect-text", action="store_true", help="Do not require a searchable text layer.")
    validate_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    engines_parser = subparsers.add_parser("list-engines", help="List available render and extract engines.")
    engines_parser.add_argument("--verbose", action="store_true", help="Enable verbose logs.")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    _configure_logging(args.verbose)

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
                    sidecar_markdown_path=Path(args.sidecar_markdown) if args.sidecar_markdown else None,
                    page_size=args.page_size,
                    margin_mm=args.margin_mm,
                    cover=args.cover,
                    validate=not args.no_validate,
                    force=args.force,
                    verbose=args.verbose,
                )
            )
            print(str(output_path))
            logging.getLogger(__name__).debug("Conversion report: %s", json.dumps(report, ensure_ascii=False))
            return ExitCode.OK

        if args.command == "batch":
            report = batch_convert(
                BatchConfig(
                    input_paths=[Path(p) for p in args.inputs],
                    output_dir=Path(args.output_dir),
                    engine=args.engine,
                    workers=args.workers,
                    sidecar_json=args.sidecar_json,
                    sidecar_html=args.sidecar_html,
                    sidecar_markdown=args.sidecar_markdown,
                    page_size=args.page_size,
                    margin_mm=args.margin_mm,
                    cover=args.cover,
                    validate=not args.no_validate,
                    force=args.force,
                    verbose=args.verbose,
                )
            )
            for result in report["results"]:
                output_path = result.get("output", {}).get("path")
                if output_path:
                    print(output_path)
            logging.getLogger(__name__).debug("Batch report: %s", json.dumps(report, ensure_ascii=False))
            return ExitCode.OK if report["failures"] == 0 else ExitCode.UNEXPECTED

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
            return ExitCode.OK

        if args.command == "pdf-extract":
            input_path = Path(args.input)
            output_dir = Path(args.output_dir) if args.output_dir else input_path.with_name(f"{input_path.stem}_extracted")
            report = extract_pdf(
                PdfExtractConfig(
                    input_path=input_path,
                    output_dir=output_dir,
                    formats=_parse_pdf_formats(args.format),
                    engine=args.engine,
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
                    sidecar_json_path=Path(args.sidecar_json) if args.sidecar_json else None,
                    force=args.force,
                    verbose=args.verbose,
                )
            )
            for output in report["outputs"]:
                print(output)
            return ExitCode.OK

        if args.command == "validate":
            report = validate_pdf(Path(args.input), expect_text=not args.no_expect_text)
            json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
            return ExitCode.OK

        if args.command == "list-engines":
            from epub2pdf_cli.pdf.extract import _load_default_extractors

            _load_default_extractors()
            json.dump(
                {
                    "renderers": sorted(ENGINES.keys()),
                    "extractors": sorted(EXTRACTORS.keys()),
                },
                sys.stdout,
                ensure_ascii=False,
                indent=2,
            )
            sys.stdout.write("\n")
            return ExitCode.OK
    except Epub2PdfError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:
        logging.getLogger(__name__).exception("Unexpected error")
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return ExitCode.UNEXPECTED

    # Unreachable because subparsers are required, but kept for safety.
    parser.error(f"Unsupported command: {args.command}")
    return ExitCode.USAGE


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def _parse_pdf_formats(raw: str) -> list[PdfExtractFormat]:
    formats = [part.strip() for part in raw.split(",") if part.strip()]
    if not formats:
        raise Epub2PdfError("At least one --format value is required.", exit_code=ExitCode.USAGE)
    invalid = [fmt for fmt in formats if fmt not in PDF_EXTRACT_FORMATS]
    if invalid:
        allowed = ", ".join(PDF_EXTRACT_FORMATS)
        raise Epub2PdfError(f"Unsupported PDF extract format(s): {', '.join(invalid)}. Allowed: {allowed}", exit_code=ExitCode.USAGE)
    return formats  # type: ignore[return-value]
