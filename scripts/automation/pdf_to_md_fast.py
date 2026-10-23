#!/usr/bin/env python3
"""Fast text + deduplicated-image-gallery converter for large reference PDFs.

For very large, text-heavy AWS reference PDFs where the embedded images are
line-art diagrams (0 recoverable OCR text) this avoids the per-page
get_image_info cost (which is O(pages) and ~minutes on 3000-page docs) and the
per-page image spam that bloats output to tens of MB.

Output:
  * "## Page N" sections with the page's text (fast get_text('text')).
  * A deduplicated "## Extracted images" gallery at the end: each distinct
    content-sized image saved once and listed (icons + full-page background
    rectangles are dropped).
  * AI-searchable frontmatter is added separately by scripts/add_aws_frontmatter.py.
"""
import argparse
import hashlib
import os
import sys
import time

try:
    import pymupdf as fitz
except Exception:
    sys.stderr.write("PyMuPDF not importable. Install in the venv.\n")
    sys.exit(3)


def _source_label(pdf_path: str) -> str:
    """Repo-relative POSIX path for the Source line (never an absolute home path)."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    try:
        rel = os.path.relpath(pdf_path, repo_root)
    except ValueError:  # different drive on Windows
        return os.path.basename(pdf_path)
    return os.path.basename(pdf_path) if rel.startswith("..") else rel.replace(os.sep, "/")


def is_content_image(w: int, h: int) -> bool:
    """Keep real diagrams; drop icons (<1000px area) and full-page rectangles."""
    area = w * h
    if area < 1000:
        return False
    if w >= 1500 and h >= 1500:
        return False
    return True


def convert(pdf_path: str, out_md: str, min_dim: int = 8) -> dict:
    pdf_path = os.path.abspath(pdf_path)
    out_md = os.path.abspath(out_md)
    stem = os.path.splitext(os.path.basename(out_md))[0]
    out_dir = os.path.dirname(out_md) or "."
    assets_dir = os.path.join(out_dir, stem + ".assets")
    os.makedirs(assets_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    n = doc.page_count
    rel_prefix = stem + ".assets"

    # ---- distinct content images: scan xrefs once (fast, no per-page image parse)
    xref_first: dict[int, int] = {}
    for i in range(n):
        for im in doc[i].get_images():  # lightweight, no full=True
            xref_first.setdefault(im[0], i + 1)

    saved: dict[int, dict] = {}
    for xref, first_page in xref_first.items():
        try:
            info = doc.extract_image(xref)
            data = info.get("image") or b""
            if not data:
                continue
            w, h = info.get("width", 0), info.get("height", 0)
            if min(w, h) < min_dim or not is_content_image(w, h):
                continue
            ext = info.get("ext", "png")
            if ext.lower() in ("", "png"):
                if data[:8] == b"\x89PNG\r\n\x1a\n":
                    ext = "png"
                elif data[:3] == b"\xff\xd8\xff":
                    ext = "jpg"
                else:
                    ext = "png"
            fname = hashlib.sha1(data).hexdigest()[:16] + "." + ext.lower()
            with open(os.path.join(assets_dir, fname), "wb") as out:
                out.write(data)
            saved[xref] = {"file": fname, "w": w, "h": h, "page": first_page}
        except Exception:
            continue

    # ---- write MD: per-page text + deduplicated gallery ----
    ts = time.strftime("%Y-%m-%d %H:%M")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(f"# {stem}\n\n")
        f.write(f"> **Source:** `{_source_label(pdf_path)}`\n")
        f.write(f"> **Generated:** {ts}\n")
        f.write(f"> **Converter:** `scripts/pdf_to_md_fast.py` "
                f"(mode=text+gallery, min-dim={min_dim})\n\n")
        f.write("---\n\n")
        for i in range(n):
            f.write(f"## Page {i + 1}\n\n")
            text = doc[i].get_text("text").rstrip()
            f.write(text + "\n\n" if text else "_[no text on this page]_\n\n")
        f.write("\n---\n\n## Extracted images\n\n")
        f.write(f"{len(saved)} distinct content image(s) in `{rel_prefix}/` "
                "(icons and full-page background rectangles dropped).\n\n")
        f.write("```text\n")
        for xref in sorted(saved, key=lambda x: saved[x]["page"]):
            r = saved[xref]
            f.write(f"p{r['page']:<5} {r['file']}  {r['w']}x{r['h']}\n")
        f.write("```\n")
    doc.close()
    return {"pdf": os.path.basename(pdf_path), "pages": n,
            "images": len(saved), "out_md": out_md}


def main() -> int:
    ap = argparse.ArgumentParser(description="Fast text + image-gallery PDF->MD")
    ap.add_argument("input")
    ap.add_argument("output", nargs="?", default=None)
    ap.add_argument("--min-dim", type=int, default=8)
    args = ap.parse_args()
    out = args.output or (os.path.splitext(args.input)[0] + ".md")
    s = convert(args.input, out, min_dim=args.min_dim)
    print(f"pages={s['pages']} images={s['images']} -> {s['out_md']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
