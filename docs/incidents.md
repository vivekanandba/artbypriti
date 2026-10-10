# Incident ledger

Every defect found here, how it surfaced, and **which gate now catches it**. The point is
Constitution S-V: a green suite is not a current suite, so each incident is first a question about
which check should have caught it.

An entry with "none — and here is why" is a legitimate answer. A missing entry is not.

| # | Date | What happened | How it surfaced | Gate that now catches it |
| --- | --- | --- | --- | --- |
| 1 | 2025-04-30 → 2026-08-04 | `content/about/` declared a portrait file that did not exist; Hugo silently fell back for ~15 months | Read by hand while investigating something else | `check-content.py` — declared resources must exist |
| 2 | 2025-04-30 → 2026-08-04 | Home cover named a file inside a child bundle, so the OpenGraph card silently fell back to the artist's portrait | Same investigation | `check-content.py` — branch-bundle resources validated (added only after the acceptance test showed the first version missed this exact case) |
| 3 | 2025-05-19 → 2026-08-05 | `ganeshas-blessings` declared `.jpg`; the file is `.jpeg` | **The validator, on its first run** — after two manual reads of the same file had missed it | `check-content.py` |
| 4 | 2025-04-30 → 2026-08-04 | CI set `HUGO_CACHEDIR` but persisted nothing; ~200 s of image processing repeated every deploy | Measured while profiling the build | **None — deliberately.** A test could only grep workflow YAML, asserting the shape of a fix rather than a behaviour. Made observable instead: every run logs cache hit or miss |
| 5 | 2026-08-05 | 116 MB of full-resolution masters published although no page referenced them | Grepping built HTML for non-derived image references (found 0) | `check-output.py` + `check-live.py` — a reachable master fails both |
| 6 | 2026-08-05 | The visual regression gate **did not work**: Playwright's default `threshold: 0.2` let an obvious background colour change pass 7/7 | Injected a real CSS change to test the gate rather than trusting it | `threshold: 0` + calibration documented in `tests/README.md` so it cannot be re-loosened silently |
| 7 | 2026-08-06 | `check-specs.py` flagged both existing specs for quoting a template token in prose while describing that very problem | Running it | Code spans stripped before scanning |
| 8 | 2026-08-08 | Deploy-time gates were written, verified in the working tree, then **lost before commit** by a `git reset --hard HEAD~1` inside a test of the commit-msg hook. The commit's file list showed no `hugo.yml`; I did not read it, and reported the work as shipped | Checking whether the gates had actually run in a production deploy — they had not | **Partly.** Re-committed and verified with `git show HEAD:<file>` rather than from the working tree. No automated gate catches "the author destroyed their own uncommitted work"; the habit is to verify from the commit, and `post-merge`/`pre-push` reduce the window |
| 9 | 2026-08-08 | Repeated the same class of error minutes later: `git checkout <file>` to undo a deliberate tamper-test also reverted the uncommitted splice next to it | Noticed the file was missing content immediately afterwards | Same as #8: commit before testing destructive paths |
| 10 | 2026-09-20 | The 336 MB `.wpress` WordPress backup is publicly reachable at the `legacy-archive` tag. Audited: it contains `database.sql` (2.1 MB) with **1 user account, 1 password hash, and ~1,250 unique email-shaped strings**. **No `wp-config.php`**, so no DB credentials or auth salts | Deliberate audit of the public attack surface | **Risk accepted by the owner on 2026-09-20**: rotate the WordPress admin password, leave the archive public. No gate — this is a standing accepted risk, not a defect. The blobs are reachable from `main`'s history, so removing the tag alone would not help; removal would need a history rewrite |

## How to add an entry

When a defect is fixed, add a row. If no gate can catch it, say so and say why — that is the honest
answer for configuration mistakes and for human error, and it is more useful than inventing a check
that only appears to cover it.
