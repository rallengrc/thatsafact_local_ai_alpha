#!/usr/bin/env python3
"""
setup_memory_link.py — Point this machine's Claude Code project memory at the repo.

Claude Code keeps per-project memory in a machine-local directory:

    ~/.claude/projects/<slugified-project-path>/memory/

That path embeds the local user profile, so it differs on every laptop and cannot
itself live in git. This script replaces it with a link to the tracked directory:

    <repo>/memories/mlaas/

Run once per machine after cloning. Idempotent — re-running a correct link is a no-op.

Links are symlinks where possible. On Windows, symlink creation needs Administrator
or Developer Mode, so this falls back to a directory junction (mklink /J), which is
equivalent for local paths and needs no elevation.

Usage:
    python scripts/automation/setup_memory_link.py [--dry-run] [--force]

    --dry-run   Report what would change; touch nothing.
    --force     Overwrite files in the repo that conflict with existing memory files.
"""
import argparse
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TARGET = REPO_ROOT / "memories" / "mlaas"


def slug_candidates(project_path: Path) -> list[str]:
    r"""Claude Code slugifies the absolute project path by replacing separators with '-'.

    e.g. C:\Users\<user>\projects\mlaas -> C--Users-<user>-projects-mlaas
         /Users/<user>/projects/mlaas   -> -Users-<user>-projects-mlaas

    Dots are also normalized in some versions, so offer both spellings and let the
    caller prefer whichever already exists on disk.
    """
    raw = str(project_path)
    base = "".join("-" if c in ':/\\' else c for c in raw)
    dotted = base.replace(".", "-")
    return [base] if base == dotted else [base, dotted]


def resolve_link_path(project_path: Path) -> Path:
    """Locate this machine's Claude Code memory directory for the given project."""
    projects_dir = Path.home() / ".claude" / "projects"
    candidates = slug_candidates(project_path)
    for slug in candidates:
        if (projects_dir / slug).is_dir():
            return projects_dir / slug / "memory"
    # Nothing on disk yet (Claude Code has not opened this project here).
    return projects_dir / candidates[0] / "memory"


def read_link(path: Path) -> Path | None:
    """Return a link's target, or None if path is not a link.

    Covers both symlinks and Windows junctions; os.readlink handles junctions on
    Python 3.8+, but raises OSError on an ordinary directory. Extended-length
    prefixes are stripped so callers can compare the result against a plain path.
    """
    try:
        raw = os.readlink(path)
    except OSError:
        return None
    # Windows junctions report an extended-length path ("\\?\C:\..."),
    # so strip that prefix to compare equal against an ordinary path.
    if raw.startswith("\\\\?\\UNC\\"):
        raw = "\\\\" + raw[8:]
    elif raw.startswith("\\\\?\\"):
        raw = raw[4:]
    return Path(raw)


def describe(path: Path) -> str:
    target = read_link(path)
    if target is not None:
        return f"link -> {target}"
    if path.is_dir():
        return "real directory"
    if path.exists():
        return "file"
    return "missing"


def migrate_contents(source: Path, dest: Path, force: bool, dry_run: bool) -> list[str]:
    """Move any real memory files out of the machine-local dir into the repo."""
    moved, conflicts = [], []
    for item in sorted(source.rglob("*")):
        if item.is_dir():
            continue
        rel = item.relative_to(source)
        out = dest / rel
        if out.exists() and not force:
            conflicts.append(str(rel))
            continue
        moved.append(str(rel))
        if not dry_run:
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, out)
    if conflicts:
        print("  ! already in repo, left untouched (use --force to overwrite):")
        for c in conflicts:
            print(f"      {c}")
    return moved


def on_rm_error(func, path, _exc):
    """Clear the read-only bit Windows sets on some files, then retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def make_link(link: Path, target: Path) -> str:
    """Create link -> target. Returns the kind of link actually created."""
    try:
        link.symlink_to(target, target_is_directory=True)
        return "symlink"
    except OSError:
        if os.name != "nt":
            raise
        # Windows without Administrator / Developer Mode: junctions need no elevation.
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(target)],
            check=True, capture_output=True, text=True,
        )
        return "junction"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report what would change; touch nothing")
    ap.add_argument("--force", action="store_true",
                    help="overwrite repo files that conflict with existing memory files")
    args = ap.parse_args()

    link = resolve_link_path(REPO_ROOT)
    print(f"repo memory   : {TARGET}")
    print(f"claude memory : {link}")
    print(f"current state : {describe(link)}")

    if not TARGET.is_dir():
        print(f"\nERROR: {TARGET} does not exist. Is this a full clone of the repo?",
              file=sys.stderr)
        return 1

    existing = read_link(link)
    if existing is not None:
        if existing.resolve() == TARGET.resolve():
            print("\nAlready linked correctly. Nothing to do.")
            return 0
        print(f"\nReplacing link that points elsewhere ({existing}).")
        if not args.dry_run:
            link.unlink()

    elif link.is_dir():
        files = [p for p in link.rglob("*") if p.is_file()]
        if files:
            print(f"\nFound {len(files)} existing memory file(s); copying into the repo:")
            for rel in migrate_contents(link, TARGET, args.force, args.dry_run):
                print(f"      {rel}")
        else:
            print("\nExisting directory is empty; nothing to migrate.")
        if not args.dry_run:
            shutil.rmtree(link, onerror=on_rm_error)

    elif link.exists():
        # Claude Code sometimes leaves a stray zero-byte placeholder file here.
        if link.stat().st_size > 0 and not args.force:
            print(f"\nERROR: {link} is a non-empty file. Move it aside, or pass --force.",
                  file=sys.stderr)
            return 1
        print("\nRemoving stray placeholder file.")
        if not args.dry_run:
            link.unlink()

    if args.dry_run:
        print("\n[dry run] Would link the two paths above. No changes made.")
        return 0

    link.parent.mkdir(parents=True, exist_ok=True)
    kind = make_link(link, TARGET)
    print(f"\nCreated {kind}: {link} -> {TARGET}")
    print("Project memory is now stored in the repo and tracked by git.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
