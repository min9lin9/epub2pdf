#!/usr/bin/env python3
"""Benchmark epub2pdf with real Project Gutenberg EPUBs and memory profiling."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import warnings
from pathlib import Path
from typing import Any, cast

# Suppress BeautifulSoup XML parsing warnings in benchmark output.
warnings.filterwarnings("ignore")
try:
    from bs4.builder import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except Exception:
    pass

from epub2pdf_cli.api import Epub2Pdf

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path.home() / ".cache" / "epub2pdf_benchmark"
ENV = {**os.environ, "PYTHONPATH": str(PROJECT_ROOT / "src")}

BOOKS: list[tuple[str, int]] = [
    ("Alice in Wonderland", 11),
    ("Pride and Prejudice", 1342),
    ("Moby Dick", 2701),
]


def download_book(title: str, book_id: int) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"pg{book_id}.epub"
    if path.exists():
        return path
    url = f"https://www.gutenberg.org/ebooks/{book_id}.epub.noimages"
    print(f"Downloading {title}...")
    urllib.request.urlretrieve(url, path)
    return path


def _worker_script() -> str:
    return """
import json, os, resource, sys, tempfile, time, warnings
sys.path.insert(0, os.environ.get("PYTHONPATH", ""))
warnings.filterwarnings("ignore")
try:
    from bs4.builder import XMLParsedAsHTMLWarning
    warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
except Exception:
    pass

from pathlib import Path
from epub2pdf_cli.api import Epub2Pdf

input_path = Path(sys.argv[1])
output_path = Path(sys.argv[2])
engine = sys.argv[3]

# macOS reports ru_maxrss in bytes, Linux in kilobytes
scale = 1024 * 1024 if sys.platform == "darwin" else 1024

client = Epub2Pdf(engine=engine, validate=False)
mem_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
start = time.perf_counter()
report = client.convert(input_path, output_path)
elapsed = time.perf_counter() - start
mem_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

print(json.dumps({
    "wall_time": elapsed,
    "render_time": report["output"]["timings"].get("render", 0.0),
    "peak_memory_mb": max(0.0, (mem_after - mem_before) / scale),
}))
"""


def run_isolated(epub_path: Path, output_path: Path, engine: str) -> dict[str, Any]:
    """Run one conversion in a fresh process to measure accurate peak memory."""
    result = subprocess.run(
        [sys.executable, "-c", _worker_script(), str(epub_path), str(output_path), engine],
        env=ENV,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Isolated {engine} conversion failed: {result.stderr}")
    return cast(dict[str, Any], json.loads(result.stdout))


def run_pooled(epub_path: Path, output_path: Path, engine: str, browser: Any | None) -> dict[str, Any]:
    """Run conversion in the current process, optionally reusing a Playwright browser."""
    client = Epub2Pdf(engine=engine, validate=False)
    if browser is not None:
        client._browser = browser
    start = time.perf_counter()
    report = client.convert(epub_path, output_path)
    elapsed = time.perf_counter() - start
    return {
        "wall_time": elapsed,
        "render_time": report["output"]["timings"].get("render", 0.0),
    }


def run_batch(epub_paths: list[Path], output_dir: Path, engine: str, workers: int) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(path, output_dir / f"{path.stem}.pdf") for path in epub_paths]
    start = time.perf_counter()
    client = Epub2Pdf(engine=engine, validate=False)
    reports = client.batch_convert(jobs, max_workers=workers)
    elapsed = time.perf_counter() - start
    successes = sum(1 for r in reports if "error" not in r)
    return {
        "engine": engine,
        "workers": workers,
        "wall_time": elapsed,
        "successes": successes,
    }


def _format_time(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.0f} ms"
    return f"{seconds:.2f} s"


def _format_mem(mb: float) -> str:
    return f"{mb:.1f} MB"


def main() -> int:
    print("Real-world benchmark cache:", CACHE_DIR)
    epub_paths: list[Path] = []
    for title, book_id in BOOKS:
        path = download_book(title, book_id)
        size_kb = path.stat().st_size / 1024
        print(f"  {title}: {path} ({size_kb:.0f} KB)")
        epub_paths.append(path)

    workdir = Path(tempfile.mkdtemp())
    print("Work directory:", workdir)

    rows: list[dict[str, Any]] = []

    print("\nRunning isolated conversions (memory measured)...")
    for title, _ in BOOKS:
        epub_path = epub_paths[BOOKS.index((title, _))]
        for engine in ("weasyprint", "playwright"):
            output_path = workdir / f"{epub_path.stem}_{engine}_isolated.pdf"
            result = run_isolated(epub_path, output_path, engine)
            rows.append({
                "book": title,
                "engine": engine,
                "mode": "isolated",
                "wall_time": result["wall_time"],
                "render_time": result["render_time"],
                "memory_mb": result["peak_memory_mb"],
            })

    print("Running pooled API conversions (speed measured)...")
    with Epub2Pdf(engine="playwright") as playwright_client:
        browser = playwright_client._browser
        for title, _ in BOOKS:
            epub_path = epub_paths[BOOKS.index((title, _))]
            for engine in ("weasyprint", "playwright"):
                output_path = workdir / f"{epub_path.stem}_{engine}_pooled.pdf"
                result = run_pooled(epub_path, output_path, engine, browser if engine == "playwright" else None)
                rows.append({
                    "book": title,
                    "engine": engine,
                    "mode": "pooled",
                    "wall_time": result["wall_time"],
                    "render_time": result["render_time"],
                    "memory_mb": None,
                })

    print("Running batch conversions...")
    batch_rows: list[dict[str, Any]] = []
    for engine in ("weasyprint", "playwright"):
        for workers in (2, 4):
            batch_rows.append({
                "engine": engine,
                "workers": workers,
                **run_batch(epub_paths, workdir / f"batch_{engine}_{workers}", engine, workers),
            })

    print("\n" + "=" * 100)
    print(f"{'Book':<30} {'Engine':<12} {'Mode':<10} {'Wall Time':<12} {'Render':<12} {'Memory':<12}")
    print("=" * 100)
    for row in rows:
        memory = _format_mem(row["memory_mb"]) if row["memory_mb"] is not None else "-"
        print(
            f"{row['book']:<30} {row['engine']:<12} {row['mode']:<10}"
            f" {_format_time(row['wall_time']):<12} {_format_time(row['render_time']):<12} {memory:<12}"
        )

    print("\n" + "-" * 80)
    print(f"{'Engine':<12} {'Workers':<8} {'Wall Time':<12} {'Success':<8}")
    print("-" * 80)
    for row in batch_rows:
        print(
            f"{row['engine']:<12} {row['workers']:<8}"
            f" {_format_time(row['wall_time']):<12} {row['successes']}/{len(epub_paths)}"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
