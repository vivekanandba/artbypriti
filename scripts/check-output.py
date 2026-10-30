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


def master_widths(content_dir):
    """Widest master per artwork slug, used to decide what a page could have shown.

    Reads the stored width. Hugo applies AutoOrient before sizing, so for an EXIF-rotated
    master the stored width is not the displayed one -- no master carries a rotation today,
    and the callers below report "cannot determine" rather than guessing if one ever does
    (CON-VER-005: a check that misdiagnoses is worse than no check).
    """
    masters = {}
    for dp, _, fns in os.walk(content_dir):
        for fn in fns:
            if fn.lower().endswith(IMAGE_EXTS):
                size = image_size(os.path.join(dp, fn))
                if size:
                    masters[os.path.basename(dp)] = max(masters.get(os.path.basename(dp), 0), size[0])
    return masters


# The artwork page's column, from .gallery-single-img { width: 100%; max-width: 1000px }.
ARTWORK_COLUMN = 1000


def check_artwork_fills_its_column(built, content_dir="content"):
    """Fail when an artwork page shows a painting smaller than the page affords.

    This is the INVERSE of check_no_upscaling, and deliberately a separate check. The artwork
    figure shrink-wraps (flex column, align-items:center), so its image renders at
    min(natural, 1000) and the browser can never stretch it -- pointing the upscaling check
    here would be the wrong assertion wearing the right name. The failure mode on this page is
    under-filling: `images.Process "fit 1000x1000"` constrains the LONGEST edge, so a portrait
    painting came out 577-792px wide in a 1000px column (24 of 47 images, spec 011).

    Nothing caught that for months. Visual regression compares each page against its own
    equally-under-filled baseline, and the other output assertions check that an image exists,
    not that it is as large as the page affords. The same blindness shipped the grid soft for
    15 months (spec 006), which is why this is a gate and not a note.
    """
    masters = master_widths(content_dir)
    short, too_small, unknown, checked = [], [], [], 0

    for dp, _, fns in os.walk(built):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            page = os.path.join(dp, fn)
            html = open(page, encoding="utf-8", errors="replace").read()
            for tag in re.findall(r"<img\b[^>]*>", html):
                if "gallery-single-img" not in tag:
                    continue
                m = re.search(r'data-src=["\']?([^"\'> ]+)', tag)
                if not m:
                    continue
                served = image_size(os.path.join(built, m.group(1).lstrip("/")))
                if not served:
                    continue
                checked += 1
                if served[0] >= ARTWORK_COLUMN:
                    continue
                slug = m.group(1).lstrip("/").split("/")[0]
                master = masters.get(slug, 0)
                where = (
                    f"{os.path.relpath(page, built)} -> {served[0]}px served into a "
                    f"{ARTWORK_COLUMN}px column (master {master}px)"
                )
                if served[0] > master:
                    # The variant is wider than the master we measured, so the measurement is
                    # wrong -- most likely an EXIF-rotated master. Say so; do not pick a side.
                    unknown.append(where)
                elif master < ARTWORK_COLUMN:
                    # Constitution III: only the artist can supply resolution never photographed.
                    too_small.append(where)
                else:
                    short.append(where)

    for s in short:
        errors.append(
            f"artwork under-fills its column: {s} — size it by width, not longest edge"
        )
    if too_small:
        warnings.append(
            f"{len(too_small)} artwork(s) below the {ARTWORK_COLUMN}px column because the master "
            f"is smaller, which is the artist's call, not a defect: " + "; ".join(too_small[:3])
        )
    if unknown:
        warnings.append(
            f"{len(unknown)} artwork(s) could not be checked: the served variant is wider than "
            f"the master as measured, so the master's orientation is not what was assumed: "
            + "; ".join(unknown[:3])
        )
    notes.append(f"{checked} artwork image(s) checked against the {ARTWORK_COLUMN}px column")


def check_no_upscaling(built, content_dir="content"):
    """Fail when an image is displayed wider than it is served, and the master could have covered it."""
    masters = master_widths(content_dir)

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


def check_csp_matches_the_markup(built):
    """A strict script-src and an inline <script> cannot both be right.

    The site declares `script-src 'self'`, which blocks inline execution. When the PWA work
    added an inline service-worker registration, the two met and the worker silently stopped
    registering -- silently, because registration swallows its own errors by design. Nothing
    failed; the feature was simply gone.

    So the two are checked against each other here rather than trusted to stay compatible.
    """
    offenders, pages, policed = [], 0, 0
    for dp, _, fns in os.walk(built):
        for fn in fns:
            if not fn.endswith(".html"):
                continue
            html = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
            if not html.strip():
                continue
            pages += 1
            # Hugo minifies attribute quotes away, so match both spellings.
            strict = ("script-src 'self'" in html) or ("script-src &#39;self&#39;" in html)
            if not strict:
                continue
            policed += 1
            # An inline block is <script> with no src= before the closing bracket.
            for tag in re.findall(r"<script\b[^>]*>", html):
                if "src=" not in tag:
                    offenders.append(os.path.relpath(os.path.join(dp, fn), built))
                    break

    if offenders:
        errors.append(
            f"{len(offenders)} page(s) carry an inline <script> while declaring "
            f"script-src 'self' -- the browser will refuse to run it, and a registration that "
            f"catches its own errors fails silently. Move it to assets/js/ and load it with a "
            f"src. First: {offenders[0]}"
        )
    elif policed:
        notes.append(f"{policed} page(s) declare script-src 'self' and carry no inline <script>")


def check_expected_files(built):
    for rel in ("index.html", "about/index.html", "request/index.html", "sitemap.xml", "robots.txt"):
        if not os.path.exists(os.path.join(built, rel)):
            errors.append(f"expected output missing: {rel}")


def check_installable(built):
    """The site is installable and its icons are what they claim to be (spec 009).

    The manifest, the worker and both icons must exist in the built output, every
    icon the manifest names must be present, and a PNG icon must really be a PNG:
    the repo's apple-touch-icon.png and favicon.png are JPEG data with a .png
    name, which browsers sniff past but a manifest declaring image/png does not.
    """
    import json

    manifest_rel = "manifest.webmanifest"
    manifest_path = os.path.join(built, manifest_rel)
    if not os.path.exists(manifest_path):
        errors.append(f"expected output missing: {manifest_rel}")
        return
    if not os.path.exists(os.path.join(built, "sw.js")):
        errors.append("expected output missing: sw.js")

    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    sizes = {icon.get("sizes") for icon in manifest.get("icons", [])}
    for required in ("192x192", "512x512"):
        if required not in sizes:
            errors.append(f"manifest declares no {required} icon; a phone will not install it")
    for icon in manifest.get("icons", []):
        rel = icon["src"].lstrip("/")
        path = os.path.join(built, rel)
        if not os.path.exists(path):
            errors.append(f"manifest names {icon['src']}, which is not in the built site")
            continue
        if icon.get("type") == "image/png":
            with open(path, "rb") as fh:
                if fh.read(8) != b"\x89PNG\r\n\x1a\n":
                    errors.append(f"{icon['src']} is declared image/png but is not a PNG")

    index = os.path.join(built, "index.html")
    if os.path.exists(index):
        with open(index, encoding="utf-8") as fh:
            html = fh.read()
        if "rel=manifest" not in html.replace('rel="manifest"', "rel=manifest"):
            errors.append("index.html does not link the manifest")
        # Follow the registration rather than grepping for a word. This assertion first
        # looked for "serviceWorker" in the HTML, which held only while the registration was
        # inline; moving it to an external file for the CSP (spec 010) would have failed it
        # even though the worker registers correctly. Checking the chain -- tag, script,
        # worker file -- is both accurate and stronger than the string it replaces.
        m = re.search(r'<script[^>]*\bsrc=["\']?([^"\'> ]+)[^>]*\bdata-sw-url=["\']?([^"\'> ]+)', html)
        if m:
            script_rel, sw_rel = m.group(1).lstrip("/"), m.group(2).lstrip("/")
            script_path = os.path.join(built, script_rel)
            if not os.path.exists(script_path):
                errors.append(f"index.html loads {m.group(1)} to register the worker, but it is not in the build")
            elif "serviceWorker.register" not in open(script_path, encoding="utf-8", errors="replace").read():
                errors.append(f"{m.group(1)} is wired up as the registration but never calls serviceWorker.register")
            if not os.path.exists(os.path.join(built, sw_rel)):
                errors.append(f"the registration points at {m.group(2)}, which is not in the built site")
        elif "serviceWorker" not in html:
            errors.append("index.html does not register the service worker")


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
    check_artwork_fills_its_column(built, content)
    check_csp_matches_the_markup(built)
    check_expected_files(built)
    check_installable(built)
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
