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


_NAV_HEAD = re.compile(r'^#{1,6}\s+(Table of Contents|List of Figures|List of Tables)\s*\.?\s*$', re.I)
_PSEUDO_HEAD = re.compile(r'(EM\s*1110|Change\s+\d|\(Part)', re.I)


def _split_nav(kind, raw):
    """Split a run-on Table-of-Contents / List-of-Figures / List-of-Tables body
    into one entry per item."""
    raw = re.sub(r'\s+', ' ', raw).strip()
    if 'figures' in kind:
        parts = re.split(r'(?=\bFigure\s+[IVXLC]+-\d+-\d+)', raw)
    elif 'tables' in kind:
        parts = re.split(r'(?=\bTable\s+[IVXLC]+-\d+-\d+)', raw)
    else:                                   # Table of Contents (Roman "VI-6-1." or arabic "2-1.")
        raw = re.sub(r'^(?:Paragraph\s+)?Page\s+', '', raw)
        parts = re.split(r'(?=(?<![A-Za-z0-9-])(?:[IVXLC]+-\d+-\d+|\d+-\d+)\.)', raw)
    return [p.strip() for p in parts if p.strip()]


def fix_nav(md_path):
    """Rebuild the run-on front-matter navigation sections (Table of Contents,
    List of Figures, List of Tables) as readable one-per-line lists. Content that
    a page-break/running-header split across a pseudo-heading is merged back.
    Returns the number of sections rebuilt."""
    text = open(md_path, encoding='utf-8').read().replace('\r\n', '\n')
    lines = text.split('\n')
    out, i, fixed = [], 0, 0
    while i < len(lines):
        m = _NAV_HEAD.match(lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        kind = m.group(1).lower()
        j, body, listed = i + 1, [], False
        while j < len(lines):
            hm = re.match(r'^#{1,6}\s+(.*)$', lines[j])
            if hm:
                if _PSEUDO_HEAD.search(hm.group(1)):   # running header -> drop, keep going
                    j += 1; continue
                break                                   # real heading -> section ends
            if lines[j].lstrip().startswith('- '):
                listed = True
            if lines[j].strip():
                body.append(lines[j].strip())
            j += 1
        items = [] if listed else _split_nav(kind, ' '.join(body))  # idempotent: skip if already a list
        out.append(lines[i])
        if listed:
            out += lines[i + 1:j]
        elif len(items) >= 2:
            out += [''] + ['- ' + e for e in items] + ['']
            fixed += 1
        else:
            out += lines[i + 1:j]            # could not split -> leave unchanged
        i = j
    with open(md_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(out))
    return fixed


_FUNCS = ("log", "ln", "sin", "cos", "tan", "exp", "sinh", "cosh", "tanh", "max", "min")


def _esc_tex(s):
    return s.replace("\\", "").replace("%", "\\%").replace("&", "\\&").replace("#", "\\#")


def _recon_carrier(t):
    """t: [(char, role)] for one PDF token (role in n/sub/sup). Return inline LaTeX
    (no $ delimiters), restoring sub/superscripts; a superscript lone o/0 is a
    degree sign."""
    out, i, n = [], 0, len(t)
    while i < n:
        ch, r = t[i]
        if r in ("sub", "sup"):
            j = i
            while j < n and t[j][1] == r:
                j += 1
            run = _esc_tex("".join(c for c, _ in t[i:j]))
            if r == "sup" and run.lower() in ("o", "0"):
                out.append("^{\\circ}")
            else:
                out.append(("_" if r == "sub" else "^") + "{" + run + "}")
            i = j
        else:
            out.append(_esc_tex(ch)); i += 1
    expr = "".join(out)
    for fn in _FUNCS:                        # function name before sub/sup -> operator
        expr = re.sub(r"(?<![A-Za-z\\])" + fn + r"(?=[_^])", "\\\\" + fn, expr)
    return expr


def _token_roles(chars, base, base_cy):
    """Split chars (each {c,size,bbox}) into space-delimited tokens of (char,role)."""
    toks, cur = [], []
    for c in chars:
        if c["c"].isspace():
            if cur:
                toks.append(cur); cur = []
            continue
        sz = round(c["size"]); cy = (c["bbox"][1] + c["bbox"][3]) / 2
        if sz <= base * 0.82 and cy > base_cy + 0.4:
            cur.append((c["c"], "sub"))
        elif sz <= base * 0.82 and cy < base_cy - 0.4:
            cur.append((c["c"], "sup"))
        else:
            cur.append((c["c"], "n"))
    if cur:
        toks.append(cur)
    return toks


def fix_subscripts(md_path, pdf_path):
    """Restore sub/superscripts the converter flattened (H0->H_0, 10-3->10^{-3},
    log10->\\log_{10}, 15o->15 degrees). For every PDF token that mixes a normal base
    with smaller, baseline-shifted glyphs, wrap a rebuilt inline-math version and
    swap ONLY that token into the markdown (anchored on its neighbour tokens), so
    surrounding prose is never turned into math. Returns count applied."""
    import collections
    doc = fitz.open(pdf_path)
    subs, seen = [], set()
    for pno in range(len(doc)):
        for b in doc[pno].get_text("rawdict")["blocks"]:
            for ln in b.get("lines", []):
                chars = [{"c": c["c"], "size": sp["size"], "bbox": c["bbox"]}
                         for sp in ln["spans"] for c in sp.get("chars", [])]
                nonsp = [c for c in chars if not c["c"].isspace()]
                if len(nonsp) < 2:
                    continue
                szc = collections.Counter(round(c["size"]) for c in nonsp)
                base = max(szc, key=lambda s: (szc[s], s))
                if base < 6 or not any(round(c["size"]) <= base * 0.82 for c in nonsp):
                    continue
                cys = sorted((c["bbox"][1] + c["bbox"][3]) / 2 for c in nonsp
                             if round(c["size"]) >= base * 0.92)
                if not cys:
                    continue
                toks = _token_roles(chars, base, cys[len(cys) // 2])
                for ti, t in enumerate(toks):
                    roles = [r for _, r in t]
                    if not any(r in ("sub", "sup") for r in roles):
                        continue
                    if roles[0] != "n":   # must start with a base glyph (no leading _/^)
                        continue
                    if any(0xE000 <= ord(c) <= 0xF8FF for c, _ in t):   # Symbol-font PUA -> KaTeX can't render
                        continue
                    body = r"\s*".join(re.escape(c) for c, _ in t)
                    repl = "$" + _recon_carrier(t) + "$"
                    left = re.escape("".join(c for c, _ in toks[ti - 1])) if ti > 0 else ""
                    right = re.escape("".join(c for c, _ in toks[ti + 1])) if ti + 1 < len(toks) else ""
                    # need an anchor; one strong side is enough for a distinctive body
                    if left and right:
                        rgx = f"({left})(\\s+)({body})(\\s+)({right})"
                        rep = (lambda m, R=repl: m.group(1) + m.group(2) + R + m.group(4) + m.group(5))
                    elif (left or right) and len(t) >= 4:
                        if left:
                            rgx = f"({left})(\\s+)({body})(?![\\w])"
                            rep = (lambda m, R=repl: m.group(1) + m.group(2) + R)
                        else:
                            rgx = f"(?<![\\w])({body})(\\s+)({right})"
                            rep = (lambda m, R=repl: R + m.group(2) + m.group(3))
                    else:
                        continue
                    key = (rgx, repl)
                    if key in seen:
                        continue
                    seen.add(key)
                    subs.append((rgx, rep))
    text = open(md_path, encoding="utf-8").read().replace("\r\n", "\n")
    applied = 0
    for rgx, rep in subs:
        try:
            text, n = re.subn(rgx, rep, text, count=1)
        except re.error:
            continue
        applied += 1 if n else 0
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return applied


_DEF_RE = re.compile(r"^[\\A-Za-z][\w^{}\\*'()|.-]{0,17}\s*=\s+\S")


def fix_deflists(md_path):
    """A "where:" block is a run of consecutive 'symbol = definition' lines that
    Markdown collapses into one run-on paragraph. Turn each such run (>=2 lines)
    into a bullet list so every definition renders on its own line. Returns the
    number of runs converted."""
    lines = open(md_path, encoding="utf-8").read().replace("\r\n", "\n").split("\n")
    out, i, n, fence = [], 0, 0, False
    while i < len(lines):
        if lines[i].lstrip().startswith("```"):
            fence = not fence
            out.append(lines[i]); i += 1; continue
        if not fence and _DEF_RE.match(lines[i]) and not lines[i].startswith(("-", "#", "|", ">")):
            j = i
            while (j < len(lines) and _DEF_RE.match(lines[j])
                   and not lines[j].startswith(("-", "#", "|", ">", "```"))):
                j += 1
            if j - i >= 2:
                out += ["- " + lines[k].strip() for k in range(i, j)]
                n += 1; i = j; continue
        out.append(lines[i]); i += 1
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out))
    return n


_DEGREE_RE = re.compile(r'(\d)\s*[oº°]\s*([CF])\b')


def fix_degree(text):
    """Superscript 'o' transcribed as the letter o before C/F is a degree sign."""
    return _DEGREE_RE.sub('\\1°\\2', text)


# Currency dollar amounts in prose ($6 billion, $1,000, $2.97 Fixed plant) collide
# with the inline-math $...$ delimiter; escape them to literal \$ . Each pattern is
# shaped so it never matches a math run (which is $<letter/\\> or $<digits>^/_ ...).
_CURRENCY = [
    re.compile(r'(?<!\\)\$(\s?\d[\d,]*(?:\.\d+)?\s*(?:million|billion|trillion|thousand)\b)', re.I),
    re.compile(r'(?<!\\)\$(\s?\d{1,3}(?:,\d{3})+(?:\.\d+)?)'),
    re.compile(r'(?<!\\)\$(\s?\d+\.\d{2}\s+[A-Z][a-z])'),
]


def fix_currency(text):
    for rx in _CURRENCY:
        text = rx.sub(r'\\$\1', text)
    return text


# Adobe/Monotype Symbol font characters left in the Unicode Private Use Area
# (U+F000 + symbol-byte) by the converter; render as boxes. Decode via the standard
# Symbol encoding (verified glyph-by-glyph): A-Z/a-z -> Greek, digits/punctuation as
# themselves, plus the math symbols that occur.
def _build_symbol():
    lc = [0x3b1, 0x3b2, 0x3c7, 0x3b4, 0x3b5, 0x3c6, 0x3b3, 0x3b7, 0x3b9, 0x3d5, 0x3ba,
          0x3bb, 0x3bc, 0x3bd, 0x3bf, 0x3c0, 0x3b8, 0x3c1, 0x3c3, 0x3c4, 0x3c5, 0x3d6,
          0x3c9, 0x3be, 0x3c8, 0x3b6]                         # a..z -> Greek
    uc = [0x391, 0x392, 0x3a7, 0x394, 0x395, 0x3a6, 0x393, 0x397, 0x399, 0x3d1, 0x39a,
          0x39b, 0x39c, 0x39d, 0x39f, 0x3a0, 0x398, 0x3a1, 0x3a3, 0x3a4, 0x3a5, 0x3c2,
          0x3a9, 0x39e, 0x3a8, 0x396]                         # A..Z -> Greek
    m = {}
    for i, cp in enumerate(lc):
        m[0xF061 + i] = chr(cp)
    for i, cp in enumerate(uc):
        m[0xF041 + i] = chr(cp)
    for d in range(10):
        m[0xF030 + d] = str(d)
    m.update({0xF021: '!', 0xF023: '#', 0xF025: '%', 0xF026: '&', 0xF028: '(', 0xF029: ')',
              0xF02B: '+', 0xF02C: ',', 0xF02D: '−', 0xF02E: '.', 0xF02F: '/',
              0xF03A: ':', 0xF03B: ';', 0xF03C: '<', 0xF03D: '=', 0xF03E: '>',
              0xF0A2: "'", 0xF040: '≅', 0xF0A3: '≤', 0xF0B3: '≥',
              0xF0B9: '≠', 0xF0B1: '±', 0xF0B4: '×', 0xF0B8: '÷',
              0xF0AE: '→'})
    return m


SYMBOL = _build_symbol()


def fix_symbol(text):
    return "".join(SYMBOL.get(ord(c), c) if 0xE000 <= ord(c) <= 0xF8FF else c for c in text)


if __name__ == "__main__":
    import sys
    ps = find_pages(sys.argv[1])
    print("notation pages:", ps)
    for s, d in reconstruct(sys.argv[1], ps)[:40]:
        print(f"  {s:10} | {d[:70]}")
