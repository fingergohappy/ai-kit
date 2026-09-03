---
name: sync-main
description: Bring the latest default branch into the current feature branch, merging or rebasing to match the repo's own convention.
argument-hint: "[--rebase] [--merge]"
disable-model-invocation: true
---

# sync-main

Bring the default branch's new commits into the current feature branch, so the branch is tested and reviewed against what `main` actually looks like now.

> **Result**: the current branch contains every commit on `origin/<default>`, or the merge stopped at conflicts that only a human should resolve.

This skill has no opinion on merge vs rebase — it reads the repository's. See Phase 1.

## Phase 1 — Resolve the ground truth

Never assume the branch names.

```sh
git rev-parse --abbrev-ref HEAD                                   # current branch
git symbolic-ref --quiet refs/remotes/origin/HEAD                 # -> refs/remotes/origin/main
```

If `origin/HEAD` is not set, fall back in this order: `main`, `master`, then ask. Do not guess a third name.

Stop and report, without changing anything, if:

- **The current branch is the default branch.** There is nothing to sync into; the user wants `git pull`, and should say so.
- **The working tree is dirty** (`git status --porcelain` is non-empty). Merging on top of uncommitted work mixes their changes into the conflict resolution and there is no clean way back out. Say which files are dirty and let the user commit or stash.
- **A merge, rebase, or cherry-pick is already in progress** (`git rev-parse --verify MERGE_HEAD` / `REBASE_HEAD` / `CHERRY_PICK_HEAD` succeeds).

### Which integration style does this repo use?

Decide this before touching anything, in this order:

1. **The user said** — `--rebase` or `--merge` in `$ARGUMENTS` wins over everything below.
2. **The history says** — how has this repo synced before?
   ```sh
   git log --merges --oneline -30 | grep "Merge remote-tracking branch 'origin/<default>'"
   ```
   Hits mean this repo merges the default branch in. No hits, plus feature branches that sit linearly on top of `<default>`, means it rebases.
3. **Still ambiguous** — ask. One line, two options. Do not pick one silently: guessing rebase in a merging repo rewrites published history, and guessing merge in a rebasing repo puts a merge commit into a history someone keeps linear on purpose.

**`git config pull.rebase` does not answer this question.** It governs how `git pull` integrates the *same* branch's remote counterpart — not how the default branch comes into a feature branch. The two are routinely different: a repo can have `pull.rebase=true` and still merge `origin/main` into its feature branches, which is exactly the case in repos this skill was built against. Reading it as the answer here gets it wrong.

## Phase 2 — Fetch and compare

```sh
git fetch origin
git log --oneline HEAD..origin/<default>     # what is coming in
git log --oneline origin/<default>..HEAD     # what this branch adds
```

If the first is empty, the branch is already up to date — say so and stop. That is a successful outcome, not a failure, and it should cost nothing.

Report the incoming commit count before merging. A branch that has drifted 200 commits behind is a different situation from one behind by 3, and the user should learn that before the conflicts show up.

## Phase 3 — Integrate

Whichever style Phase 1 settled on:

```sh
git merge origin/<default>       # merging repo
git rebase origin/<default>      # rebasing repo — see the warning below
```

**On conflict, stop.** Do not resolve, do not `--abort` on the user's behalf. Report:

- the conflicted paths (`git diff --name-only --diff-filter=U`)
- for each, one line on what the two sides changed
- the two ways out: resolve and continue (`git commit`, or `git rebase --continue`), or abort (`git merge --abort` / `git rebase --abort`) to get back to where they were

Resolving someone else's merge conflict without being asked is how work silently disappears — the wrong side gets picked, and the diff looks intentional. If the user wants help resolving, that is a separate request (the `resolving-merge-conflicts` skill, where available).

## Phase 4 — Verify and report

After a clean merge, run the project's test command **if one obviously exists** (`make test`, `npm test`, `go test ./...` — detect, don't invent). A merge that succeeds textually can still break the build, and finding that out now is much cheaper than after the PR is open.

Report:

1. how many commits came in, and the range
2. which style was used and why (user asked / history shows), and whether it was a fast-forward, a real merge commit, or a rebase
3. test result, or that no test command was detected
4. that the branch has **not** been pushed — this skill does not push

## When the answer is rebase

Rebasing rewrites this branch's commits, so whether it came from `--rebase` or from Phase 1's detection:

- if the branch was already pushed, the next push needs `--force-with-lease` (never plain `--force`) — **say this in the report**, don't let the user discover it at push time
- if anyone else has the branch checked out, their history diverges silently
- the conflict may repeat per replayed commit; `git rebase --abort` is the way back

Never switch to rebase on your own because the history "looks cleaner". In a repo that merges, a rebased branch is the anomaly — and the person who set that convention is not in this conversation.
