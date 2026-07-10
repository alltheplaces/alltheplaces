# AllThePlaces Session Prompt

You are working in /Users/iandees/SynologyDrive/Projects/AllThePlaces/alltheplaces (the alltheplaces repo).

Read `.claude/REVIEW_RULES.md` carefully before starting — it contains all conventions, preferred patterns, and decisions made in prior sessions.

Run `git pull --ff-only` first.

**All changes must go through a pull request — no exceptions.** Never commit directly to `master`, even for a trivial one-line fix. Always:
1. Create a branch (`git checkout -b fix/description`)
2. Commit your change there
3. Push and open a PR (`gh pr create`)
4. Merge via `gh pr merge N --squash`

If you accidentally commit to local `master` before pushing, immediately run `git reset HEAD~1` to unstage it, then re-apply on a branch. Once pushed to remote `master` the change cannot be undone (force-push is blocked).

## Open PRs — three-phase triage

**Phase 1:** Run the `pr-triage` agent for a cheap first-pass classification of all open PRs. Have it flag any PR that will need an `update-branch` rebase to merge — a rebase resets required checks to pending, so those PRs should be batched separately from clean, already-green ones rather than mixed into the same wave.

**Phase 2:** Act on the JSON output:
- **merge_now** — `gh pr merge N --squash --delete-branch` directly (no agent needed), UNLESS you also want a real code review (not just CI-status triage) — in that case route through `pr-handler` like `investigate` below, capped the same way.
- **investigate** — dispatch `pr-handler` agents, **capped at ~5-8 concurrent, never more**. Before dispatching a batch anywhere near that size, check headroom with `gh api rate_limit --jq .resources` — 26 concurrent agents each calling `gh` fully exhausted the GraphQL quota (5000/hr) in one run and every `gh` call from then on failed for the rest of the hour. Dispatch in waves; wait for a wave to clear before starting the next.
  - **Always pass `isolation: "worktree"`** to every `pr-handler` dispatch. `pr-handler` runs `git checkout`/branch/rebase operations; without worktree isolation, concurrent agents share the main checkout's working directory and can silently delete untracked files in it (this is how `REVIEW_RULES.md` and this file were lost during an earlier unisolated 26-agent batch).
  - `pr-handler` must check CI **once** and never poll/wait/sleep inline for a pending check — if a required check is `pending`/`queued`, it should stop immediately and report `BLOCKED_ON_CI` with the PR number, not spin up its own wait-and-merge loop.
- **investigate_dead_spiders** — hand the full list to ONE `dead-spider-triage` agent (it works through them sequentially); don't spawn one agent per removal PR
- **hold** — report each to the user with the reason from the triage table
- **skip** — ignore

**Phase 3:** After all `pr-handler` agents in a wave return, collect every `BLOCKED_ON_CI` result into one list and do a single centralized, backed-off sweep — `gh pr checks N` for each PR in turn, spaced out, not parallelized — merging any that have gone green. Do this here in the orchestrator, not via more agents or multiple independent `ScheduleWakeup` loops (each one re-hits the same shared rate limit independently). If rate-limited during the sweep, read the reset time from `gh api rate_limit --jq .resources` and wait for it rather than guessing a delay.

**`mergeable: "UNKNOWN"` is not a conflict — never treat it as one.** During any batch-merge session (Phase 2's direct `merge_now` merges, or `pr-handler`'s own merge step), merging one PR briefly makes every *other* open PR show `mergeable: UNKNOWN` while GitHub recomputes mergeability. This is transient, not a real conflict — the repo does not require branches to be up-to-date (`required_status_checks.strict = false`), so a merely-stale branch is never a blocker. If a direct `gh pr merge` fails, check `gh pr view N --json mergeable,mergeStateStatus`: on `UNKNOWN`, wait a few seconds and retry the merge; only run `gh pr update-branch N` when `mergeable` has actually resolved to `CONFLICTING`. Confirmed 2026-07-10: a 34-PR merge burst caused 9 non-conflicting PRs (touching entirely separate files) to get needlessly `update-branch`'d, resetting their CI to pending for no reason.

Any `SUPERSEDED` result (the same fix already landed via a different merged PR) should be surfaced to the user for a merge/close decision — never closed unilaterally by an agent.

Common CI failure causes (for Phase 2 pr-handler agents):
- **pre-commit naming failure**: check expected class name with `python3 -c "import sys; sys.path.insert(0,'ci'); import check_spider_naming_consistency as c; print(c.snake_to_camel('spider_name') + 'Spider')"`
- **CodeBuild timeout only** (pytest + pre-commit pass): acceptable — merge
- **Real CodeBuild failure** (0 results, crash, 404): investigate before merging

## Issue triage — use background agents, 5 at a time max

Work through open issues oldest-first:
```
gh issue list --state open --json number,title --limit 200 --search "is:issue" | \
  python3 -c "import json,sys; [print(i['number'], i['title']) for i in sorted(json.load(sys.stdin), key=lambda x: x['number']) if x['number'] >= 13100]"
```

Delegate **one issue per background agent** — this keeps each agent token-efficient and focused.
Use the prompt template below, substituting a single issue number.

---
**Agent prompt template:**

  In /Users/iandees/SynologyDrive/Projects/AllThePlaces/alltheplaces, triage GitHub issue
  #NNNN. Read `.claude/REVIEW_RULES.md` first.

  For this issue:
  1. **Spider already exists** → close:
     ```
     gh api repos/alltheplaces/alltheplaces/issues/NNN/comments -f body='Spider already exists as `name`. 🤖'
     gh api -X PATCH repos/alltheplaces/alltheplaces/issues/NNN -f state=closed
     ```
  2. **Site/domain dead** (DNS fail, connection refused, consistent 4xx) → close with explanation + 🤖
  3. **Data quality bug in existing spider** → check latest CI output at
     https://alltheplaces-data.openaddresses.io/runs/latest/output/<spider>.geojson
     If still broken: fix the spider, open a PR with `Closes #N`. If already fixed: close citing the fix.
  4. **Valid new spider request, site accessible** → BUILD IT using a git worktree (see below), open a PR with `Closes #N`
  5. **Infrastructure/meta** → leave open

  **Worktree pattern** (required for every code change — never commit to master directly):
  ```bash
  git fetch origin
  git worktree add /tmp/wt-BRANCH -b BRANCH origin/master
  cd /tmp/wt-BRANCH
  # write/fix spider, test: scrapy crawl NAME --set CLOSESPIDER_ITEMCOUNT=10
  # commit ONLY the spider file(s)
  git push -u origin BRANCH
  gh pr create --head BRANCH --title "..." --body "...\n\nCloses #NNN"
  cd /Users/iandees/SynologyDrive/Projects/AllThePlaces/alltheplaces
  git worktree remove /tmp/wt-BRANCH
  ```

  **Class name check** (run before committing to catch naming hook failures early):
  ```
  python3 -c "import sys; sys.path.insert(0,'ci'); import check_spider_naming_consistency as c; print(c.snake_to_camel('spider_name') + 'Spider')"
  ```

  Post 🤖 at the start of all comments. No "Investigated:" prefix, no manual timestamps.
  Do NOT manually close issues that have an open PR with `Closes #N` — GitHub closes them automatically on merge.

---

Launch up to 5 agents in parallel, one issue each. Wait for them to complete before launching the next batch.
When an agent reports back with `gh` commands it couldn't run, execute them directly here.
If an agent has been running >10 minutes, check its worktree for partial work and extract it manually.
