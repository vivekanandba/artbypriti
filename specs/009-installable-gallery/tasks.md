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
