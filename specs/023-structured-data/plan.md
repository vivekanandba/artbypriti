# Implementation Plan: Artwork Structured Data

**Spec**: [spec.md](./spec.md) · **Branch**: `023-structured-data` · **Created**: 2026-11-13

## Approach

- `layouts/partials/artwork-jsonld.html` builds a `dict` and emits it with `jsonify`, which
  escapes `<`, `>` and `&`, so no title can close the script element.
- `head-custom.html` includes it on pages that have a category — exactly the 46 artworks.
  About and Request have none.
- The image is the same 1600 px variant the lightbox serves (same processing call, so the same
  cached file), never a master.

## What is left out, and why

| Field | Why not |
| --- | --- |
| `dateCreated` | Front-matter dates arrived from the WordPress migration as post dates. Publishing one as a creation date turns an unknown into a false fact (`CON-DATA-006`). The output check fails if one appears. |
| `width` / `height` | Dimensions are the artist's free text; two are in inches pending her answer. Parsing is inference. |
| `artMedium` for "General" | "General" is a category on this site but not a medium. |

## The CSP interaction

A JSON-LD block is a `<script>` with no `src`, so the existing markup check called it inline
code. Per the HTML standard a script with a non-JavaScript type is a **data block** that is never
executed, so `script-src` does not govern it. The check now uses that exact list; `type=text/javascript`
inline code still fails, which is tested.

## Verification

Build output parsed on every run; red with the partial removed and red with `dateCreated`
planted; the browser CSP suite visits an artwork page and must see no violation.
