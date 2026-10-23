# Neutral Vocabulary and Term Classes

> **Use this for:** deciding what counts as client commentary, what to write instead, and how the scanner's private term file is laid out. This file names no real client, site or system on purpose.

## Term classes

| Class | What it covers | Write instead |
|-------|----------------|---------------|
| Client / program | The customer's company, division, program acronym, product line | "the customer", or drop the sentence |
| Sites | Research campuses, buildings, cities tied to the client | Drop. For topology say "on-premises site" |
| Internal infrastructure | Internal registry brand, internal storage host, proxy or VPN names, internal hostnames | "internal container registry", "on-prem S3-compatible store", "corporate proxy" |
| People and org | Stakeholder names, team names, ticket or SOW numbers | Drop |
| Engagement framing | "for the client we decided", scope, pricing, schedule, option labels tied to a deal | Move to a note under `Projects/Burstable MLaaS/` |
| Other clients | Any second customer's name or marking | Never in OSS scope; escalate to the user |
| Employer / author | Employer name in `author:` frontmatter | **Open decision.** Leave existing values alone; do not add new ones to OSS files without asking |

## Technique stays, attribution goes

| Keep (generic) | Remove (attribution) |
|----------------|----------------------|
| "Air-gapped or proxy-restricted on-prem VMs; images come from an internal registry mirror" | The customer's name, site, registry brand |
| "Tri-environment model: local Mac, AWS EKS burst, on-prem VMs" | Who owns each environment |
| "Physics-surrogate ML for turbine aerodynamics" | The customer's program names |
| Labels like `mlaas.io/tier` | Labels with a customer domain |

## Diagrams, tests, commits
- Diagram titles, aliases, notes and filenames follow the same classes (plantuml Rule 8).
- Test fixtures use a made-up name such as "Zorblax".
- Commit and PR text describe the change, not the customer.

## Scanner reference
`scripts/automation/client_term_scan.py` reports `path:line: [class]`. Classes:

| Class | Meaning |
|-------|---------|
| `private-term` | Matches an entry in the private term file |
| `resolved-label` | A 🔵 label with a real name filled in, in OSS scope |
| `unresolved-client-placeholder` | The literal placeholder left in a normal doc (allowed only in `.github/`, templates and the label template) |
| `internal-host` | Internal-looking hostname |
| `email-address` | Email address (git remotes, `example.*` and GitHub noreply are ignored) |

Third-party vendor docs (`Resources/aws|flyte|ray|docker-k8s`) get only the literal `client:` / `term:` checks.

### Private term file
`Projects/Burstable MLaaS/.client-terms.txt` (private; never copy it elsewhere):

```
# comment
client: <name>      the client; also used to resolve the label (step 2)
term: <text>        literal, case-insensitive, applied everywhere
re: <regex>         case-insensitive, first-party files only
cs: <regex>         case-sensitive, first-party files only
```

Without the file (for example a fresh OSS clone) only the generic classes run.
