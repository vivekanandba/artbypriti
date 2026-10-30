# Implementation Plan: An installable gallery

**Branch**: `feat/pwa` | **Date**: 2026-10-10 | **Spec**: [spec.md](./spec.md)

## Summary

A manifest, two genuine PNG icons and a static service worker, wired through
`head-custom.html` so the vendored theme is untouched. The worker caches what the visitor
loaded rather than a hand-written list, because Hugo fingerprints the CSS and JS.

## Approach

1. **Icons.** Re-encode the 180×180 brand image to real PNGs at 192 and 512. The existing
   `apple-touch-icon.png` is JPEG data under a `.png` name, so it cannot simply be copied
   into a manifest that declares `image/png`.
2. **Manifest** in `static/`, served at the site root, scope `/`.
3. **Worker** in `static/`: precache only the manifest and icons; runtime-cache documents,
   styles, scripts and fonts; never images; network-first so new work is never hidden.
4. **Wiring** in `layouts/partials/head-custom.html`, which the theme already includes.
5. **Gate**: `check_installable` in `scripts/check-output.py`, which already reads the
   built site, so CI covers it with no new tooling (NFR-001).

## Alternatives considered

- **A Hugo output format rendering `sw.js` as a template**, so the fingerprinted asset
  URLs could be substituted at build time. Rejected: it would have to replicate the
  theme's asset pipeline exactly to produce the same hashes, and runtime caching solves
  the same problem without that coupling.
- **Precaching the gallery.** Rejected: 566 MB.

## Risks

- A visitor who has never been online sees nothing but the start URL. Accepted: the shell
  is the promise, not the archive.
- Stale styles if a deploy changes CSS while a page is cached. Mitigated by network-first
  documents and by caching page and CSS together on the same visit.
