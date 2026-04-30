# Security

## Reporting a vulnerability

If you find a security issue in this plugin — for example, a skill that
instructs an agent in a way that could leak credentials, exfiltrate data,
execute unintended code, or be combined with prompt injection to bypass user
intent — please report it privately rather than opening a public issue.

**Email:** `joe@wtfs.net`

Please include:

- A description of the issue and its impact.
- A minimal reproduction (skill name, prompt, and observed behavior).
- The plugin version (`bd export | jq -r '.version'` or check `.claude-plugin/marketplace.json`).
- Any harness-specific context (Claude Code version, Codex version, OS).

You should expect an initial acknowledgement within 7 days. Coordinated
disclosure timelines are negotiable based on severity and complexity; the
default target is a fix shipped within 30 days of validation, with public
disclosure no earlier than the fix release.

## Threat model — what counts as a vulnerability

The plugin ships **prose instructions to AI agents**, not executable code that
runs against user data directly. Agent harnesses (Claude Code, Codex, etc.)
are responsible for sandboxing tool execution. With that in mind, in-scope
concerns include:

- **Skill instructions that could be weaponized via prompt injection** — e.g.
  a SKILL.md that tells an agent to run shell commands derived from
  attacker-controlled content without sanitization, or to write secrets to a
  location an attacker can read.
- **Reference-loaded files that bypass the skill's intended trigger** — e.g.
  a `references/*.md` that, when loaded, suspends rules established in
  `SKILL.md`.
- **Workflow scripts** under `scripts/` or `plugins/*/skills/*/scripts/` that
  execute with insufficient input validation (command injection, path
  traversal, unsafe eval).
- **Release pipeline issues** — supply-chain risks in `.github/workflows/`,
  exposed secrets, attestation bypass.

Out of scope:

- General prompt-injection susceptibility in the underlying agent harness.
  Report those upstream to the harness maintainer.
- The behavior of `bd` (beads) itself. Report at <https://github.com/steveyegge/beads>.
- Issues in `obra/superpowers` upstream content. Report at <https://github.com/obra/superpowers>.

## Coordinated disclosure

We will credit reporters who request credit in the release notes for the fix
release. If you prefer to remain anonymous, that is also fine.

If you believe a fix has been silently shipped that addresses your report,
please confirm with us before publishing your write-up so we can coordinate
the public timing.
