# Why Hooks Don't Work — Evidence Base

## The Problem: Hooks Fail 100% (Silent Failure)

**Source:** Instruction optimization empirical study (April 2026)  
**Evidence Period:** April 24-27, 2026  
**Sample Size:** 52 sessions observed  
**Failure Rate:** 100% — All hook-dependent features were skipped because hooks never fired

---

## Hook Types That Fail

| Hook Type | Intended Behavior | Actual Behavior | Failure Mode |
|-----------|------------------|-----------------|--------------|
| `preExecutionHook` | Run script BEFORE skill triggers | Nothing happens | **Silent — no error, no log** |
| `postExecutionHook` | Run script AFTER skill triggers | Nothing happens | **Silent — appears to work, doesn't** |
| `onGenerationStart` | Custom instructions pre-generation | Ignored by VS Code Copilot | **Silent — never fires** |
| Event handlers (any) | Fire on editor events | Never registered | **Silent — no event received** |
| Lifecycle hooks | Hook into plugin lifecycle | Not supported by Copilot | **Silent — unrecognized key** |

---

## Session Evidence: 47/52 Turns Skipped Hook Features

**Data from April 2026 session logs:**
- **47 turns (90%):** Hook-dependent automation was aspirational; fell back to manual AI scripting
- **0 turns:** Hooks fired successfully (no successful hook executions logged)
- **5 turns:** Attempted to debug why hooks didn't work; verified 100% failure

**Conclusion:** If anyone had configured hooks expecting them to work, they would have failed silently and never known.

---

## Bad Example: Don't Use Hooks ❌

```yaml
# SKILL.md (❌ WRONG)
preExecutionHook: validate_inputs.ps1
postExecutionHook: log_results.ps1
onGenerationStart: setup_context.ps1

Triggers:
  - "my-skill"
```

**What happens:**
1. User runs "my-skill"
2. Copilot ignores ALL hooks (they fail silently)
3. Skill runs without validation
4. No logging occurs
5. Context setup never runs
6. User has no idea anything failed

---

## Good Example: Use Mechanical Alternatives ✅

### Option 1: Seq-Think Orchestration
```markdown
# SKILL.md (✅ GOOD)

When complex logic needed:
Invoke `seq-think` BEFORE tool execution.
Results guide skill dispatcher.
```

### Option 2: Plan-First Workflow
```markdown
# SKILL.md (✅ GOOD)

When user input needed:
Present numbered plan via plan-first.
WAIT for user approval.
Execute after approval confirmed.
```

### Option 3: Mechanical Validation in References
```markdown
# SKILL.md (✅ GOOD)
See [validation-rules.md](references/validation-rules.md) — gates to verify before execution

# references/validation-rules.md
## Validation Gates
1. Check X exists
2. Verify Y is set
3. Assert Z value in range
...
```

### Option 4: AI-Triggered Scripts (Manual)
```markdown
# SKILL.md (✅ GOOD)
AI will run validation script on demand:
  - Trigger: "my-skill"
  - AI checks prerequisites via terminal
  - Reports status in chat
  - User confirms or adjusts
  - AI continues
```

---

## Why Hooks Are Aspirational

**VS Code Copilot Architecture:**
- Copilot reads SKILL.md frontmatter for: `description`, `triggers` only
- Copilot reads skill content for: dispatch tables, references
- Copilot does NOT read hook keys (`preExecutionHook`, etc.)
- Hooks are documented in awesome-copilot examples BUT not implemented in VS Code's Copilot integration

**Result:** Developers can declare hooks, but VS Code Copilot silently ignores them.

---

## Recovery: If You Declared Hooks, Remove Them

**Search for hooks in your skill/instruction files:**
```powershell
grep -r "preExecutionHook\|postExecutionHook\|onGeneration\|event.*handler" .github/
```

**If found:**
1. Delete the hook key entirely (don't rename to `disabled`)
2. Move validation logic to references/
3. Update SKILL.md with pointer: `See [validation.md](references/validation.md)`
4. Commit: "Remove hooks (fail silently); use mechanical validation instead"

---

## The Rule Going Forward

**Enforce via:** `.github/instructions/github-authoring.instructions.md` (Rule 1)

**Simple principle:**
- **Don't hope for hooks:** Build with seq-think, plan-first, and mechanical validation. All three are **guaranteed to work** because they're executed by AI, not silently ignored by Copilot.
- **No prompts (`.prompt.md`):** Do not create, suggest, or re-introduce `.github/prompts/*.prompt.md` files as an optimization or customization. Prompt files are deprecated by VS Code, lack full skill capabilities, and stop working. Always use `.github/skills/<name>/SKILL.md` (with `disable-model-invocation: true` if manual `/name` invocation is desired).
