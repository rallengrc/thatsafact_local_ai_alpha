"""
test_client_term_scan.py — Tests for the client-neutral content scanner.

All fixtures use a made-up client name ("Zorblax"); the real name never appears in tests.
"""

from pathlib import Path

import pytest

import client_term_scan as cts

LABEL = "\U0001F535\U0001F6E1\uFE0F"  # blue shield label emoji


def write(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


@pytest.fixture()
def terms_file(tmp_path):
    f = tmp_path / "terms.txt"
    f.write_text(
        "# comment\n"
        "client: Zorblax Corp\n"
        "term: Zorblax\n"
        "re: Quuxville\\s+Lab\n"
        "cs: \\bZBX\\b\n",
        encoding="utf-8",
    )
    return f


def classes(hits):
    return {(h.path, h.cls) for h in hits}


def test_load_client_name(terms_file):
    assert cts.load_client_name(terms_file) == "Zorblax Corp"


def test_load_client_name_missing_file(tmp_path):
    assert cts.load_client_name(tmp_path / "nope.txt") is None


def test_private_term_literal_regex_and_case_sensitive(tmp_path, terms_file):
    write(tmp_path, "docs/a.md", "built for zorblax last year\n")
    write(tmp_path, "docs/b.md", "met at Quuxville   Lab today\n")
    write(tmp_path, "docs/c.md", "the ZBX program\n")
    write(tmp_path, "docs/d.md", "the zbx program\n")
    hits = cts.scan(tmp_path, terms_file)
    got = classes(hits)
    assert ("docs/a.md", "private-term") in got
    assert ("docs/b.md", "private-term") in got
    assert ("docs/c.md", "private-term") in got
    assert not any(p == "docs/d.md" for p, _ in got)


def test_clean_tree_has_no_hits(tmp_path, terms_file):
    write(tmp_path, "docs/a.md", "Generic Flyte and Ray notes.\n")
    assert cts.scan(tmp_path, terms_file) == []


def test_exempt_private_areas_are_skipped(tmp_path, terms_file):
    write(tmp_path, "Projects/smaas/notes.md", "Zorblax SOW\n")
    write(tmp_path, "Projects/Burstable MLaaS/notes.md", "Zorblax SOW\n")
    write(tmp_path, "Inbox/plan.md", "Zorblax plan\n")
    write(tmp_path, "memories/log.md", "Zorblax log\n")
    assert cts.scan(tmp_path, terms_file) == []


def test_resolved_label_is_flagged_but_placeholder_is_not_in_github(tmp_path, terms_file):
    write(tmp_path, "docs/a.md", f"classification: {LABEL} Acme Proprietary\n")
    write(tmp_path, ".github/instructions/x.md", f"classification: {LABEL} [client] Proprietary\n")
    got = classes(cts.scan(tmp_path, terms_file))
    assert ("docs/a.md", "resolved-label") in got
    assert not any(p.startswith(".github/") for p, _ in got)


def test_unresolved_placeholder_flagged_in_regular_docs_only(tmp_path, terms_file):
    write(tmp_path, "docs/a.md", f"classification: {LABEL} [client] Proprietary\n")
    write(tmp_path, "Resources/Templates/t.md", f"classification: {LABEL} [client] Proprietary\n")
    got = classes(cts.scan(tmp_path, terms_file))
    assert ("docs/a.md", "unresolved-client-placeholder") in got
    assert not any(p.startswith("Resources/Templates/") for p, _ in got)


def test_generic_classes_without_terms_file(tmp_path):
    write(tmp_path, "docs/a.md", "ping build01.corp and mail jane@acme-example.io\n")
    got = classes(cts.scan(tmp_path, None))
    assert ("docs/a.md", "internal-host") in got
    assert ("docs/a.md", "email-address") in got


def test_allowed_emails_not_flagged(tmp_path):
    write(tmp_path, "docs/a.md", "bot 123+x@users.noreply.github.com and a@example.com\n")
    assert cts.scan(tmp_path, None) == []


def test_third_party_docs_only_get_private_terms(tmp_path, terms_file):
    write(tmp_path, "Resources/aws/guide.md", "host ip-10-0-0-1.ec2.internal mail a@b.io\n")
    write(tmp_path, "Resources/aws/leak.md", "Zorblax inside vendor doc\n")
    write(tmp_path, "Resources/aws/acronym.md", "the ZBX feature of the vendor\n")
    got = classes(cts.scan(tmp_path, terms_file))
    assert ("Resources/aws/leak.md", "private-term") in got
    assert not any(p in ("Resources/aws/guide.md", "Resources/aws/acronym.md") for p, _ in got)


def test_paths_argument_limits_scope(tmp_path, terms_file):
    write(tmp_path, "a/x.md", "Zorblax\n")
    write(tmp_path, "b/y.md", "Zorblax\n")
    got = classes(cts.scan(tmp_path, terms_file, paths=["a"]))
    assert got == {("a/x.md", "private-term")}


def test_binary_and_unreadable_files_are_skipped(tmp_path, terms_file):
    (tmp_path / "img.png").write_bytes(b"\x89PNG Zorblax")
    write(tmp_path, "ok.md", "fine\n")
    assert cts.scan(tmp_path, terms_file) == []


def test_main_never_prints_the_matched_term(tmp_path, terms_file, capsys):
    write(tmp_path, "docs/a.md", "line one\nbuilt for Zorblax\n")
    rc = cts.main(["--root", str(tmp_path), "--terms-file", str(terms_file)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "docs/a.md:2" in out
    assert "private-term" in out
    assert "orblax" not in out


def test_main_exit_zero_and_notice_without_terms_file(tmp_path, capsys):
    write(tmp_path, "docs/a.md", "clean\n")
    rc = cts.main(["--root", str(tmp_path), "--terms-file", str(tmp_path / "missing.txt")])
    out = capsys.readouterr().out
    assert rc == 0
    assert "generic classes only" in out


def test_export_memories_label_uses_private_client_name(tmp_path):
    import export_memories

    terms = tmp_path / "terms.txt"
    terms.write_text("client: Zorblax Corp\n", encoding="utf-8")
    assert export_memories.classification_label(terms) == f"{LABEL} Zorblax Corp Proprietary"


def test_export_memories_label_falls_back_to_placeholder(tmp_path):
    import export_memories

    assert export_memories.classification_label(tmp_path / "missing.txt") == f"{LABEL} [client] Proprietary"


def test_personal_absolute_path_flagged_in_first_party_docs(tmp_path):
    write(tmp_path, "docs/a.md", "[x](/Users/jdoe/work/mlaas/README.md)\n")
    write(tmp_path, "docs/b.md", "see C:\\Users\\jdoe\\work\\mlaas\\README.md\n")
    got = classes(cts.scan(tmp_path, None))
    assert ("docs/a.md", "personal-abs-path") in got
    assert ("docs/b.md", "personal-abs-path") in got


def test_placeholder_user_paths_and_container_paths_not_flagged(tmp_path):
    write(
        tmp_path,
        "docs/a.md",
        "use /Users/<user>/mlaas or /Users/username/mlaas or /Users/.../x\n"
        "container /home/ray/anaconda3 and C:\\Users\\<user>\\mlaas\n",
    )
    assert cts.scan(tmp_path, None) == []


def test_third_party_source_line_checked_for_personal_path(tmp_path):
    write(tmp_path, "Resources/aws/a.md", "> **Source:** `/Users/jdoe/work/mlaas/Resources/aws/a.pdf`\n")
    write(tmp_path, "Resources/aws/b.md", "vendor example: cd /Users/jdoe/project\n")
    got = classes(cts.scan(tmp_path, None))
    assert ("Resources/aws/a.md", "personal-abs-path") in got
    assert not any(p == "Resources/aws/b.md" for p, _ in got)
