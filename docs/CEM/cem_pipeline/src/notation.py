#!/usr/bin/env python3
"""Reconstruct CEM 'Definitions of Symbols' back-matter as a two-column GFM table.

These sections are a single left-aligned list — each row starts at the page's
left margin with the symbol, followed by its definition; wrapped continuation
lines (usually the [units]) are indented. Marker reads the wraps out of order, so
we rebuild the rows directly from PDF word coordinates instead.
"""
import re
import fitz

# WP-GreekCentury / WP-GreekHelve (WordPerfect Greek fonts) embed unnamed,
# cmap-less subset glyphs, so PyMuPDF returns the raw byte code instead of the
# Greek letter. The layout is the WordPerfect Greek character set: lowercase on
# even codes from 0x22 (alpha), uppercase on the interleaved odd codes. Verified
# glyph-by-glyph by rendering every code that appears in the Part II notation
# sections. Latin variables use Times/Arial and are left untouched.
WPGREEK = {
    0x22: 'α', 0x24: 'β', 0x28: 'γ', 0x2a: 'δ', 0x2c: 'ε',
    0x2e: 'ζ', 0x30: 'η', 0x32: 'θ', 0x34: 'ι', 0x36: 'κ',
    0x38: 'λ', 0x3a: 'μ', 0x3c: 'ν', 0x3e: 'ξ', 0x40: 'ο',
    0x42: 'π', 0x44: 'ρ', 0x46: 'σ', 0x48: 'ς', 0x4a: 'τ',
    0x4c: 'υ', 0x4e: 'φ', 0x50: 'χ', 0x52: 'ψ', 0x54: 'ω',
    0x23: 'Α', 0x25: 'Β', 0x27: 'Γ', 0x29: 'Δ', 0x2b: 'Ε',
    0x2d: 'Ζ', 0x2f: 'Η', 0x31: 'Θ', 0x33: 'Ι', 0x35: 'Κ',
    0x37: 'Λ', 0x39: 'Μ', 0x3b: 'Ν', 0x3d: 'Ξ', 0x3f: 'Ο',
    0x41: 'Π', 0x43: 'Ρ', 0x45: 'Σ', 0x49: 'Τ', 0x4b: 'Υ',
    0x4d: 'Φ', 0x4f: 'Χ', 0x51: 'Ψ', 0x53: 'Ω', 0x6e: 'φ',
}


def _words(page):
    """Like page.get_text('words') but with WordPerfect-Greek-font characters
    translated to real Unicode Greek. Returns (x0,y0,x1,y1,text) tuples."""
    out = []
    for b in page.get_text("rawdict")["blocks"]:
        for ln in b.get("lines", []):
            for sp in ln["spans"]:
                greek = "Greek" in sp["font"]
                cur = None
                for c in sp.get("chars", []):
                    ch = WPGREEK.get(ord(c["c"]), c["c"]) if greek else c["c"]
                    if not ch.strip():                  # whitespace ends a word
                        if cur:
                            out.append(tuple(cur)); cur = None
                        continue
                    x0, y0, x1, y1 = c["bbox"]
                    if cur is None:
                        cur = [x0, y0, x1, y1, ch]
                    else:
                        cur[0] = min(cur[0], x0); cur[1] = min(cur[1], y0)
                        cur[2] = max(cur[2], x1); cur[3] = max(cur[3], y1)
                        cur[4] += ch
                if cur:
                    out.append(tuple(cur))
    return out


RUN_RE = re.compile(
    r'^(EM\s*1110|\(Part|Change\s+\d|[IVX]+-\d+-\d+|\d+\s*$'
    r'|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\b'
    r'|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d)', re.I)
GROUP_RE = re.compile(r'^[^\s]{1,4}\s*\([a-zA-Z]+\)\s*$')     # e.g. "κ (kappa)"


def _rows(page, ytol=4, translate=False):
    """Group a page's words into visual rows: [(x0, [words sorted by x])].
    translate=True remaps WordPerfect-Greek glyphs to Unicode (Part II)."""
    words = _words(page) if translate else [w for w in page.get_text("words")]
    words.sort(key=lambda w: (round(w[1] / ytol), w[0]))
    rows, cur, cy = [], [], None
    for w in words:
        yc = (w[1] + w[3]) / 2
        if cy is None or abs(yc - cy) <= ytol:
            cur.append(w)
            cy = yc if cy is None else (cy + yc) / 2
        else:
            rows.append(cur)
            cur, cy = [w], yc
    if cur:
        rows.append(cur)
    out = []
    for r in rows:
        r.sort(key=lambda w: w[0])
        out.append((r[0][0], r))
    return out


UNIT_RE = re.compile(r'\[(?:length|force|time|deg|dimension|radian|kg|slug|m/|N/|MN|tonne|percent)',
                     re.I)


def _is_notation_page(page):
    """A notation page is a symbol list: many short left-margin entries whose
    definitions carry a [unit] bracket — a pattern body prose does not have."""
    units = short = 0
    for x0, r in _rows(page):
        line = " ".join(w[4] for w in r)
        if UNIT_RE.search(line):
            units += 1
        if 70 <= x0 <= 98 and len(r[0][4]) <= 6 and len(r) >= 2:
            short += 1
    return units >= 5 and short >= 8


def find_pages(pdf_path):
    """Indices of the (contiguous, back-matter) notation pages, or []."""
    doc = fitz.open(pdf_path)
    flags = [(_is_notation_page(p)) for p in doc]
    doc.close()
    # take the longest run of notation pages in the last third of the document
    best = []
    i = 0
    while i < len(flags):
        if flags[i]:
            j = i
            while j < len(flags) and flags[j]:
                j += 1
            if (j - i) > len(best):
                best = list(range(i, j))
            i = j
        else:
            i += 1
    return best


def reconstruct(pdf_path, pages=None):
    """Return [(symbol, definition)] rows for the notation section."""
    doc = fitz.open(pdf_path)
    if pages is None:
        pages = find_pages(pdf_path)
    pairs = []
    for pi in pages:
        page = doc[pi]
        for x0, r in _rows(page, translate=True):
            toks = [w[4] for w in r]
            line = " ".join(toks).strip()
            if not line or RUN_RE.match(line):
                continue
            if GROUP_RE.match(line):        # "κ (kappa)" group header -> skip
                continue
            if x0 <= 98:                    # symbol row: first token = symbol
                sym = toks[0]
                rest = " ".join(toks[1:]).strip()
                pairs.append([sym, rest])
            elif pairs:                     # indented wrap -> append to last def
                pairs[-1][1] = (pairs[-1][1] + " " + line).strip()
    doc.close()
    # tidy: collapse spaces, drop empty / running-header / lone-punctuation rows
    out = []
    for s, d in pairs:
        s = s.strip()
        d = re.sub(r'\s+', ' ', d).strip()
        if not s or RUN_RE.match(s):
            continue
        if len(s) == 1 and not (s.isalnum() or ord(s) > 127):   # lone ascii punctuation
            continue
        out.append((s, d))
    return out


def to_gfm(pairs):
    if not pairs:
        return []
    esc = lambda t: t.replace('|', '\\|')
    gfm = ["| Symbol | Definition |", "|---|---|"]
    for s, d in pairs:
        gfm.append(f"| {esc(s)} | {esc(d)} |")
    return gfm


_HEAD_RE = re.compile(r'(Definitions of Symbols|\bSymbols\b)', re.I)


def fix_markdown(md_path, pdf_path):
    """Replace a chapter's flattened 'Symbols' section with a reconstructed
    two-column table. Returns the number of rows written, or 0 if not applied."""
    pages = find_pages(pdf_path)
    if not pages:
        return 0
    pairs = reconstruct(pdf_path, pages)
    if len(pairs) < 10:
        return 0
    text = open(md_path, encoding="utf-8").read().replace("\r\n", "\n")
    lines = text.split("\n")
    # last heading mentioning Symbols / Definitions of Symbols (back-matter)
    hi = level = None
    for i, ln in enumerate(lines):
        m = re.match(r'^(#{1,6})\s+(.*)$', ln)
        if m and _HEAD_RE.search(m.group(2)):
            hi, level = i, len(m.group(1))
    if hi is None:
        return 0
    # Symbols is the last real section; bound at the next REAL section heading
    # (skip running-header pseudo-headings like "## Change 3 (28 Sep 11)"), else EOF.
    end = len(lines)
    for j in range(hi + 1, len(lines)):
        mj = re.match(r'^(#{1,6})\s+(.*)$', lines[j])
        if not mj:
            continue
        if re.match(r'(Change\s+\d|EM\s*1110|\(Part)', mj.group(2), re.I):
            continue
        if len(mj.group(1)) <= level:
            end = j
            break
    new = lines[:hi + 1] + [""] + to_gfm(pairs) + [""] + lines[end:]
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(new))
    return len(pairs)


def _tokens(lines):
    """Split a sequence of rawdict lines (a whole block/paragraph) into
    whitespace-delimited tokens, so a Greek glyph wrapped across a line break
    still has Latin neighbours. Each token is a list of (raw, fixed, is_wpgreek)."""
    toks, cur = [], []
    for ln in lines:
        for sp in ln["spans"]:
            greek = "Greek" in sp["font"]
            for c in sp.get("chars", []):
                ch = c["c"]
                if ch.isspace():
                    if cur:
                        toks.append(cur); cur = []
                    continue
                g = greek and ord(ch) in WPGREEK
                cur.append((ch, WPGREEK[ord(ch)] if g else ch, g))
        if cur:                       # line break ends the current token
            toks.append(cur); cur = []
    if cur:
        toks.append(cur)
    return toks


def _anchor(toks, lo, hi):
    """Whitespace-flexible regex for tokens[lo:hi] used as context anchors. A
    Greek char in an anchor token may already be fixed in the markdown (depending
    on replacement order), so match either its raw or fixed glyph."""
    parts = []
    for t in toks[lo:hi]:
        chars = [f"[{re.escape(raw)}{re.escape(fixed)}]" if g and raw != fixed else re.escape(raw)
                 for raw, fixed, g in t]
        if chars:                       # Marker may insert spaces inside a token too
            parts.append(r"\s*".join(chars))
    return r"\s+".join(parts)


def fix_prose(md_path, pdf_path, exclude_pages=()):
    """Repair WordPerfect-Greek glyph corruption in Part II *body* text (e.g.
    'g/2 B' -> 'g/2 π', 'stream function Q' -> 'stream function Ψ'). For each
    Greek-bearing token we build a regex anchored on its Latin neighbour tokens and
    swap ONLY that token, so legitimate Latin/digits ('subscript 0', 'L_0', a real
    'D') are never touched. Returns (patterns_applied, unmatched, distinct)."""
    doc = fitz.open(pdf_path)
    # WP-Greek corruption is Part II only; skip documents that never use the font.
    if not any("Greek" in f[3] for pno in range(len(doc)) for f in doc.get_page_fonts(pno)):
        return 0, 0, 0
    exclude = set(exclude_pages)
    subs, seen = [], set()
    for pno in range(len(doc)):
        if pno in exclude:
            continue
        for b in doc[pno].get_text("rawdict")["blocks"]:
            if True:
                toks = _tokens(b.get("lines", []))
                for ti, t in enumerate(toks):
                    if not any(c[2] for c in t):
                        continue
                    # need Latin anchors on both sides; widen short anchors
                    if ti == 0 or ti == len(toks) - 1:
                        continue
                    li = ti - 2 if len(toks[ti - 1]) < 3 and ti >= 2 else ti - 1
                    ri = ti + 3 if len(toks[ti + 1]) < 3 and ti + 2 < len(toks) else ti + 2
                    left, right = _anchor(toks, li, ti), _anchor(toks, ti + 1, ri)
                    if not left or not right:
                        continue
                    body = r"\s*".join(re.escape(c[0]) for c in t)
                    fixed = "".join(c[1] for c in t)
                    regex = f"({left})(\\s+)({body})(\\s+)({right})"
                    key = (regex, fixed)
                    if key in seen:
                        continue
                    seen.add(key)
                    subs.append((regex, fixed))
    text = open(md_path, encoding="utf-8").read().replace("\r\n", "\n")
    applied = missed = 0
    for regex, fixed in subs:
        try:
            new, n = re.subn(regex,
                             lambda m, f=fixed: m.group(1) + m.group(2) + f + m.group(4) + m.group(5),
                             text)
        except re.error:
            continue
        if n:
            text = new; applied += 1
        else:
            missed += 1
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return applied, missed, len(subs)


if __name__ == "__main__":
    import sys
    ps = find_pages(sys.argv[1])
    print("notation pages:", ps)
    for s, d in reconstruct(sys.argv[1], ps)[:40]:
        print(f"  {s:10} | {d[:70]}")
