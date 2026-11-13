# Feature Specification: An installable gallery whose pages open without a connection

**Feature Branch**: `feat/pwa`

**Created**: 2026-10-10

**Status**: Implemented — PR #27

**Input**: "I would like to have PWA version of all the apps where it is possible."

## Problem

The gallery cannot be installed. There is no manifest, so a phone offers no "add to home
screen", and a visitor who wants the gallery a tap away gets a browser bookmark instead.
Pages also come from the network every time: on a weak connection the site is blank.

Two details make this different from the apps in the fleet:

1. **Hugo fingerprints the CSS and JS** (`/css/main.min.<hash>.css`). A hand-written
   precache list would name files that stop existing at the next deploy, and a static
   service worker has no build step to substitute the hashes into it.
2. **The gallery is 566 MB of artwork.** Caching images to make an offline visit prettier
   would fill a visitor's phone.

There is also a smaller defect: `static/images/apple-touch-icon.png` and `favicon.png` are
**JPEG data with a `.png` name**. Browsers sniff the content and cope. A manifest that
declares `image/png` for such a file is making a claim that is not true.

## Requirements

- **FR-001**: A manifest at `/manifest.webmanifest` declaring `name`, `short_name`,
  `display: standalone`, `start_url` and `scope` of `/`, and PNG icons at 192×192 and
  512×512 that are genuinely PNG.
- **FR-002**: Every page links the manifest and declares `theme-color`, via
  `layouts/partials/head-custom.html` — never by editing `themes/gallery/`, which is
  vendored.
- **FR-003**: A service worker registered on load, whose failure is swallowed.
- **FR-004**: The worker caches **what the visitor loaded** — documents, styles, scripts,
  fonts — and not images. Because a page and the exact hashed CSS it references are cached
  on the same visit, they can never be a version apart; this is what the apps need a build
  step to achieve.
- **FR-005**: Documents are network-first. A cached page must never be shown when the real
  one is reachable, or a new painting would be invisible to a returning visitor.
- **FR-006** *(amended 2026-11-07)*: The worker's cache name is **stamped by the build** —
  the commit in CI (`HUGO_BUILD_COMMIT`), the UTC build time otherwise — and `activate`
  deletes every other cache. It shipped as the hand-bumped `artbypriti-v1`, which nobody
  bumped, so no old cache was ever deleted (fleet retrospective; FLEET.md, PWA standard).
- **FR-007** *(amended 2026-11-07)*: The manifest declares a **maskable 512×512 PNG** with
  the artwork inside the central 80% safe zone, so Android does not crop the mark.
- **NFR-001** *(amended 2026-11-07)*: No new dependency. The worker is a Hugo template
  (`assets/sw.js`) rendered at the site root on every build, not a static file — the stamp
  is what a static file could not provide.

## Success Criteria

1. The built site contains `manifest.webmanifest`, `sw.js`, `images/icon-192.png` and
   `images/icon-512.png`.
2. Every icon the manifest names exists in the built site, and any icon declared
   `image/png` begins with the PNG signature.
3. `index.html` links the manifest and registers the worker.
4. Offline, after a visit, the home page renders with its styles.
5. The built worker's cache name carries the build stamp, and a browser sees exactly one
   stamped `artbypriti-*` cache after activation.
6. The manifest names a maskable 512×512 icon, and every PNG icon's real pixels match its
   declared size.

## Verification

- `scripts/check-output.py::check_installable` — asserts 1 to 3 against the built site on
  every CI run. Proven by mutation: declaring a JPEG as a PNG icon is reported, and a
  missing manifest is reported.
- The site was built locally with Hugo 0.147.8 and the output inspected: the manifest is
  linked, `theme-color` is present, and the worker registers `/sw.js`.
- `check_installable` also asserts 5 and 6 on the built output (2026-11-07). Red first: the
  built main site failed it on `artbypriti-v1` and the missing maskable icon.
- `tests/visual/pwa.spec.js` asserts 4 and 5 in a real browser, in the pinned Playwright
  container: the worker registers at `/` scope, one stamped cache exists, and the home page
  loads with the network off. Red against main's build (`artbypriti-v1`); a mutant worker
  that cannot answer offline fails it. The screenshot specs block service workers.

## Not verified here

Criterion 4 was unverified until 2026-11-07; it is now covered by `pwa.spec.js` in desktop
Chromium. A real phone in aeroplane mode remains unverified.

The 512×512 icon is **upscaled from the 180×180 brand image**, the largest that exists in
the repository. It is the real mark rather than an invented one, but it is soft at that
size; replacing it with artwork exported at 512 is a one-file change.

## Out of scope

Offline browsing of artwork, push notifications, an app-store package.
