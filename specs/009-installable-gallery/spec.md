# Feature Specification: An installable gallery whose pages open without a connection

**Feature Branch**: `feat/pwa`

**Created**: 2026-10-10

**Status**: Draft

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
- **NFR-001**: No new dependency and no build step. The worker is a static file.

## Success Criteria

1. The built site contains `manifest.webmanifest`, `sw.js`, `images/icon-192.png` and
   `images/icon-512.png`.
2. Every icon the manifest names exists in the built site, and any icon declared
   `image/png` begins with the PNG signature.
3. `index.html` links the manifest and registers the worker.
4. Offline, after a visit, the home page renders with its styles.

## Verification

- `scripts/check-output.py::check_installable` — asserts 1 to 3 against the built site on
  every CI run. Proven by mutation: declaring a JPEG as a PNG icon is reported, and a
  missing manifest is reported.
- The site was built locally with Hugo 0.147.8 and the output inspected: the manifest is
  linked, `theme-color` is present, and the worker registers `/sw.js`.

## Not verified here

Criterion 4 — an actual offline load in a browser. The check asserts the worker ships and
is registered, not that a phone with aeroplane mode on renders the page.

The 512×512 icon is **upscaled from the 180×180 brand image**, the largest that exists in
the repository. It is the real mark rather than an invented one, but it is soft at that
size; replacing it with artwork exported at 512 is a one-file change.

## Out of scope

Offline browsing of artwork, push notifications, an app-store package.
