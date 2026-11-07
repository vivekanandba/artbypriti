# Tasks: An installable gallery

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md)

- [x] T1 — Re-encode the brand image to genuine PNG at 192 and 512 (`static/images/`).
- [x] T2 — `static/manifest.webmanifest`, scope `/`, both icons declared.
- [x] T3 — `static/sw.js`: precache manifest and icons; runtime-cache documents, styles,
      scripts, fonts; skip images; network-first; versioned cache cleaned on activate.
- [x] T4 — Link the manifest, declare `theme-color` and register the worker in
      `layouts/partials/head-custom.html`.
- [x] T5 — `check_installable` in `scripts/check-output.py`, wired into `main()`.
- [x] T6 — Verify by mutation: a JPEG declared as a PNG icon is reported; a missing
      manifest is reported.
- [ ] T7 — Replace the 512 icon with artwork exported at that size, rather than upscaled.
- [x] T8 — 2026-11-07: stamp the worker's cache name from the build (`assets/sw.js` as a
      template; `HUGO_BUILD_COMMIT` in CI); `check_installable` refuses an unstamped worker.
- [x] T9 — 2026-11-07: a maskable 512×512 icon inside the 80% safe zone; `check_installable`
      requires it and checks every PNG icon's real size against its declared size.
- [x] T10 — 2026-11-07: `tests/visual/pwa.spec.js` proves registration, the stamped cache and
      an offline load in a browser; the screenshot specs now block service workers.
