---
name: ui-test-lead
description: |
  Lead manual UI testing that a tester agent (dsh, Claude Code, codex, ... in another tmux pane, on this machine or another one over ssh) carries out in a real browser against a test environment: every brief carries the user's standing test rules (browser only and never the database, reach pages by clicking not by URL, a finish point for every item so the tester never waits on its own, don't burn shared accounts' login codes, press only authorised buttons, copy errors verbatim instead of retrying), then each report is verified against the database before the next item goes out, and every defect found is traced, checked against its ticket and put to the user on the spot. Use whenever the user says "继续测试", "派测试", "让它测一下 XX", "测下一批", "测试进度到哪了", "按上线范围测", "let the tester check X", "next test batch", "how far is testing". Delivery itself is tmux-dispatch (same machine) or a pointer pasted over ssh (another machine).
argument-hint: "[<what to test>]"
disable-model-invocation: false
---

# ui-test-lead

You lead the testing; a tester agent clicks. The tester sees only the brief and the browser. **You** own everything that needs judgement or privileges: reading the code and the tickets to state what should happen, checking the database, flipping mocks and switches, deciding whether something is a defect, and asking the user. Keeping those on your side is what keeps the tester's report honest: it records what a real customer or operator would see, nothing more.

## 0. What the project has to tell you

The rules below are generic. The specifics live in the project (its CLAUDE.md, release / test docs, your memory for it). Find them before the first brief, and write the ones the tester needs into the brief:

- the environment's URLs (customer app, admin console) and which accounts to use;
- how a tester gets login codes and 2FA codes (a read-only helper endpoint, a mailbox) — and which accounts the user also logs into by hand;
- how **you** read the database read-only (and the limits: statement timeout, no long transactions);
- how you flip mocks / switches, if the test needs them;
- where test results and environment changes are recorded (a test-scope document, a runbook log);
- the test scope: what changed since production, per ticket, so progress can be counted.

## 1. Rules that go into every brief

The tester starts from nothing and cannot see this conversation. Put this block, adapted to the project, into the first `## Task` of every new channel document. Later follow-ups need not repeat it, but a rule the user adds later goes out as its own follow-up at once.

```markdown
### Rules (apply to every task in this document)

1. **Browser only, never the database.** Act only on the pages of <customer app> and <admin console>. Do not read or change the database; do not call the helper's SQL / mock-switch / data-seeding endpoints; do not call the platform's API with scripts in place of the pages. Only exception: login codes and 2FA codes from <read-only helper endpoints>.
2. **Reach pages by clicking, not by typing a URL or following a pasted link** (the login page excepted). The click path a real customer or operator takes is what is being tested; an entry you cannot find is itself a finding. An ID in the brief is something to look for in a list, not a URL to build.
3. **Stop at the finish point; never wait on your own.** Every item states its finish point. Where it does not say to wait, record what the page shows now and move on — the back-end outcome is checked by the dispatcher. Where it says to wait, keep to the stated interval and limit, and at the limit record what you see.
4. **Login codes are shared.** <Environment> sends one login code per address every <N> seconds: no repeated resends, no login loops. <Accounts the user also uses> — log in only when needed, once, and not again while the session holds. Login failing or "too many attempts" → `BLOCKED:`.
5. **Press only authorised buttons.** Anything that moves money or changes configuration (confirm a payment, dispose of a case, archive, toggle, save settings) only when the item explicitly asks, and only that one press. The admin console is look-only unless an item grants a step. "Open the review page and leave" means do not submit.
6. **On an error, copy it; do not retry.** On a refusal, error or warning, stop at that step, copy the text verbatim (every language shown), screenshot it, report. Do not change the amount, recipient or any input and try again — the dispatcher needs the first outcome. Items that say "expected to be refused, note it and continue" are the exception. If the browser itself crashes, restart it, resume from that step, and say so in the report.
7. **Use only what the page tells you.** Every value you type (a reference, an evidence id, an order number, an account) must be something the customer or operator could know from the screens, an email they received, or a document they hold. If a step needs a value that is only in the database, or that only the brief gave you, stop and report it as a finding ("the form wants X, nothing on screen shows X") instead of typing it.
8. **Report.** For every item: what you saw / the page's text verbatim / screenshot paths (absolute, on your machine, file names carrying the item id) / what differs from the expectation ("none" if nothing). The status line starts with `DONE:`, `BLOCKED:` or `QUESTION:`. Never write passwords, login codes or 2FA codes into the report.
```

## 2. How to write each item

- An id (`N1`, `T3`, `M1`, …) and the ticket it checks.
- The account to use and where to start (which menu).
- Every value the tester has to type comes from the screens, an email the user or operator receives, or a document they hold — never from the database. If the flow needs a value only the database has (an internal reference, an evidence id), that is itself a finding: write the item so the tester has to look for it on the page, and record the gap if it is not there.
- Steps as a **click path**, never a URL; find records by a short id prefix plus what they look like (amount, currency, counterparty).
- The expectation, taken from the code and the ticket — the tester does not read code. State exact texts, filter labels, which list a record should appear in.
- **A finish point**: "done when you see X"; for back-end progress "refresh every N minutes, at most M minutes". An item without a finish point does not go out.
- An item that needs you to flip a mock or switch midway (a reversal, a provider refusal, an empty pool) goes out in two halves: the tester stops at a page, you flip, then the second half.
- An admin write step names its scope ("only this one step") and goes out only after the user agreed to it.

## 3. Delivering

- Tester on this machine: the `tmux-dispatch` skill.
- Tester on another machine: keep the channel document on **this** machine, so there is one copy. Paste a one-line pointer into the tester's pane over ssh:
  `printf '%s' "<pointer>" | ssh <host> 'tmux load-buffer -b td - && tmux paste-buffer -p -d -b td -t <pane> && sleep 1 && tmux send-keys -t <pane> Enter'`.
  The pointer says where the document is (`ssh <this-host> cat <path>`) and that the report is appended there over ssh, then announced by running this machine's `tmux-reply` script over ssh: `ssh <this-host> "bash <path>/tmux-reply/scripts/reply.sh <your pane> <doc> 'DONE: …'"`. Give the remote tester a small skill that says exactly this, so it does not have to be repeated in every pointer. Take the pane id from `ssh <host> tmux list-panes -a`, not from memory.
- Before pasting, `capture-pane` the tester once: if a menu is open ("Enter to select"), your Enter would pick an option.

## 4. When a report arrives

1. Read the report section, not just the status line.
2. **Verify against the database** (read-only): the record's state, the provider's state, checks, routing decisions, cases and refunds. The page and the database must agree before the item passes. If the back end is not final yet, poll it to the end yourself — never send the tester back to wait.
3. Record the result in the project's test record, and any environment change in its runbook log.
4. Write "verified: …" into the next follow-up, then send the next item.

## 5. When a test turns up a problem

- **Put it to the user at once**, one question at a time — do not batch problems for the end.
- Before asking: find the cause (file:line); read the ticket — if the ticket already states the behaviour, follow it and only tell the user; find who built it (ticket assignee and the commits / PRs, back end and front end separately).
- Explain with a concrete case (which customer, what they did, what they saw), and say whether it is in the **customer app or the admin console**.
- An environment problem (configuration, a switch retired by test runs, a mock left on) is not a code defect: say so, and ask before fixing the environment.

## 6. Progress

When asked how far testing is, count against the test scope (leave out what is deliberately not tested) and give a percentage per area (for example: the main new feature's channels / its functions / everything else and the admin console), plus what is half done and what has not started.
