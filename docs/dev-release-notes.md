# Dev release notes & build banner (fork-only)

> **Lane**: `feat/dev-tools`. These files must NEVER ride an upstream extraction —
> upstream suites are extracted path-restricted from `master`, and this feature
> only concerns our Gitea/CI deployment. Files owned by this lane:
> `.gitea/scripts/release_notes.py`, the `dev_build_banner` template tag,
> `BB_BUILD_*` args in `test-docker/Dockerfile`, and this document.

## What the user sees

Every deploy to bb-dev creates a Gitea release (`bb-YYYYMMDD.N`) with three sections:

1. **🧪 What to try on bb-dev** — plain-English, written by humans in the PR body.
2. **📋 Changelog** — merged PRs with links + commit count since the previous release.
3. **🔧 Build** — image + digest, pipeline run, DB backup location.

The user menu additionally shows the dev build identity under the official version:

```
v2.x.x (abc1234)
bb-20260820.4 · 2026-08-20 17:53 UTC
```

## Authoring "What to try" (the bb-notes convention)

In the PR body, wrap the plain-English section in HTML comment markers:

```markdown
<!-- bb-notes:begin -->
- **Feeding add form** — the child should already be pre-selected (Kaelan).
  Check the Pumping dropdown lists recent sessions too.
- **Feed inventory edit** — open a feed linked to a pumping session; the linked
  session should be selected and saving must not blank it.
<!-- bb-notes:end -->
```

Guidelines:

- Write for the person opening bb-dev after the deploy: **what to open, what to
  click, what "correct" looks like** — including pages that previously errored
  and should now work.
- The markers are invisible when Gitea renders the PR (HTML comments), so the
  PR body stays clean.
- Multiple merged PRs each contribute their own `bb-notes` section.
- **No markers → no section**: the release falls back to a reminder note; the
  changelog layer always works.

## Mechanics (CI)

- `release` job checks out the pushed branch, runs
  `.gitea/scripts/release_notes.py`, and posts the output as the release body.
- The composer: newest release tag ≠ this one → `compare/<prev>...<sha>` →
  merge commits (`Merge pull request 'x' (#N)`) → fetch each PR body →
  extract `bb-notes` → compose with the changelog + build footer.
- The banner: the `build` job computes the tag, passes
  `BB_BUILD_TAG`/`BB_BUILD_TIME` as build-args → `ENV` in the image →
  `dev_build_banner` template tag → conditional line in `nav-dropdown.html`.
  Env unset (tests, upstream trees) → renders nothing.
