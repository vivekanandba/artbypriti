# Feature Specification: Artwork Structured Data

**Feature Branch**: `023-structured-data`

**Created**: 2026-11-13

**Status**: Implemented — PR #44

## Problem

The only schema.org markup on the site sat in the list branch of `gallery.html`, which never
renders, so `params.author` was inert and nothing told a search engine who made these paintings.

## Requirements

- **FR-001**: Each of the 46 artwork pages (pages with a category) carries one JSON-LD
  `VisualArtwork` with name, url, the 1600 px image variant, `creator` from `params.author.name`,
  `artMedium` from the category (omitted for "General"), and the artist's description when present.
- **FR-002**: No `dateCreated` (front-matter dates are WordPress post dates, not creation dates)
  and no parsed `width`/`height` (dimensions are the artist's free text) — `CON-DATA-006`.
- **FR-003**: The CSP markup check treats non-JavaScript `<script>` types as data blocks, using
  HTML's exact list; typed inline JavaScript still fails.
- **FR-004**: `check_artwork_structured_data` parses every block and fails on a missing,
  duplicated, unparseable, mistyped, creator-less or master-image block, or on any `dateCreated`.

## Success Criteria

- **SC-001**: 46 pages carry valid VisualArtwork data; non-artwork pages carry none.
- **SC-002**: The gate is red with the partial removed and red with `dateCreated` planted;
  both demonstrated.
- **SC-003**: Typed inline JavaScript under `script-src 'self'` still fails; JSON-LD passes.
