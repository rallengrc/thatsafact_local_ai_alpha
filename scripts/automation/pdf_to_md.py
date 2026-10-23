#!/usr/bin/env python3
"""
pdf_to_md.py — Convert a PDF to Markdown, extracting BOTH text AND images.
Careful, repeatable (idempotent), and display-correct.

WHAT THIS DOES
  * Text:  page-by-page extraction in reading order; each page is fenced under a
           "## Page N" heading so the document's structure is preserved.
  * Images (embedded rasters):
       - Sourced from get_image_info(xrefs=True) — the images ACTUALLY drawn on a
         page, each with its on-page bbox. (get_images(full=True) instead lists the
         page's shared resource pool: the same ~30 images "appear" on every page,
         which is NOT what is drawn and breaks per-page/frequency logic.)
       - DEDUPLICATED by content hash: a logo drawn on 188 pages becomes ONE file
         on disk, not 188.
       - PLACED at their real on-page position (the bbox), interleaved with the
         text in reading order.
       - FREQUENCY-AWARE: an image drawn on more than `--running-fraction`
         (default 50%) of pages is treated as a running logo/footer — it is kept
         in the asset inventory but NOT spammed into every page's body.
       - Referenced with URL-ENCODED, space-free paths so they render in GitHub,
         VS Code, and other Markdown viewers.
  * Page renders: --mode pages (render every page to a PNG — the reliable way to
           show *vector* diagrams that have zero embedded rasters, e.g. the earlier
           "Ray and Flyte" doc) or --render-empty (render only pages with no
           embedded raster).
  * Repeatable / idempotent: the output .md and its .assets folder are cleaned
           and regenerated on every run, so running the script twice yields the
           same files.
  * Read-only on the source PDF: only the output location is written.
  * Self-checks: after writing, every image link is verified to resolve to a real
           file; the run fails (exit 4) if any are broken.

WHY THE EARLIER VERSION FAILED TO DISPLAY IMAGES
  Its folder name contained spaces ("Ray and Flyte - ... .md.assets") and its
  links were not URL-encoded. Markdown renderers do not resolve raw spaces in
  image paths, so the images were broken. Fixed here by (1) slugifying the folder
  name and (2) URL-encoding every link.

DEPENDENCY
  PyMuPDF (`import pymupdf`; the old `fitz` is deprecated). On this machine it
  lives in a project venv (Homebrew blocks system pip via PEP 668):
      python3 -m venv .venv && ./.venv/bin/pip install pymupdf
  Run with that interpreter:
      ./.venv/bin/python scripts/pdf_to_md.py [input.pdf] [output.md] [options]
  If pymupdf/fitz is unavailable, the script prints the setup command and exits
  cleanly.

USAGE
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf                 # in-place, auto
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf out.md
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf --mode pages    # vector-only doc
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf --render-empty  # auto + fill gaps
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf --dpi 200
  ./.venv/bin/python scripts/pdf_to_md.py in.pdf --running-fraction 0.6

MODES
  auto (default)  text + embedded-raster gallery (frequency-aware, placed where
                  possible, deduped).
  extract         alias for auto.
  pages           render every page to a PNG (best for vector-diagram PDFs).
  both            embedded-raster gallery AND a PNG per page.
"""

import argparse
import hashlib
import os
import re
import shutil
import sys
import time
from urllib.parse import quote, unquote

# --- Dependency gate -------------------------------------------------------
fitz = None
try:
    import pymupdf as fitz  # PyMuPDF (current import name)
except Exception:
    try:
        import fitz  # type: ignore  # older PyMuPDF alias
    except Exception:
        sys.stderr.write(
            "This script needs PyMuPDF (`import pymupdf` / `import fitz`), "
            "which is not importable here.\n"
            "Set up the project venv and run through it:\n\n"
            "    python3 -m venv .venv\n"
            "    ./.venv/bin/pip install pymupdf\n"
            "    ./.venv/bin/python %s\n"
            % os.path.basename(sys.argv[0])
        )
        sys.exit(3)

DEFAULT_PDF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "memories",
    "Ray and Flyte - Orchestration and Distributed Compute.pdf",
)

LINK_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")


# --- Helpers ---------------------------------------------------------------
def _source_label(pdf_path: str) -> str:
    """Repo-relative POSIX path for the Source line (never an absolute home path)."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    try:
        rel = os.path.relpath(pdf_path, repo_root)
    except ValueError:  # different drive on Windows
        return os.path.basename(pdf_path)
    return os.path.basename(pdf_path) if rel.startswith("..") else rel.replace(os.sep, "/")


def slugify(name: str) -> str:
    """Filesystem/markdown-safe folder name: lowercase, non-alnum -> hyphen."""
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s or "images"


def _guess_ext(data: bytes, hint: str | None) -> str:
    if hint and hint.lower() not in ("", "png"):
        return hint.lower()
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    if data[:4] == b"GIF8":
        return "gif"
    if data[6:10] == b"BM":
        return "bmp"
    return "png"


def _clean_line(s: str) -> str:
    return re.sub(r"[ \t]+", " ", s).strip()


def _text_block_to_md(block: dict) -> str:
    """Render a text block (get_text('dict') form) to markdown text."""
    lines: list[str] = []
    for line in block.get("lines", []):
        spans = line.get("spans", [])
        text = "".join(sp.get("text", "") for sp in spans)
        cleaned = _clean_line(text)
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def _row(y: float) -> int:
    """Bucket a y coordinate so horizontally-adjacent items keep L->R order."""
    return int(round(y / 3.0))


def _link(rel_path: str) -> str:
    """URL-encode a relative image path so it renders in any Markdown viewer."""
    return quote(rel_path, safe="/")


def _load_xref(doc, xref: int) -> dict:
    """Return image info for an xref: {hash, ext, w, h, data} or {'empty':True}."""
    try:
        e = doc.extract_image(xref)
        data = e.get("image") or b""
        if not data:
            return {"empty": True}
        return {
            "hash": hashlib.sha1(data).hexdigest(),
            "ext": _guess_ext(data, e.get("ext")),
            "w": e.get("width", 0),
            "h": e.get("height", 0),
            "data": data,
        }
    except Exception:
        return {"empty": True}


# --- Core ------------------------------------------------------------------
def convert(pdf_path: str, out_md: str, dpi: int = 150, mode: str = "auto",
            min_dim: int = 8, running_fraction: float = 0.5, clean: bool = True,
            render_empty: bool = False) -> dict:
    """Convert `pdf_path` to Markdown at `out_md`. See module docstring for modes."""
    pdf_path = os.path.abspath(pdf_path)
    out_md = os.path.abspath(out_md)
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    stem = os.path.splitext(os.path.basename(out_md))[0]
    slug = slugify(stem)
    out_md_dir = os.path.dirname(out_md) or "."
    assets_dir = os.path.join(out_md_dir, f"{slug}.assets")
    rel_prefix = f"{slug}.assets"  # relative to the .md file

    os.makedirs(out_md_dir, exist_ok=True)
    if clean:
        # remove this stem's previous output and any stale assets folders for it
        for stale in (out_md, assets_dir):
            if os.path.isfile(stale):
                os.remove(stale)
            elif os.path.isdir(stale):
                shutil.rmtree(stale)
        for entry in os.listdir(out_md_dir):
            if entry.startswith(slug + ".assets"):  # e.g. old "slug.assets.bak"
                p = os.path.join(out_md_dir, entry)
                if os.path.isdir(p):
                    shutil.rmtree(p)
    os.makedirs(assets_dir, exist_ok=True)

    do_gallery = mode in ("auto", "extract", "both")
    render_every = mode in ("pages", "both")
    version_raw = getattr(fitz, "version", getattr(fitz, "__version__", "n/a"))
    version = version_raw[0] if isinstance(version_raw, (tuple, list)) else str(version_raw)

    doc = fitz.open(pdf_path)  # read-only open of the source
    total_pages = doc.page_count
    threshold = max(1, int(round(running_fraction * total_pages)))

    stats = {
        "pdf": pdf_path, "out_md": out_md, "assets_dir": assets_dir,
        "pages": total_pages, "raster_refs": 0, "unique_images": 0,
        "running_images": 0, "rendered": 0, "dropped_tiny": 0, "text_chars": 0,
        "broken_links": 0,
    }

    # ---- PASS 1: inventory every page's ACTUALLY-DRAWN images ----
    # get_image_info(xrefs=True) reports the images really rendered on the page
    # (with their on-page bbox). get_images(full=True) instead lists the page's
    # SHARED resource pool (the same ~30 images "appear" on every page), which is
    # NOT what is drawn and would break any per-page / frequency logic.
    xref_cache: dict[int, dict] = {}     # xref -> info
    hash_info: dict[str, dict] = {}      # content hash -> info
    page_drawn: list[list[tuple[str, float, float]]] = []  # (hash, x0, y0)
    for pno in range(total_pages):
        page = doc[pno]
        drawn: list[tuple[str, float, float]] = []
        seen_on_page: set[int] = set()
        for it in page.get_image_info(xrefs=True):
            xref = it.get("xref")
            if not xref or xref in seen_on_page:
                continue
            seen_on_page.add(xref)
            info = xref_cache.get(xref)
            if info is None:
                info = _load_xref(doc, xref)
                xref_cache[xref] = info
            if info.get("empty"):
                continue
            if min(info["w"], info["h"]) < min_dim:
                stats["dropped_tiny"] += 1
                continue
            bbox = it.get("bbox") or (0, 0, 0, 0)
            h = info["hash"]
            hash_info.setdefault(h, info)
            drawn.append((h, float(bbox[0]), float(bbox[1])))
            stats["raster_refs"] += 1
        page_drawn.append(drawn)

    freq = {h: 0 for h in hash_info}
    for drawn in page_drawn:
        for (h, _, _) in drawn:
            freq[h] += 1

    def is_running(h: str) -> bool:
        return freq.get(h, 0) > threshold

    # save each unique image once
    saved: dict[str, str] = {}
    unique_records: dict[str, dict] = {}
    for h, info in hash_info.items():
        fname = f"{h[:16]}.{info['ext']}"
        with open(os.path.join(assets_dir, fname), "wb") as out:
            out.write(info["data"])
        saved[h] = fname
        unique_records[h] = {
            "file": fname, "w": info["w"], "h": info["h"],
            "pages": sorted(p + 1 for p in range(total_pages)
                            if any(dh == h for (dh, _, _) in page_drawn[p])),
            "running": is_running(h),
        }

    def figure_md(h: str, pno: int) -> str:
        return f"![Page {pno + 1} figure]({_link(f'{rel_prefix}/{saved[h]}')})"

    # ---- PASS 2: write the Markdown ----------------------------------------
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# {stem}\n\n")
        f.write(f"> **Source:** `{_source_label(pdf_path)}`\n")
        f.write(f"> **Generated:** {time.strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"> **Converter:** `scripts/pdf_to_md.py` "
                f"(PyMuPDF {version}, mode={mode}, dpi={dpi}, "
                f"min-dim={min_dim}, running-fraction={running_fraction})\n\n")
        f.write("---\n\n")

        for pno in range(total_pages):
            page = doc[pno]
            f.write(f"## Page {pno + 1}\n\n")

            items: list[tuple[int, int, str]] = []  # (row, x0, fragment)

            # text (type-0 blocks only)
            if do_gallery or render_every:
                for b in page.get_text("dict").get("blocks", []):
                    if b.get("type") == 0:
                        t = _text_block_to_md(b)
                        if t:
                            stats["text_chars"] += len(t)
                            items.append((_row(b["bbox"][1]), b["bbox"][0], t))

            # place actually-drawn images at their on-page position; skip running
            # logos/footers (still saved + listed in the manifest)
            if do_gallery:
                for (h, x0, y0) in page_drawn[pno]:
                    if is_running(h):
                        continue
                    items.append((_row(y0), x0, figure_md(h, pno)))

            items.sort(key=lambda it: (it[0], it[1]))
            body = "\n\n".join(it[2] for it in items) or "_[no text on this page]_"
            f.write(body + "\n\n")

            # optional page render
            if render_every or (render_empty and not page_drawn[pno]):
                pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0),
                                      alpha=False)
                name = f"p{pno + 1}.png"
                pix.save(os.path.join(assets_dir, name))
                f.write(f"![Page {pno + 1} (rendered)]"
                        f"({_link(f'{rel_prefix}/{name}')})\n\n")
                stats["rendered"] += 1

        # manifest
        f.write("\n---\n\n## Extracted images\n\n")
        running = sum(1 for r in unique_records.values() if r["running"])
        f.write(f"{stats['raster_refs']} actually-drawn image placement(s) -> "
                f"{len(unique_records)} unique image(s) in `{rel_prefix}/` "
                f"({running} treated as running logo/footer; "
                f"{stats['dropped_tiny']} tiny image(s) dropped; "
                f"{stats['rendered']} page render(s)).\n\n")
        if unique_records or stats["rendered"]:
            f.write("```text\n")
            for r in sorted(unique_records.values(), key=lambda r: r["file"]):
                flag = "  [running]" if r["running"] else ""
                pages = ", ".join(map(str, r["pages"][:10]))
                if len(r["pages"]) > 10:
                    pages += f" ... (+{len(r['pages']) - 10})"
                f.write(f"{r['file']:<22} {r['w']}x{r['h']:<8} "
                        f"pages: {pages}{flag}\n")
            for i in range(1, total_pages + 1):
                if os.path.isfile(os.path.join(assets_dir, f"p{i}.png")):
                    f.write(f"p{i}.png (page render)\n")
            f.write("```\n")
        else:
            f.write("_No images were produced._\n")

    doc.close()
    stats["unique_images"] = len(unique_records)
    stats["running_images"] = running
    stats["broken_links"] = _verify_links(out_md, out_md_dir)
    return stats


def _verify_links(out_md: str, out_md_dir: str) -> int:
    """Count image links in the written .md that do NOT resolve to a real file."""
    broken = 0
    with open(out_md, encoding="utf-8") as f:
        text = f.read()
    for m in LINK_RE.finditer(text):
        target = m.group(1).split()[0]
        target = target.lstrip("<").rstrip(">").strip()
        if not target:
            continue
        path = os.path.join(out_md_dir, unquote(target))
        if not os.path.isfile(path):
            broken += 1
    return broken


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Convert a PDF to Markdown with text + deduped, placed, "
                    "URL-encoded images (repeatable, idempotent, self-checking)."
    )
    ap.add_argument("input", nargs="?", default=DEFAULT_PDF,
                    help="Input PDF path (default: the Ray and Flyte PDF).")
    ap.add_argument("output", nargs="?", default=None,
                    help="Output .md path (default: same name as input, .md).")
    ap.add_argument("--mode", choices=["auto", "extract", "pages", "both"],
                    default="auto",
                    help="auto/extract: embedded-raster gallery; pages: render every "
                         "page; both: gallery + page renders.")
    ap.add_argument("--dpi", type=int, default=150,
                    help="Render resolution for page PNGs (default 150).")
    ap.add_argument("--min-dim", type=int, default=8,
                    help="Drop embedded images smaller than N px on a side "
                         "(default 8).")
    ap.add_argument("--running-fraction", type=float, default=0.5,
                    help="Treat an image as a running logo/footer (kept in the "
                         "manifest, not spammed inline) if it appears on more than "
                         "this fraction of pages (default 0.5).")
    ap.add_argument("--render-empty", action="store_true",
                    help="Also render pages that contain no embedded raster "
                         "(for vector-only docs).")
    ap.add_argument("--keep-old", action="store_true",
                    help="Do NOT clean previous output before writing.")
    args = ap.parse_args()

    input_pdf = args.input or DEFAULT_PDF
    out_md = args.output or (os.path.splitext(input_pdf)[0] + ".md")

    try:
        stats = convert(
            input_pdf, out_md, dpi=args.dpi, mode=args.mode,
            min_dim=args.min_dim, running_fraction=args.running_fraction,
            clean=not args.keep_old, render_empty=args.render_empty,
        )
    except FileNotFoundError as e:
        sys.stderr.write(f"error: {e}\n")
        return 1
    except Exception as e:  # noqa: BLE001
        sys.stderr.write(f"error: conversion failed: {e}\n")
        return 2

    print("PDF -> Markdown conversion complete")
    print(f"  input          : {stats['pdf']}")
    print(f"  output md      : {stats['out_md']}")
    print(f"  pages          : {stats['pages']}   "
          f"raster refs: {stats['raster_refs']}   "
          f"unique imgs: {stats['unique_images']} "
          f"({stats['running_images']} running)")
    print(f"  page renders   : {stats['rendered']}   "
          f"dropped tiny: {stats['dropped_tiny']}")
    print(f"  broken links   : {stats['broken_links']}   "
          f"assets dir: {stats['assets_dir']}/")
    if stats["broken_links"]:
        sys.stderr.write("WARNING: some image links did not resolve.\n")
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
