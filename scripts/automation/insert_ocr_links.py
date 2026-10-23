#!/usr/bin/env python3
"""Insert an idempotent 'OCR transcript' link under each high-value figure in the
main guide, pointing at its Markdown sidecar under images/pakt/ocr/."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT / "Resources" / "third_party_docs" / "docker-k8s" / "images"
# Derive the figures subdir dynamically (it contains manifest.json) so we never
# hardcode a name that can be mistyped.
FIG_DIR = next((d for d in IMAGES_DIR.iterdir()
                if d.is_dir() and (d / "manifest.json").exists()), None)
if FIG_DIR is None:
    raise SystemExit("Could not locate manifest.json under images/")
MANIFEST = FIG_DIR / "manifest.json"
OCR_DIR = FIG_DIR / "ocr"
MD = ROOT / "Resources" / "third_party_docs" / "docker-k8s" / "operational-ai-with-docker-color-images.md"

items = json.loads(MANIFEST.read_text(encoding="utf-8"))
ocr_by_base = {e["filename"].replace(".png", "") for e in items if e.get("ocr")}
# Fallback: if manifest ocr fields didn't persist, discover sidecars on disk.
if not ocr_by_base:
    ocr_by_base = {p.name.replace(".md", "") for p in OCR_DIR.glob("*.md")}
print("figures dir:", FIG_DIR.name, "| ocr sidecars:", len(ocr_by_base))

# Match Markdown image lines: ![alt](path.png) via plain string ops (no regex).
PREFIX = "> \U0001F4DD **OCR transcript:** [Fig text]("
SUFFIX = ")"

lines = MD.read_text(encoding="utf-8").split("\n")
out = []
added = 0
for i, ln in enumerate(lines):
    out.append(ln)
    if not ln.startswith("!["):
        continue
    open_idx = ln.find("](")
    close_idx = ln.rfind(")")
    if open_idx == -1 or close_idx <= open_idx:
        continue
    path = ln[open_idx + 2:close_idx].strip()
    if not path.endswith(".png"):
        continue
    base = path.replace("\\", "/").rsplit("/", 1)[-1][: -len(".png")]
    if base in ocr_by_base and not base.startswith("ch_"):
        ocr = "images/" + FIG_DIR.name + "/ocr/" + base + ".md"
        link = PREFIX + ocr + SUFFIX
        # idempotent: scan forward past blank lines for an existing link
        j = i + 1
        already = False
        while j < len(lines) and lines[j].strip() == "":
            j += 1
        if j < len(lines) and lines[j].strip() == link:
            already = True
        if not already:
            out.append("")
            out.append(link)
            added += 1

MD.write_text("\n".join(out), encoding="utf-8")
print(f"inserted {added} inline OCR links (high-value figures)")
