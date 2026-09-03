---
name: release-ops
description: Collect the ops steps a release needs, from every PR merged since the last release plus a reverse check against the diff itself.
argument-hint: "[<since-tag>] [--to <ref>]"
disable-model-invocation: true
---

# release-ops

Before cutting a release, gather everything a human must do by hand to deploy it — new env vars, migrations, seed SQL, provisioning, flags — and check that list against the diff, so nothing that needs doing is missing from it.

> **Result**: one checklist, every item traceable to a PR or a commit, plus an explicit list of what the diff needs that nobody declared.

The point is not the summary. Summing up what the PRs already say is the easy half and the half that can't catch anything. **The value is the reverse check in Phase 4** — finding what the code needs that no PR mentioned.

## Phase 1 — Anchor, and check the anchor is usable

```sh
git fetch origin --tags
git tag -l 'v*' --sort=-v:refname | grep -v -- '-rc' | head -1     # last stable release
```

Use the argument if the user gave one. Otherwise the newest **stable** tag — exclude `-rc`/`-alpha`/`-beta`. Release-candidate tags are a poor anchor: they are often cut on branches that were later rebased or squashed, so the tag ends up outside the mainline even though its content shipped.

Then verify the anchor is on the line you are releasing from:

```sh
git merge-base --is-ancestor <tag> <to-ref>      # --to, default origin/main
```

**False means stop and say so.** The tag points at a commit that is not in this branch's history — a release cut on a branch that was never merged back, or a rebased branch. Every "already released / not yet released" verdict below is unreliable in that state. Report it, list what you found anyway, and ask the user for a commit to use as the real starting point. Do not guess your way past this: guessing wrong either drops an ops step from the list, or re-lists one that was already executed — and re-running a non-idempotent seed is its own outage.

## Phase 2 — Collect the PRs

Do **not** grep PR numbers out of merge-commit messages. That misses every squash- and rebase-merged PR (they leave no `Merge pull request` line at all), and those PRs' ops steps would vanish silently.

Ask GitHub, then let git decide what already shipped:

```sh
gh pr list --state merged --base <default> --limit 100 \
  --json number,title,body,mergedAt,mergeCommit,author
```

For each PR, `mergeCommit.oid` is the commit that actually landed on the base branch — it exists for merge, squash and rebase alike:

```sh
git merge-base --is-ancestor <oid> <tag>    # 0 = already released, non-0 = in this release
```

Two things to get right:

- **If the result count equals `--limit`, the list is truncated.** Raise it or page; a silently cut list drops the oldest PRs of the release, which are the ones people have already forgotten.
- **PR number order is not merge order.** A long-lived branch opened months ago can merge yesterday and carry a low number. Never filter by number range, and never assume a low number means "old news" — judge only by `--is-ancestor`.

## Phase 3 — Pull the declared ops steps

From each in-release PR's body, take the ops section (the one `ship-pr` writes). Keep the PR number on every item — the reader will want to open it.

PRs merged before that convention existed have no such section. Mark them **"not declared"**, not "none" — Phase 4 is what covers them.

## Phase 4 — Reverse check: what does the diff need that nobody said?

This is the part that catches real problems. Run the same detection over the whole release range, then subtract what Phase 3 already declared.

```sh
git diff <tag>..<to-ref> --stat
git diff <tag>..<to-ref> --diff-filter=A --name-only     # added files
git log  <tag>..<to-ref> --oneline
```

| Signal | How to find it |
|---|---|
| New env var / config key | new `os.Getenv` / `process.env.` / `getenv` / `ENV[` reads in the diff; new lines in `.env.example`, chart values, config schemas |
| Migration | added files under the project's migration directory — note renames and version collisions, not just additions |
| Seed / backfill SQL | added `.sql` with `INSERT`/`UPDATE`; new scripts under `scripts/`, `db/seeds/` |
| New dependency or external service | `go.mod` / `package.json` / `requirements.txt` / `Cargo.toml` diffs; new API hosts, queues, cron entries, buckets |
| Feature flag | new flag and its default value |

Everything the diff needs but no PR declared goes in its own section of the output. Two sources feed it:

- **Commits pushed straight to the default branch**, which belong to no PR at all. In a repo where admins can bypass branch protection this is not an edge case — check `git log <tag>..<to-ref> --no-merges` for commits with no PR reference.
- **PRs whose body predates the ops convention**, or whose author left the section out.

For each, attribute it to the commit SHA rather than a PR, so the reader can still find out who and why.

## Phase 5 — The checklist

Order the items the way they must be executed, not the way they were found. Migrations before the code that reads the new columns; seeds after the migration; flags last.

```markdown
# Release <next-version> — ops checklist
since v1.3.3 (2026-09-01) · 7 PRs · 12 direct commits

## Declared in PRs
- [ ] **Migration** `000085_screening_waiver.up.sql` — renamed from 000074 after a collision; check no environment ran the old number (#43)
- [ ] **Env** `PAYMENT_TIMEOUT_MS` — no default, service won't start without it; production 3000 (#45)

## Not declared — found in the diff
- [ ] **Migration** `000086_address_lookup.up.sql` — pushed directly, no PR (7f5867ff)

## Order
1. migrate  2. roll containers  3. seed  4. enable flags

## Unverified
- #44 "Ib 139" — body has no ops section and the diff touches `internal/ledger`; confirm with the author
```

Rules for this output:

- **Every item names its source** — PR number or commit SHA. An item nobody can trace back is an item nobody will trust.
- **"Not declared" is not the same as "none"** — keep the sections separate. The first says the PR authors checked; the second says the machine found it anyway.
- **An empty checklist must be stated explicitly** — "no ops steps for this release, verified against the diff". A missing section reads as "not looked at".
- Do not silently drop an item because it looks already-done. If Phase 1 warned about the anchor, say per item that it may already have shipped.

## Not this skill's job

- Cutting the tag, building, or promoting — this only produces the list
- Deciding whether the release is ready
- Editing PR bodies to backfill missing ops sections (say they're missing; let the author fix it)
