"""Shared fixtures for the gate-script unit tests.

Two awkwardnesses these helpers hide:

1. The scripts are hyphen-named (`check-content.py`), so they cannot be imported normally.
   `load()` pulls each one in by path.
2. They keep module-level `errors` / `warnings` / `notes` lists. A module cached between
   tests would leak findings from one test into the next and quietly turn real failures
   green, so every `load()` returns a *fresh* module object.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"


def load(name):
    """Import a hyphen-named script as a fresh module object."""
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_gate_{name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    # Not every script keeps all three lists; clear whichever it has.
    for bucket in ("errors", "warnings", "notes"):
        getattr(module, bucket, []).clear()
    return module


@pytest.fixture
def content(tmp_path):
    """Build a content/ tree. Returns a helper that writes one artwork bundle."""
    root = tmp_path / "content"
    root.mkdir()

    def artwork(slug, *, title="A Painting", date="2021-02-21", categories="[Oil on Canvas]",
                description="A description.", dimensions="(50 cm X 40 cm)",
                resource="painting.jpg", image="painting.jpg", extra=""):
        d = root / slug
        d.mkdir(parents=True, exist_ok=True)
        fm = ["---", f'title: "{title}"']
        if date: fm.append(f"date: {date}")
        if categories: fm.append(f"categories: {categories}")
        fm.append(f"description: {description}" if description else "description:")
        if dimensions: fm.append(f"dimensions: {dimensions}")
        if resource: fm += ["resources:", f"  - src: {resource}"]
        if extra: fm.append(extra)
        fm += ["---", ""]
        (d / "index.md").write_text("\n".join(fm), encoding="utf-8")
        if image:
            (d / image).write_bytes(jpeg_bytes(800, 600))
        return d

    artwork.root = root
    return artwork


def jpeg_bytes(width, height):
    """A byte string with a valid JPEG SOF0 header of the given size.

    `check-output.py` reads dimensions from the header rather than depending on Pillow, so
    the tests must exercise that reader on real header bytes — not on a mock that would
    prove nothing about the parser.
    """
    sof = (b"\xff\xc0" + (8 + 3 * 3).to_bytes(2, "big") + b"\x08"
           + height.to_bytes(2, "big") + width.to_bytes(2, "big") + b"\x03"
           + b"\x01\x11\x00\x02\x11\x01\x03\x11\x01")
    return b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + sof + b"\xff\xd9"


def png_bytes(width, height):
    import struct, zlib
    ihdr = struct.pack(">II", width, height) + b"\x08\x02\x00\x00\x00"
    chunk = b"IHDR" + ihdr
    return (b"\x89PNG\r\n\x1a\n" + struct.pack(">I", len(ihdr)) + chunk
            + struct.pack(">I", zlib.crc32(chunk)))
