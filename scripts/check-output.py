#!/usr/bin/env python3
"""Assert on the BUILT SITE, not on the build's exit code.

Constitution Principle I: a green build is not evidence of correctness. Hugo answers a
missing resource with a silent fallback, so every defect this repository has actually
shipped was invisible to `hugo`'s exit code. These assertions read `public/` and fail
loudly on output that is wrong despite a successful build.

Companion to check-content.py, which validates inputs. This validates results.

Usage:  python3 scripts/check-output.py [built_dir] [--content content_dir]
Exit:   0 = clean (warnings allowed), 1 = errors found
"""

import os
import re
import sys
from urllib.parse import urlparse, unquote

# Principle IV: the deployed site stays under 40MB. It is ~28MB today.
MAX_PAYLOAD_MB = 40
IMAGE_EXTS = (".jpg", ".jpeg", ".png")
# Hugo names every processed variant with an "_hu_<hash>" infix. Anything without it is
# an original copied verbatim.
DERIVED_MARKER = "_hu_"
NON_ARTWORK = {"about"}

errors = []
warnings = []
notes = []


def artworks_from_content(content_dir):
    """Map slug -> whether front matter promises a dimensions caption."""
    out = {}
    if not os.path.isdir(content_dir):
        return out
    for name in sorted(os.listdir(content_dir)):
        index = os.path.join(content_dir, name, "index.md")
        if not os.path.isfile(index) or name in NON_ARTWORK:
            continue
        fm = open(index, encoding="utf-8").read().split("\n---", 1)[0]
        m = re.search(r"^dimensions:[ \t]*(.*)$", fm, re.MULTILINE)
        out[name] = bool(m and m.group(1).strip())
    return out


def check_no_masters(built):
    """No full-resolution original may be published (Principle IV).

    Scoped to page-bundle output directories — those containing an index.html — because
    that is where Hugo copies bundle resources. Files under static/ (favicons, the touch
    icon) are legitimately copied verbatim and must not be flagged.
    """
    masters = [
        os.path.relpath(os.path.join(dp, fn), built)
        for dp, _, fns in os.walk(built)
        for fn in fns
        if fn.lower().endswith(IMAGE_EXTS)
        and DERIVED_MARKER not in fn
        and "index.html" in fns
    ]
    if masters:
        total = sum(os.path.getsize(os.path.join(built, m)) for m in masters) / 1048576
        errors.append(
            f"{len(masters)} full-resolution master(s) published ({total:.1f} MB) — "
            f"publishResources should prevent this. First: {masters[0]}"
        )
    else:
        notes.append("no full-resolution masters published")


def check_payload(built):
    total = sum(
        os.path.getsize(os.path.join(dp, fn))
        for dp, _, fns in os.walk(built)
        for fn in fns
    ) / 1048576
    if total > MAX_PAYLOAD_MB:
        errors.append(f"payload {total:.1f} MB exceeds the {MAX_PAYLOAD_MB} MB budget")
    else:
        notes.append(f"payload {total:.1f} MB (budget {MAX_PAYLOAD_MB} MB)")


def check_artwork_pages(built, artworks):
    """Every artwork must render a page, with an image, and with its caption."""
    missing_caption = []
    for slug, promises_dimensions in artworks.items():
        page = os.path.join(built, slug, "index.html")
        if not os.path.isfile(page):
            errors.append(f"artwork '{slug}' has no built page at {slug}/index.html")
            continue
        html = open(page, encoding="utf-8", errors="replace").read()

        if not re.search(r'<img[^>]+(?:data-src|src)=', html):
            errors.append(f"artwork page '{slug}' renders no image")

        has_caption = 'class=dimensions' in html or 'class="dimensions"' in html
        if promises_dimensions and not has_caption:
            errors.append(
                f"artwork page '{slug}' has dimensions in front matter but renders no caption"
            )
        elif not promises_dimensions:
            missing_caption.append(slug)

    if missing_caption:
        # Principle III: artist-authored content warns, never blocks.
        warnings.append(
            f"{len(missing_caption)} artwork(s) render no size caption because front matter "
            f"has no dimensions: {', '.join(sorted(missing_caption))}"
        )
    notes.append(f"{len(artworks)} artwork pages checked")


def image_size(path):
    """Intrinsic pixel size of a JPEG/PNG, using the stdlib only.

    check-output.py must run on a bare CI runner (NFR-004: no new dependency), so this reads
    the header rather than importing Pillow. Returns (width, height) or None.
    """
    try:
        with open(path, "rb") as fh:
            head = fh.read(24)
            if len(head) < 24:
                return None
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                return (int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big"))
            if head[:2] != b"\xff\xd8":
                return None
            fh.seek(2)
            while True:
                b = fh.read(1)
                while b and b != b"\xff":
                    b = fh.read(1)
                while b == b"\xff":
                    b = fh.read(1)
                if not b:
                    return None
                marker = b[0]
                if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
                    continue
                seg = fh.read(2)
                if len(seg) < 2:
                    return None
                length = int.from_bytes(seg, "big")
                # SOF0-SOF15, excluding the non-frame markers DHT/JPG/DAC
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                    data = fh.read(5)
                    if len(data) < 5:
                        return None
                    return (int.from_bytes(data[3:5], "big"), int.from_bytes(data[1:3], "big"))
                fh.seek(length - 2, 1)
    except OSError:
        return None


# The CSS width each surface displays an image at. An image narrower than its slot is stretched
# by the browser: 47 paintings shipped that way for months because every gate compared a page
# against its own equally-soft baseline (specs/006-image-resolution).
# Only the grid has a FIXED slot: its figure sets width:100% inside a 600px card, so a
# narrow image really is stretched. The artwork page's figure shrink-wraps (flex column,
# align-items:center), so its image renders at natural width and can never be upscaled --
# measured, after an earlier version of this check wrongly assumed a 1000px slot there.
DISPLAY_SLOTS = (("class=lazyload", 600, "grid card"),)


def check_no_upscaling(built, content_dir="content"):
    """Fail when an image is displayed wider than it is served, and the master could have covered it."""
    masters = {}
    for dp, _, fns in os.walk(content_dir):
        for fn in fns:
            if fn.lower().endswith(IMAGE_EXTS):
                size = image_size(os.path.join(dp, fn))
                if size:
                    masters[os.path.basename(dp)] = max(masters.get(os.path.basename(dp), 0), size[0])

    stretched, too_small, checked = [], [], 0
    for dp, _, fns in os.walk(built):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            page = os.path.join(dp, fn)
            html = open(page, encoding="utf-8", errors="replace").read()
            for tag in re.findall(r"<img\b[^>]*>", html):
                m = re.search(r'data-src=["\']?([^"\'> ]+)', tag)
                if not m:
                    continue
                if "gallery-single-img" in tag:
                    continue  # no fixed slot; see DISPLAY_SLOTS
                slot = next((w for token, w, _ in DISPLAY_SLOTS if token in tag), None)
                if slot is None:
                    continue
                served = image_size(os.path.join(built, m.group(1).lstrip("/")))
                if not served:
                    continue
                checked += 1
                if served[0] >= slot:
                    continue
                slug = m.group(1).lstrip("/").split("/")[0]
                where = f"{os.path.relpath(page, built)} -> {served[0]}px served into a {slot}px slot"
                # Constitution III: if the master itself is too small, only the artist can fix that.
                (too_small if masters.get(slug, 0) < slot else stretched).append(where)

    for s in stretched:
        errors.append(f"image is upscaled by the browser: {s} — size it by width, not longest edge")
    if too_small:
        warnings.append(
            f"{len(too_small)} image(s) served below their display size because the master is smaller: "
            + "; ".join(too_small[:3])
        )
    notes.append(f"{checked} displayed images checked against their slot width")


def check_expected_files(built):
    for rel in ("index.html", "about/index.html", "request/index.html", "sitemap.xml", "robots.txt"):
        if not os.path.exists(os.path.join(built, rel)):
            errors.append(f"expected output missing: {rel}")


def check_internal_links(built):
    """Every internal href/src must resolve to something in the built site."""
    checked = 0
    broken = {}
    for dp, _, fns in os.walk(built):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            page = os.path.join(dp, fn)
            html = open(page, encoding="utf-8", errors="replace").read()
            for m in re.finditer(r'(?:href|src|data-src)=["\']?([^"\'> ]+)', html):
                url = m.group(1)
                if url.startswith(("http://", "https://", "mailto:", "#", "data:", "//")):
                    continue
                checked += 1
                target = os.path.join(built, unquote(urlparse(url).path).lstrip("/"))
                if not (os.path.exists(target) or os.path.exists(os.path.join(target, "index.html"))):
                    broken.setdefault(url, os.path.relpath(page, built))
    for url, src in list(broken.items())[:10]:
        errors.append(f"broken internal link: {src} -> {url}")
    if len(broken) > 10:
        errors.append(f"...and {len(broken) - 10} more broken link(s)")
    notes.append(f"{checked} internal references resolved")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    built = args[0] if args else "public"
    content = "content"
    if "--content" in sys.argv:
        content = sys.argv[sys.argv.index("--content") + 1]

    if not os.path.isdir(built):
        print(f"error: no built site at {built!r} — run a build first", file=sys.stderr)
        return 1

    artworks = artworks_from_content(content)
    if not artworks:
        print(f"error: no artwork bundles found under {content!r}", file=sys.stderr)
        return 1

    check_no_masters(built)
    check_payload(built)
    check_artwork_pages(built, artworks)
    check_no_upscaling(built, content)
    check_expected_files(built)
    check_internal_links(built)

    for n in notes:
        print(f"ok:      {n}")
    for w in warnings:
        print(f"warning: {w}")
    for e in errors:
        print(f"ERROR:   {e}")

    print(f"\nchecked built site {built!r}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
