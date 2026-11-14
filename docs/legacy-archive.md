# Legacy archive — where the old migration files went

The `legacy/` directory was removed from the working tree. **Nothing was deleted from git
history**, so every file is still retrievable — permanently — at the tag below.

## 🔗 Open the archive

**Browse it in the browser, no clone needed:**

### 👉 https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy

| Link | What it opens |
| --- | --- |
| [Browse `legacy/`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy) | The whole directory as it was, browsable file by file |
| [The archive commit](https://github.com/vivekanandba/artbypriti/commit/8d0cf6e376da7eb0e482d328cda45b472408ef6b) | Commit `8d0cf6e` — the last state containing `legacy/` |
| [The `legacy-archive` tag](https://github.com/vivekanandba/artbypriti/releases/tag/legacy-archive) | Tag landing page, with source-download links |
| [Download everything as a zip](https://github.com/vivekanandba/artbypriti/archive/refs/tags/legacy-archive.zip) | ⚠️ ~1.5 GB — the entire repo at that commit, `legacy/` included |

**Straight to a subdirectory:**

| | |
| --- | --- |
| [`legacy/wordpress`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/wordpress) | Original WordPress site + the split `.wpress` backup |
| [`legacy/migration_1`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/migration_1) | First WordPress → Hugo attempt |
| [`legacy/migration_2`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/migration_2) | Second attempt |
| [`legacy/migration_3`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/migration_3) | Third attempt |
| [`legacy/migration_4`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/migration_4) | Fourth attempt |
| [`legacy/migration_5`](https://github.com/vivekanandba/artbypriti/tree/legacy-archive/legacy/migration_5) | Fifth attempt — the flatten-content restructure behind today's layout |

Single files can be fetched raw, e.g.
[`flatten-content.py`](https://raw.githubusercontent.com/vivekanandba/artbypriti/legacy-archive/legacy/migration_5/flatten-content.py):

```
https://raw.githubusercontent.com/vivekanandba/artbypriti/legacy-archive/legacy/<path>
```

All of the above were verified to return HTTP 200 for an anonymous visitor.

## The reference

| | |
| --- | --- |
| **Tag** | `legacy-archive` |
| **Commit** | `8d0cf6e376da7eb0e482d328cda45b472408ef6b` |
| **Subject** | Merge pull request #14 from vivekanandba/docs/update-repo-owner-readme |
| **Date** | 2026-06-07 |
| **Contents** | 1477 files, 1380 MB under `legacy/` |

The `legacy-archive` tag exists so this reference cannot rot: the commit stays reachable
regardless of what happens to branch history, and the links above are built on the tag rather
than on a branch, so they keep working.

> These links resolve because the repository is public. If it is ever made private, the URLs
> stay valid but will require being signed in with access; the `git` commands below work either
> way.

## Why it was removed

`legacy/` was 1380 MB of the repository's 1497 MB tip tree — 92% of everything CI downloaded
and wrote on *every single deploy*, for files that no build step reads. Removing it from the
tree cuts a fresh checkout to roughly 117 MB.

## What was in it

| Path | Files | Size | What it is |
| --- | --- | --- | --- |
| `legacy/wordpress` | 8 | 335 MB | The original WordPress site backup, including a `.wpress` export split across four `*_part_0*` files |
| `legacy/migration_1` | 414 | 257 MB | First WordPress → Hugo migration attempt (`wp_to_hugo.py`, exports, image tree) |
| `legacy/migration_2` | 424 | 262 MB | Second attempt (`migrate_all.sh`, original-title logs) |
| `legacy/migration_3` | 428 | 263 MB | Third attempt |
| `legacy/migration_4` | 101 | 131 MB | Fourth attempt (`migrate4.py`) |
| `legacy/migration_5` | 102 | 131 MB | Fifth attempt — the flat-content restructure (`flatten-content.py`) that produced today's layout |

The five migration snapshots are near-identical copies of the same WordPress-era image set,
which is why the total is so large relative to the ~116 MB of live artwork.

## How to get it back

Inspect without restoring anything:

```bash
git show legacy-archive --stat -- legacy/          # what changed at that commit
git ls-tree -r --name-only legacy-archive -- legacy/   # full file listing
git show legacy-archive:legacy/migration_5/flatten-content.py   # read a single file
```

Restore the whole directory into the working tree:

```bash
git restore --source=legacy-archive -- legacy/
# older git: git checkout legacy-archive -- legacy/
```

Restore just one subdirectory:

```bash
git restore --source=legacy-archive -- legacy/wordpress/
```

Reassemble the split WordPress backup after restoring it (see also
`docs/linux-file-split-and-merge-guide.md`):

```bash
cat legacy/wordpress/backup/*.wpress_part_* > artbypriti.wpress
```

**If you cloned shallowly** (CI does this by default), the archive commit won't be present
locally. Fetch it first:

```bash
git fetch --unshallow            # or: git fetch --depth=1 origin tag legacy-archive
```

Anything restored this way is deliberately untracked-by-intent — don't commit it back onto
`main`, or the checkout cost returns.

## Why the history was not rewritten (decision, 2026-11-14)

The pack is still **561 MB**, almost all of it this archive. Rewriting history would reclaim it,
and was considered and **declined**:

- `CON-PROC-010` (adopted 2026-11-07, raised from this very archive) says history is additive:
  removing something leaves a reference that still resolves, and rewriting published history costs
  every existing clone. The archive's whole design — a tag, a browsable link, restore commands —
  depends on the commits staying reachable.
- The cost that mattered is gone: the CI checkout fell from 1,497 MB to 118 MB when the archive
  left the working tree. (The security job still fetches full history, deliberately — the secret
  scan has to see every commit.)
- The one case where the rule says rewriting is *correct* is security remediation. Incident #10
  (a WordPress database dump with a password hash and ~1,250 email-shaped strings inside the
  `.wpress` file) is exactly that case — and the owner decided on 2026-09-20 to **accept the risk
  and rotate the password** rather than purge. That decision stands until the owner revisits it;
  if they do, a purge is the rule-sanctioned route, and the tag above would need re-pointing.

So: not an oversight, and not irreversible either way — recorded so the next person does not have
to rediscover the trade-off.
