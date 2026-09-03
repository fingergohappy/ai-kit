---
name: ship-pr
description: Bring the default branch in, push, open a PR, then optionally watch CI and merge it when green. Detects the repo's own merge/rebase and PR-merge conventions rather than assuming.
argument-hint: "[--draft] [--no-merge]"
disable-model-invocation: true
---

# ship-pr

Take the current feature branch from "work is done" to "PR is open", and — if the user says so — keep watching until CI decides, merging on green and coming back to them on red.

> **Result**: a PR open against the default branch, and either merged, or stopped at a named failing check.

## Phase 1 — Sync

Do everything the `sync-main` skill does: resolve the real branch names, refuse on a dirty tree or an in-progress merge, **work out whether this repo merges or rebases** (its Phase 1 — don't assume either), fetch, integrate `origin/<default>`, stop on conflict.

**A conflict ends this skill.** Don't push a branch mid-conflict and don't open a PR "to see what CI says" — report the conflict and stop, exactly as `sync-main` would.

If the branch was already up to date, that's fine, carry on to Phase 2 — there is still something to ship.

If Phase 1 landed on rebase and the branch was previously pushed, the Phase 2 push needs `--force-with-lease`. Know that before you get there.

## Phase 2 — Push

```sh
git push -u origin HEAD          # first push of this branch
git push                         # subsequent
```

If the push is rejected as non-fast-forward, someone else moved the branch. **Stop.** Do not `--force`. Report what diverged and let the user decide.

If Phase 1 rebased, the push needs `--force-with-lease`, never plain `--force` — and only when the rebase is the reason the remote diverged. A non-fast-forward rejection on a branch you did **not** rebase means someone else pushed; that is the case above, and force would destroy their work.

## Phase 3 — Open the PR

First check whether one already exists for this branch:

```sh
gh pr view --json number,url,state,isDraft 2>/dev/null
```

If it exists and is open, **reuse it** — the push in Phase 2 already updated it. Say so instead of trying to create a duplicate.

Otherwise create it:

```sh
gh pr create --base <default> --head <branch> --title "<title>" --body "<body>"
```

- **Title**: derived from the commits this branch adds (`git log --oneline origin/<default>..HEAD`). One commit → its subject. Several → what they add together, written in whatever style the recent history uses — read `git log --oneline -20` and match it (conventional prefixes, gitmoji, bare sentences: each repo differs, don't impose one).
- **Body**: if `.github/pull_request_template.md` exists, **fill that template out** — don't ignore it and don't paste it back empty. Otherwise: what changed and why, then the commit list. Either way, add the ops section below.
- **Language**: match the existing PRs (`gh pr list --limit 10 --json title,body`). Don't switch the repo to another language.
- `--draft` if the user passed it.

### The ops section is not optional

A PR body that only describes code leaves whoever deploys it to find out at deploy time that it needs a variable nobody set. **Work these out from the diff** — don't ask the user to recall them, and never write "none" without having looked.

```sh
git diff origin/<default>...HEAD --stat
git diff origin/<default>...HEAD --diff-filter=A --name-only    # added files: migrations and seeds land here
```

At minimum, check for each of these:

| What | How to find it | What the PR must say |
|---|---|---|
| **New env var / config key** | new reads in the diff (`os.Getenv`, `process.env.`, `getenv`, `ENV[`), new lines in `.env.example` / `.env.sample` / chart values | name, whether it has a default, what breaks if unset, suggested production value |
| **Migration** | added files under the project's migration directory | file/version, what it does, whether it locks, whether `down` is safe |
| **Seed / backfill SQL** | added `.sql` containing `INSERT`/`UPDATE`, new scripts under `scripts/`, `db/seeds/` | when to run it (after migrate? before cutover?), whether it is idempotent, what a second run does |
| **New dependency or external service** | `go.mod` / `package.json` / `requirements.txt` / `Cargo.toml` diffs; new API hosts, queues, cron entries, buckets | what must be provisioned, which credentials, which network access |
| **Feature flag** | new flag and its default | on or off at deploy, who flips it, how to roll back |
| **Order between the above** | more than one of the rows above | the explicit sequence |

Write it as a checklist, so the person deploying can tick items off:

```markdown
## Ops

- [ ] **Env** `PAYMENT_TIMEOUT_MS` — no default; the service fails to start without it. Production: 3000
- [ ] **Migration** `000075_add_refund_idx.up.sql` — creates an index CONCURRENTLY, no table lock
- [ ] **Seed** `scripts/seed_refund_reasons.sql` — idempotent; run after the migration, before the flag is on
- [ ] **Order**: migrate → roll containers → seed → enable `refund_v2`
```

If the diff genuinely needs no ops work, say **"Ops: none"** explicitly. A missing section reads as "nobody thought about it"; an explicit "none" reads as "checked, nothing needed".

If the project keeps a deployment checklist for this change elsewhere (an sdd implementation spec has one in its release section), take the items from there rather than re-deriving them — but still put them in the PR body, because the reviewer and the deployer read the PR, not that file.

Report the PR URL as soon as it exists. That is the deliverable; everything after this point is optional.

## Phase 4 — Ask before touching the merge

Ask the user, in one line: **auto-accept this PR?** Explain what it means in the same breath — wait for CI, merge on green, come back on red.

Do not proceed to Phase 5 without an explicit yes. If the user says no (or passed `--no-merge`), stop here: the PR is open, the URL is reported, done.

## Phase 5 — Watch CI

Look once before waiting:

```sh
gh pr checks <number>
```

Three cases:

- **No checks configured** — nothing to wait for. Tell the user there is no CI on this PR and ask whether to merge anyway. Don't silently treat "no checks" as "green".
- **All finished** — go straight to Phase 6.
- **Still running** — wait, but not in the foreground:

```sh
gh pr checks <number> --watch --fail-fast     # run this in the background
```

CI runs routinely take longer than a foreground command may last. Start the watch in the background and let its completion wake you; do not sit in a `sleep`/poll loop burning turns, and do not shorten the wait by declaring a result the checks haven't reached.

While waiting, report that you are waiting and roughly what for (`3 checks running: ci / build / lint`).

## Phase 6 — Green merges, red asks

**Green** (`gh pr checks` exits 0 / every required check passed) — merge it the way this repo merges PRs. That is a different question from Phase 1's, and it has its own answer:

```sh
gh api repos/{owner}/{repo} --jq '{merge:.allow_merge_commit, squash:.allow_squash_merge, rebase:.allow_rebase_merge}'
```

1. **Only one allowed** — use it. The others are switched off on purpose.
2. **Several allowed** — read the history: `Merge pull request #NN from …` commits mean merge commits; a linear `<default>` where each PR landed as exactly one commit means squash.
3. **Still ambiguous** — ask. Squashing a repo that keeps merge commits throws away authorship granularity that nobody can get back.

```sh
gh pr merge <number> --merge|--squash|--rebase --delete-branch
git checkout <default> && git pull
```

If the merge is refused — branch protection, required review, out-of-date base — report the exact refusal and stop. That refusal is a rule someone set on purpose; it is not an obstacle to route around.

**Red**: stop and bring it back to the user with enough to act on:

- which check failed, and its URL
- the failing step's output — the actual error lines, not "the build failed" (`gh run view <run-id> --log-failed`, trimmed to what matters)
- whether it looks related to this branch's changes or pre-existing on `<default>`
- the PR is left open and unmerged

Then ask what they want: fix and re-push, merge anyway, or leave it.

Never merge a red PR without being told to in that exact situation, and never re-run CI hoping for a different answer without saying that's what you're doing.

## Report

1. sync result — merged or rebased (and how that was decided), commits integrated, or already up to date
2. PR — URL, created or reused
3. CI — checks run and their verdicts, or that the user declined the watch
4. merge — merged and back on `<default>`, or why not
