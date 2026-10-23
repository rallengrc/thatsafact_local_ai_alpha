#!/usr/bin/env python3
"""OCR the high-value Packt figures from the docker-k8s PDF and store transcripts.

Output: per-figure Markdown sidecars under <images>/ocr/<figure>.md
        + an `ocr` field added to each manifest.json entry.

Only the "high value" figures (Docker/K8s desktop screenshots, terminal output,
dashboards, model logs, Compose graphs) are OCR'd. Pure line-art "mental model /
architecture / migration" diagrams are skipped — their captions already carry the
meaning and OCR would only add label noise.

Usage:
    .venv/bin/python scripts/ocr_packt_figures.py            # OCR high-value set
    .venv/bin/python scripts/ocr_packt_figures.py --all      # OCR every figure
    .venv/bin/python scripts/ocr_packt_figures.py --dry-run  # list what would be OCR'd
"""
import json
import os
import re
import subprocess
import sys
import datetime
from pathlib import Path

# Resolve the images dir without hardcoding the subfolder name (avoids shell typos).
ROOT = Path(__file__).resolve().parent.parent.parent
IMAGES_DIR = ROOT / "Resources" / "third_party_docs" / "docker-k8s" / "images"
# Derive the figures subdir dynamically (it contains manifest.json).
FIG_DIR = next((d for d in IMAGES_DIR.iterdir()
                if d.is_dir() and (d / "manifest.json").exists()), None)
if FIG_DIR is None:
    raise SystemExit("Could not locate manifest.json under images/")
MANIFEST = FIG_DIR / "manifest.json"
OCR_DIR = FIG_DIR / "ocr"

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path and SCRIPTS_DIR.exists():
    sys.path.insert(0, str(SCRIPTS_DIR))
from common_platform import find_executable

TESS = find_executable("tesseract") or "tesseract"

# HIGH value = UI screenshots, terminals, dashboards, logs, command output,
# config files, tables. LOW value = conceptual line-art diagrams.
HIGH_KW = [
    "view", "dashboard", "desktop", "terminal", "output", "log", "console",
    "interface", "screenshot", "result", "response", "screen", "window", "panel",
    "command", "exec", "inspect", "build", "run", "pull", "start", "stop",
    "prune", "system", "container", "image", "registry", "port", "volume",
    "network", "config", "yaml", "compose", "manifest", "table", "metric",
    "graph", "chart", "monitor", "trace", "queue", "pod", "deploy", "service",
    "node", "kubernetes", "kubectl", "docker", "agent", "chatbot", "ui",
    "catalog", "lifecycle", "settings", "install", "enable", "authentication",
    "connection", "client", "controller", "sandbox", "micro", "team",
]
LOW_KW = [
    "mental model", "architecture", "workflow", "pipeline", "flow", "diagram",
    "migration", "pattern", "component", "layer", "overview", "map", "benefit",
    "compar", "why", "role", "exclus", "practical mental", "conceptual",
    "comparison of", "difference between",
]


def classify(caption: str) -> str:
    c = (caption or "").lower()
    if any(k in c for k in LOW_KW):
        return "LOW"
    if any(k in c for k in HIGH_KW):
        return "HIGH"
    return "MID"


def run_tesseract(png_path: str) -> tuple[str, int]:
    """Return (transcript_text, exit_code)."""
    try:
        out = subprocess.run(
            [TESS, png_path, "stdout", "--psm", "3", "-l", "eng"],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        return "⚠ OCR timed out (120s)", 124
    return out.stdout.strip(), out.returncode


def clean(text: str) -> str:
    # Collapse 3+ blank lines and strip trailing spaces per line.
    lines = [ln.rstrip() for ln in text.splitlines()]
    collapsed = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()
    return collapsed


def figure_id(caption: str) -> str:
    m = re.match(r"Figure\s+(\d+)\.(\d+)", caption or "")
    return f"fig_{m.group(1)}_{m.group(2)}" if m else "unknown"


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--high"
    do_all = mode == "--all"
    dry = "--dry-run" in sys.argv

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    OCR_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    targets = []
    for entry in manifest:
        cls = classify(entry.get("caption", ""))
        if do_all or cls == "HIGH":
            targets.append((entry, cls))

    print(f"Manifest: {MANIFEST.name} ({len(manifest)} entries)")
    print(f"OCR targets: {len(targets)} ({'ALL' if do_all else 'HIGH-value'})")

    done, empty = 0, 0
    for entry, cls in targets:
        png = IMAGES_DIR.parent / entry["relative_path"]
        if not png.exists():
            print(f"  SKIP (missing): {entry['filename']}")
            continue

        base = entry["filename"].replace(".png", "")
        ocr_md = OCR_DIR / f"{base}.md"

        if dry:
            print(f"  [dry] {entry['filename']}  ({cls})")
            continue

        text, code = run_tesseract(str(png))
        text = clean(text)
        cap = entry.get("caption", "")
        fid = figure_id(cap)
        empty_note = "" if text else "\n_(no text extracted — likely a pure graphic)_\n"
        if not text:
            empty += 1

        ocr_md.write_text(
            f"# OCR Transcript: {cap}\n\n"
            f"- **Figure:** {fid}\n"
            f"- **Source image:** `{entry['filename']}`\n"
            f"- **PDF page:** {entry.get('page')}\n"
            f"- **Dimensions:** {entry.get('width')}×{entry.get('height')}\n"
            f"- **OCR engine:** tesseract 5.5.3 (eng)\n"
            f"- **Generated:** {ts}\n\n"
            f"## Transcript\n\n"
            f"```\n{text}\n```\n"
            f"{empty_note}\n---\n"
            f"_Caption: {cap}_\n",
            encoding="utf-8",
        )
        entry["ocr"] = f"ocr/{base}.md"
        entry["ocr_status"] = "ok" if text else "empty"
        done += 1
        tag = "ok" if text else "EMPTY"
        print(f"  {tag:6s} {entry['filename']}  ({cls})")

    if not dry:
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"\nWrote {done} transcripts to {OCR_DIR.relative_to(ROOT)}/")
        print(f"Empty (no text): {empty} | manifest updated with `ocr` fields")
    return 0


if __name__ == "__main__":
    sys.exit(main())
