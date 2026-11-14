# Tasks: Artwork Structured Data

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Branch**: `023-structured-data`

- [x] **T001** Confirmed what the site already records: `params.author.name = "Priti Ghatlia"`
  (marked inert in `hugo.toml` until "a small template change"), and that the 46 artworks are
  exactly the pages with a category.
- [x] **T002** Decided what not to state: `dateCreated`, parsed dimensions, and a medium for
  "General".
- [x] **T003** `artwork-jsonld.html`, included from `head-custom.html`. 46 pages carry it; the
  `olive` block parses and points at the same 1600 px variant as the lightbox.
- [x] **T004** The CSP markup check flagged all 46 blocks as inline scripts. Fixed by exempting
  data blocks using HTML's exact JavaScript-type list, not "anything with a type"; typed inline
  JavaScript still fails.
- [x] **T005** `check_artwork_structured_data` parses every block. Red with the partial removed
  (46 pages, "0 JSON-LD blocks") and red with `dateCreated` planted; green restored.
- [x] **T006** 20 unit tests in `tests/unit/test_structured_data.py`; the existing "clean site"
  fixture gained a block, since a clean artwork page now needs one.
- [x] **T007** Browser CSP suite run on the build: no violation from the JSON-LD.
- [ ] **T008** After deploy: confirm the live artwork pages carry the block.
