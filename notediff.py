#!/usr/bin/env python3
"""Notation diff: render two versions of the score with the changed bars in red.

    python3 notediff.py [OLD [NEW]]

OLD and NEW are git revisions (default: HEAD against the working tree).
Bars are compared through ly2musicxml, both parts and lyrics together; inserted
or removed bars are aligned rather than shifting everything after them.
Writes old.pdf and new.pdf to a temporary directory, plus overlay-N.png per
page: both versions superimposed, black where they agree, red for ink only in
the old version and green for ink only in the new.
"""

import difflib
import os
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zlib

sys.dont_write_bytecode = True
import ly2musicxml

SRC = "teasdale-carol.ly"

HIGHLIGHT = r"""
#(define (diff-highlight bars)
   (lambda (context)
     (make-engraver
       (acknowledgers
         ((grob-interface engraver grob source)
           (if (memv (ly:context-property context 'currentBarNumber) bars)
               (ly:grob-set-property! grob 'color red)))))))
"""


def source(rev):
    if rev is None:
        with open(SRC) as f:
            return f.read()
    return subprocess.run(["git", "show", f"{rev}:{SRC}"], check=True,
                          capture_output=True, text=True).stdout


def bars(ly, tmp, name):
    """One entry per bar: (number, comparable text of that bar in every part)."""
    src, dst = os.path.join(tmp, name + ".ly"), os.path.join(tmp, name + ".xml")
    with open(src, "w") as f:
        f.write(ly)
    ly2musicxml.main(src, dst)
    parts = []
    for part in ET.parse(dst).getroot().iter("part"):
        ms = []
        for m in part.iter("measure"):
            n = m.get("number")
            m.attrib.pop("number")
            ms.append((int(n), ET.tostring(m, encoding="unicode")))
        parts.append(ms)
    return [(ms[0][0], tuple(m[1] for m in ms)) for ms in zip(*parts)]


def changed(old, new):
    oc, nc = set(), set()
    sm = difflib.SequenceMatcher(None, [b[1] for b in old], [b[1] for b in new],
                                 autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            oc.update(b[0] for b in old[i1:i2])
            nc.update(b[0] for b in new[j1:j2])
    return sorted(oc), sorted(nc)


def render(ly, marked, tmp, name):
    ly = ly.replace("\\score {", HIGHLIGHT + "\n\\score {", 1)
    ly = re.sub(r"\\layout\s*\{",
                lambda m: m.group(0) + "\n    \\context { \\Score \\consists "
                f"#(diff-highlight '({' '.join(map(str, marked))})) }}", ly, count=1)
    path = os.path.join(tmp, name)
    with open(path + ".ly", "w") as f:
        f.write(ly)
    subprocess.run(["lilypond", "-s", "-o", path, path + ".ly"], check=True)
    return path + ".pdf"


def pages(pdf, tmp, name):
    """Greyscale pages of a PDF as (width, height, bytes), via Ghostscript."""
    out = os.path.join(tmp, name + "-%d.pgm")
    subprocess.run(["gs", "-q", "-dNOPAUSE", "-dBATCH", "-dSAFER", "-sDEVICE=pgmraw",
                    "-r110", "-dTextAlphaBits=4", "-dGraphicsAlphaBits=4",
                    "-o", out, pdf], check=True)
    result, n = [], 1
    while os.path.exists(out % n):
        with open(out % n, "rb") as f:
            data = f.read()
        m = re.match(rb"P5\s+(?:#[^\n]*\n\s*)*(\d+)\s+(\d+)\s+\d+\s", data)
        result.append((int(m[1]), int(m[2]), data[m.end():]))
        n += 1
    return result


def write_png(path, w, h, rgb):
    rows = b"".join(b"\0" + rgb[y * w * 3:(y + 1) * w * 3] for y in range(h))
    def chunk(kind, body):
        return (len(body).to_bytes(4, "big") + kind + body
                + zlib.crc32(kind + body).to_bytes(4, "big"))
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", w.to_bytes(4, "big") + h.to_bytes(4, "big") + bytes([8, 2, 0, 0, 0]))
                + chunk(b"IDAT", zlib.compress(rows, 6)) + chunk(b"IEND", b""))


def align(w, h, o, n, reach=15, step=40):
    """Shift the rows of the new page vertically to best match the old page, so
    music nudged up or down by a change elsewhere doesn't come out entirely red
    and green. The shift may vary down the page; changing it by one row costs
    as much as `step` mismatched pixels, so it only changes where that pays."""
    ink = bytes(1 if v < 128 else 0 for v in range(256))
    bits = lambda img: [int.from_bytes(img[y * w:(y + 1) * w].translate(ink), "big")
                        for y in range(h)]
    bo, bn = bits(o), bits(n)
    shifts = range(-reach, reach + 1)
    total, back = [0] * len(shifts), []
    for r in range(h):
        here = [(bn[r] ^ (bo[r + s] if 0 <= r + s < h else 0)).bit_count() for s in shifts]
        best = [min(range(len(shifts)), key=lambda j: total[j] + step * abs(i - j))
                for i in range(len(shifts))]
        total = [total[j] + step * abs(i - j) + here[i] for i, j in enumerate(best)]
        back.append(best)
    i = min(range(len(shifts)), key=lambda i: (total[i], abs(shifts[i])))
    out = bytearray(b"\xff" * (w * h))
    for r in reversed(range(h)):
        s = shifts[i]
        if 0 <= r + s < h:
            out[(r + s) * w:(r + s + 1) * w] = n[r * w:(r + 1) * w]
        i = back[r][i]
    return bytes(out)


def overlay(old_pdf, new_pdf, tmp):
    """Old ink alone comes out red, new ink alone green, shared ink black."""
    paths = []
    for i, ((w, h, o), (w2, h2, n)) in enumerate(zip(pages(old_pdf, tmp, "o"),
                                                       pages(new_pdf, tmp, "n")), 1):
        n = align(w, h, o, n)
        # ink counts as shared if the other version has ink within one row:
        # a staff line half a pixel lower is the same line
        near = lambda img: bytes(map(min, img, b"\xff" * w + img[:-w], img[w:] + b"\xff" * w))
        rgb = bytearray(w * h * 3)
        for k, (a, b, na, nb) in enumerate(zip(o, n, near(o), near(n))):
            red = nb - a                  # old ink with no new ink nearby
            green = na - b                # new ink with no old ink nearby
            red = red if red > 100 else 0     # smaller differences are anti-aliasing
            green = green if green > 100 else 0
            black = max(0, 255 - min(a, b) - max(red, green))
            rgb[3 * k] = max(0, 255 - black - green)
            rgb[3 * k + 1] = max(0, 255 - black - red - green * 2 // 5)
            rgb[3 * k + 2] = max(0, 255 - black - red - green)
        paths.append(os.path.join(tmp, f"overlay-{i}.png"))
        write_png(paths[-1], w, h, bytes(rgb))
    return paths


def main(old_rev="HEAD", new_rev=None):
    tmp = tempfile.mkdtemp(prefix="notediff-")
    old_ly, new_ly = source(old_rev), source(new_rev)
    oc, nc = changed(bars(old_ly, tmp, "old-xml"), bars(new_ly, tmp, "new-xml"))
    print(f"changed bars in {old_rev}: {oc or 'none'}")
    print(f"changed bars in {new_rev or 'working tree'}: {nc or 'none'}")
    print(render(old_ly, oc, tmp, "old"))
    print(render(new_ly, nc, tmp, "new"))
    for path in overlay(render(old_ly, [], tmp, "old-plain"),
                        render(new_ly, [], tmp, "new-plain"), tmp):
        print(path)


if __name__ == "__main__":
    main(*sys.argv[1:3])
