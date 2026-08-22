# Fork Development Workflow

> How this fork develops features, assembles them into a running dev
> image, and ships clean PRs to upstream `babybuddy/babybuddy`.
> Written 2026-08-19. Update **in the same PR** as any change to the
> branch architecture described here.

## Why this fork exists

Two deliverables, which pull in opposite directions:

1. **A running app with everything assembled.** Features only work and
   can only be tested when they run *together* — in one tree, on one
   database, behind one Docker image (`babybuddy-test`). That tree is
   `dev`, and it is deliberately messy: every feature's iterations,
   interleaved, plus merge commits.
2. **Clean PRs to upstream.** A maintainer wants *their* latest code
   plus your one feature — a handful of files, clean commits, nothing
   else. They never want to see our integration history.

The core trick that lets both coexist: **a repo is two things — the
files (what the app is) and the history (the story of how it got
there).** Day-to-day work needs the right *files*. An upstream PR is
judged on its *history*. This workflow keeps one messy-history place
for building, and manufactures clean-history branches on demand for
shipping. The two never mix.

## Branch map

| Branch | Role | History |
|---|---|---|
| `master` | Mirror of upstream `babybuddy/babybuddy` — read-only, never committed to | Clean (upstream's own) |
| `feat/dev-integration` | `master` + ONE snapshot commit carrying `dev`'s tree — the clean-room base new suites are born from | Clean by construction |
| `feat/<suite>` | One feature **suite** per branch (e.g. `milk-inventory`, `formula-inventory`); all iterations of the suite commit here | 1 snapshot + suite commits |
| `dev` | Integration branch — suite tips PR'd in; CI builds/deploys the test image from it | Messy, intentionally |
| `feat/dev-tools` | Fork-only tooling/CI/docs that will never go upstream | Small, clean |

**`dev = master + all feat/* merged in canonical order + feat/dev-integration`.**

`feat/dev-integration` exists because a suite must *run* (so it needs
all of `dev`'s files) but must stay *attributable* (so its diff vs its
base is exactly its own work). Branch from `dev` and you inherit 250+
commits of everyone's interleaved work; branch from `master` and the
suite won't boot. The snapshot gives you dev's exact tree with one
commit of history.

### Regenerating the snapshot

When `dev` advances and new suite work begins: fresh worktree from
`master` → `git read-tree -u --reset dev` → single commit → gate
(`git diff <new-integration> dev` must be empty) → force-push-with-lease.
Nothing is consumed; the old snapshot is simply superseded.

### Re-anchoring a suite after its batch lands

Once a suite's batch is fully merged into `dev`, point its branch at
the fresh integration snapshot for the next iteration — the snapshot
already carries the suite's content (it copies dev's tree), so tip =
integration tip, zero suite-only commits. Same branch, fresh anchor;
the landed history lives on inside `dev`. (`feat/milk-inventory`
followed this pattern 2026-08-18.)

## Day-to-day procedure

1. **Start a suite**: verify integration freshness
   (`git diff feat/dev-integration gitea/dev --stat` → empty; if not,
   regenerate first), then branch from `feat/dev-integration` — or from
   a dependency suite's tip if the suite truly depends on it. Never
   branch from `dev` or `master`.
2. **Iterate**: all work commits to the suite branch. One suite = one
   branch; no per-iteration branch chains.
3. **Land a batch**: push the suite branch, open a Gitea PR into `dev`,
   wait for `CI / migrate` + `CI / test` green, merge **on Gitea**
   (`dev` is branch-protected; direct pushes are rejected), then tag
   `bb-YYYYMMDD.N`. The pipeline migrates → tests → builds the registry
   image → recreates `babybuddy-test` on the host runner → smoke-tests.
4. **If the PR shows `mergeable: false`** (common for suite branches —
   old merge-base vs `master` makes git see the whole fork delta as
   conflict): merge `gitea/dev` into the suite branch, resolve toward
   the suite tree, gate (`git diff --cached HEAD` must be 0), push.
   Gitea recomputes mergeability; CI re-runs on the new head.

## Shipping upstream (extraction)

Suite branches are **never** PR'd upstream as branches. Upstream PRs
are manufactured at ship time:

1. Fresh branch from upstream `master`.
2. Path-restricted apply of the suite's **final file state** (new files
   whole; shared files hunk-by-hunk — only the suite's hunks).
3. Clean commit(s); run the full test suite on that branch *before*
   opening the PR — if the suite secretly depends on something missing,
   it fails locally with a stack trace, and a maintainer never sees it.
4. Open the PR.

Attribution comes from an extraction worksheet (attribute via merge
structure + `git log master..dev -- <file>`; exclude content already
submitted upstream). When a suite depends on another suite (formula
imports milk's models), either **stack** the extraction PR on the
dependency's open PR branch (auto-rebases when the base merges), wait
for the dependency to land, or — last resort, kept small — let a minor
delta ride along.

## History & provenance (why it looks like this)

- **Pre-2026-08-18 — born-clean-at-start.** Every feature kept a clean
  `master`-based branch from day one, merged into `dev` for image
  assembly. This shipped the ~6 upstream PRs currently open (diaper
  0039, continuations 0041, spit-up 0045, …). It worked — its failure
  mode was *maintenance*: dual bookkeeping (clean branch + dev
  participation) across months of iteration produced 3+ wrong-base
  branch pollutions and the 8-branch/248-commit milk chain (preserved
  as `archive/milk-chain/*`).
- **Since 2026-08-18 — clean-at-ship.** The same clean artifact is now
  minted once, at extraction, when the final state is known, instead of
  maintained continuously. `rerere` remains in active use for dev↔suite
  syncs. The extraction machinery has shipped zero upstream PRs so far
  — treat the model as provisional and revisit once the backlog lands.
  If the machinery costs more than the pollution it prevents, returning
  to born-clean-at-start is a legitimate, well-understood option.

## Known quirks

- `mergeable: false` on internal suite PRs is a *history* artifact
  (head/base/merge-base trio), not a content problem — see procedure
  step 4. Upstream extraction branches never hit it: they're born from
  `master` with zero fork history.
- Local lefthook lint fails on clean `dev` (38 files of black-version
  drift, 2026-08-19). CI runs no black. Sanctioned bypass for
  mechanical merges: `LEFTHOOK=0`, gated on tree-equality.
- `feat/dev-tools` carries fork-only CI/workflow changes; keep
  `.gitea/workflows/ci.yml` identical between `dev` and `feat/dev-tools`.
