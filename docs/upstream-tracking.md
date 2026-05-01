# Tracking obra/superpowers Upstream

This plugin is a **rewrite**, not a fork, of [obra/superpowers](https://github.com/obra/superpowers). The shared lineage is acknowledged in the repo `LICENSE` and `CHANGELOG.md`. Upstream evolves independently; this document defines how the maintainer keeps an eye on it without committing to a tight coupling.

## Why a tracking process

A rewrite drifts from its source over time. Without periodic checks:

- Useful upstream improvements (new skills, sharper trigger language, better Red Flags tables) land late or not at all.
- Diverging trigger descriptions can produce subtly different activation behavior across the two ecosystems, surprising users who move between them.
- Bug fixes obra ships quietly may take months to reach our consumers if no one looks.

A tracking cadence is the cheapest insurance against silent drift.

## Cadence

**Quarterly review.** Once per calendar quarter (target: first Monday of Jan / Apr / Jul / Oct), the maintainer (or a delegate) runs the diff exercise below. Out-of-cycle reviews are fine when an upstream release is announced or when a contributor flags a specific drift.

**Trigger-driven review.** Anytime an issue or PR mentions "obra has X", "upstream changed Y", or names a specific upstream commit/tag, treat it as a partial review of just the area in question.

## What the review covers

For each quarterly review, fetch upstream HEAD and compare against the last recorded sync point:

```bash
# Initial setup
git remote add obra https://github.com/obra/superpowers.git    # one time

# Each review
git fetch obra
git log <last-sync-sha>..obra/main --oneline -- skills/        # behavior changes
git log <last-sync-sha>..obra/main --oneline -- agents/        # if we ever ship agents
git log <last-sync-sha>..obra/main --oneline -- hooks/         # hook surface changes
git log <last-sync-sha>..obra/main --oneline -- commands/      # slash command changes
```

Sample skills directly for shape changes:

```bash
git diff <last-sync-sha>..obra/main -- skills/<name>/SKILL.md
```

The first time a review runs, `<last-sync-sha>` is `bc1fbe8` (the commit on which v0.1.1 of this plugin was tagged) — the recorded sync point at the **bottom of this document**.

## Decisions to record per review

Every quarterly review writes an entry to `## Sync log` (below). Each entry captures:

1. **Reviewer / date / commit ranges examined.**
2. **Per upstream change** — one of:
   - **Port:** the change is being adopted into this plugin. Open a bead for the port; reference upstream SHA in the description.
   - **Adapt:** the upstream idea is useful but the implementation will differ here (e.g. because we use `bd` instead of `TodoWrite`). Open a bead.
   - **Skip:** the change doesn't apply to this rewrite. Record the reason inline (one line).
   - **Defer:** worth doing eventually but not this cycle. Bead with "deferred" tag or `bd defer --until=<future>`.
3. **New `<last-sync-sha>` for the next review.** Update the bottom of this file before closing the review.

## What does **not** trigger a port

The rewrite has explicit policy differences from upstream that are intentional, not lag:

- **Persistence layer.** Upstream uses `TodoWrite` and markdown plan/spec files. We use `bd`. Skills that mention specific tools, files, or formats from upstream require translation, not a copy-paste port.
- **Repo structure.** Upstream's `agents/`, `hooks/`, `commands/` directories are not part of our distribution. Improvements there are out of scope.
- **Lockstep MAJOR releases.** This plugin's version numbers do not track upstream's. A breaking change upstream is not automatically a breaking change here.

When porting, preserve the *prescribed behavior* and *trigger semantics* but rewrite the prose to match the bd-native style of the surrounding skills.

## Attribution policy

When a port lands, the commit message and CHANGELOG entry both:

- Reference the upstream SHA the change is derived from.
- Note any deliberate divergence ("upstream uses TodoWrite; this port uses `bd create`").
- Preserve the existing repo-level MIT attribution in `LICENSE` (no per-file headers per the convention established in PR #39).

## Sync log

Append a new entry per review. Most-recent first.

| Date | Reviewer | Range examined | New sync SHA | Notes |
|------|----------|----------------|--------------|-------|
| 2026-04-29 | jhbongaarts | initial (v0.1.0 baseline) | `bc1fbe8` | Initial public release; rewrites 14 obra skills as the v0.1.0 baseline. |

### YYYY-MM-DD — Reviewer name (template)

**Range examined:** `<old-sha>..obra/main`

**Decisions:**

- _(skill / topic)_ — Port / Adapt / Skip / Defer. _(One-line rationale; bead ID if Port or Adapt or Defer.)_

**New sync SHA:** `<new-sha>` (committed in this review.)
