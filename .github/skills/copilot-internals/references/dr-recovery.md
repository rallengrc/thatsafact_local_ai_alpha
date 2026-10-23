# DR-Sync Recovery: Matching Pending Entries to Git Commits

**Related Skill:** `.github/skills/copilot-internals/SKILL.md`  
**Purpose:** Reconstruct pending session log entries from git history when JSONL or transcripts have gaps.

---

## The Recovery Pattern

When session log entries exist as user prompts but Actions/Results are marked `(pending)` from a prior DR-sync (disaster recovery sync) or unlogged session, use git history to reconstruct the work:

1. **Extract commit hashes** relating to the topic area:
   ```bash
   git log --all -S"ClassName" --oneline -n 20
   ```
2. **Correlate commits to prompts** — match commit messages and code changes to session prompt topics and timestamps.
3. **Extract Actions from code state** — inspect affected files, test modifications, and configuration changes from commits:
   ```bash
   git show <hash> --stat
   git show <hash> --name-only
   ```
4. **Validate with timestamps** — verify commit dates cluster near the prompts' time range.
5. **Reconstruct Nav lines** — cite actual file paths from commit diffs (`git show <hash> --name-only`).

---

## Anti-Pattern to Avoid

Do not invent work details that do not match git evidence. If uncertain about exact execution details, mark as `[reconstructed from commit <hash> with confidence 0.85]`.
