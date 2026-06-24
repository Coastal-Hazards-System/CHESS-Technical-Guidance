#!/usr/bin/env python3
"""Ground-truth fingerprinting from the born-digital text layer.

The PDF's real character stream inside an equation's bbox is the strongest
correctness signal available (no OCR involved). We reduce both that text and a
candidate's LaTeX to a *multiset of meaningful symbols* and compare them.
"""
import re
import collections

# --- Greek: unicode glyph -> canonical name --------------------------------
GREEK_UNICODE = {
    'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta', 'ε': 'epsilon',
    'ϵ': 'epsilon', 'ζ': 'zeta', 'η': 'eta', 'θ': 'theta', 'ϑ': 'theta',
    'ι': 'iota', 'κ': 'kappa', 'λ': 'lambda', 'μ': 'mu', 'µ': 'mu', 'ν': 'nu',
    'ξ': 'xi', 'ο': 'omicron', 'π': 'pi', 'ϖ': 'pi', 'ρ': 'rho', 'ϱ': 'rho',
    'σ': 'sigma', 'ς': 'sigma', 'τ': 'tau', 'υ': 'upsilon', 'φ': 'phi',
    'ϕ': 'phi', 'χ': 'chi', 'ψ': 'psi', 'ω': 'omega',
    'Γ': 'gamma', 'Δ': 'delta', 'Θ': 'theta', 'Λ': 'lambda', 'Ξ': 'xi',
    'Π': 'pi', 'Σ': 'sigma', 'Φ': 'phi', 'Ψ': 'psi', 'Ω': 'omega',
    'Υ': 'upsilon',
    '∇': 'nabla', '∂': 'partial', '∞': 'infty',
}

# --- Greek/function/operator latex commands -> canonical name --------------
GREEK_CMD = {
    'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'varepsilon', 'zeta', 'eta',
    'theta', 'vartheta', 'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi',
    'omicron', 'pi', 'varpi', 'rho', 'varrho', 'sigma', 'varsigma', 'tau',
    'upsilon', 'phi', 'varphi', 'chi', 'psi', 'omega',
    'Gamma', 'Delta', 'Theta', 'Lambda', 'Xi', 'Pi', 'Sigma', 'Phi', 'Psi',
    'Omega', 'Upsilon', 'nabla', 'partial', 'infty',
}
# canonicalize the var* / capital forms to their base name
_GREEK_CANON = {
    'varepsilon': 'epsilon', 'vartheta': 'theta', 'varpi': 'pi',
    'varrho': 'rho', 'varsigma': 'sigma', 'varphi': 'phi',
    'Gamma': 'gamma', 'Delta': 'delta', 'Theta': 'theta', 'Lambda': 'lambda',
    'Xi': 'xi', 'Pi': 'pi', 'Sigma': 'sigma', 'Phi': 'phi', 'Psi': 'psi',
    'Omega': 'omega', 'Upsilon': 'upsilon',
}

FUNCS = {
    'log', 'ln', 'lg', 'exp', 'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
    'sinh', 'cosh', 'tanh', 'coth', 'arcsin', 'arccos', 'arctan', 'sqrt',
    'max', 'min', 'lim', 'sup', 'inf', 'det', 'sum', 'int', 'prod', 'abs',
    'erf', 'erfc',
}

# letter-like LaTeX commands that denote a single symbol (map to a plain letter)
LETTER_CMD = {'ell': 'l', 'imath': 'i', 'jmath': 'j', 'hbar': 'h', 'aleph': 'a'}

# letter-like unicode glyphs -> plain letter
LETTERLIKE = {'ℓ': 'l', 'ı': 'i', 'ȷ': 'j', 'ℏ': 'h', 'ℎ': 'h', 'ℋ': 'h'}

SUPERSUB = {
    '⁰': '0', '¹': '1', '²': '2', '³': '3', '⁴': '4', '⁵': '5', '⁶': '6',
    '⁷': '7', '⁸': '8', '⁹': '9',
    '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', '₅': '5', '₆': '6',
    '₇': '7', '₈': '8', '₉': '9',
}

OPS_UNICODE = {
    '−': '-', '–': '-', '—': '-', '∗': '*', '×': '*', '·': '*', '⋅': '*',
    '∙': '*', '∕': '/', '⁄': '/', '≤': '<', '≥': '>', '≈': '=', '≃': '=',
    '≅': '=', '≡': '=', '∝': '=', '→': '=', '⇒': '=', '±': 'pm', '∓': 'pm',
}

# The CEM equations use a legacy math font whose text-layer codepoints don't
# match the rendered glyphs: '='→ "'", minus → "&", '+' → "%" (verified against
# the born-digital layer). Map them back so the ground-truth fingerprint keeps
# the relational/arithmetic operators.
CEM_MATHFONT = {"'": ' = ', '&': ' - ', '%': ' + ', '’': ' = ',
                '′': ' = '}

OP_CHARS = set('+-=/<>*')
_NAMES = sorted(set(GREEK_UNICODE.values()) | {_GREEK_CANON.get(g, g) for g in GREEK_CMD} | FUNCS,
                key=len, reverse=True)
# leading word-boundary; trailing must not be a letter (a digit may follow,
# e.g. "log2") so subscripted function names still tokenize as the function.
_NAME_RE = re.compile(r'\b(' + '|'.join(re.escape(n) for n in _NAMES) + r')(?![A-Za-z])')


def text_in_bbox(page, rect) -> str:
    """Born-digital characters inside a rectangle (PyMuPDF clip)."""
    try:
        return page.get_text("text", clip=rect)
    except Exception:
        return ""


def _tokenize(normalized: str):
    """Pull whole-word greek/function names, then single alnum chars + ops."""
    tokens = []

    def grab(m):
        tokens.append(_GREEK_CANON.get(m.group(0), m.group(0)))
        return ' '
    s = _NAME_RE.sub(grab, normalized)
    for ch in s:
        if ch.isalnum():
            tokens.append(ch)
        elif ch in OP_CHARS:
            tokens.append(ch)
    return sorted(tokens)


def symbol_multiset(s: str):
    """Fingerprint a born-digital text snippet."""
    if not s:
        return []
    for u, op in CEM_MATHFONT.items():
        s = s.replace(u, op)
    for u, ch in LETTERLIKE.items():
        s = s.replace(u, ch)
    for u, name in GREEK_UNICODE.items():
        s = s.replace(u, ' ' + name + ' ')
    for u, d in SUPERSUB.items():
        s = s.replace(u, d)
    for u, a in OPS_UNICODE.items():
        s = s.replace(u, ' pm ' if a == 'pm' else a)
    s = s.lower()
    return _tokenize(s)


def latex_symbol_multiset(latex: str):
    """Fingerprint a candidate LaTeX string, comparably to symbol_multiset."""
    if not latex:
        return []
    t = re.sub(r'\\tag\s*\{[^}]*\}', ' ', latex)
    t = re.sub(r'\\(?:label|nonumber|notag)\b', ' ', t)
    # operator commands -> canonical
    repl = {
        r'\\times': '*', r'\\cdot': '*', r'\\ast': '*', r'\\div': '/',
        r'\\leq': '<', r'\\le\b': '<', r'\\geq': '>', r'\\ge\b': '>',
        r'\\neq': '=', r'\\approx': '=', r'\\equiv': '=', r'\\simeq': '=',
        r'\\cong': '=', r'\\propto': '=', r'\\to': '=', r'\\rightarrow': '=',
        r'\\Rightarrow': '=', r'\\pm': ' pm ', r'\\mp': ' pm ',
    }
    for pat, r in repl.items():
        t = re.sub(pat, r, t)
    # greek / function commands -> their names
    def cmd(m):
        name = m.group(1)
        if name in GREEK_CMD or name in FUNCS:
            return ' ' + _GREEK_CANON.get(name, name) + ' '
        if name in LETTER_CMD:
            return ' ' + LETTER_CMD[name] + ' '
        return ' '  # structural command (\frac, \left, \mathbf, ...) -> drop
    t = re.sub(r'\\([a-zA-Z]+)', cmd, t)
    # drop structure/markup
    t = re.sub(r'[{}\^_~$&\\]', ' ', t)
    for u, d in SUPERSUB.items():
        t = t.replace(u, d)
    t = t.lower()
    return _tokenize(t)


# glyphs that are visually identical and routinely confused by OCR
_CONFUSABLE = {'i': 'l', '1': 'l', '|': 'l', 'o': '0'}


def loose(tokens):
    """Confusable-normalized multiset for deciding whether two independent engines
    agree despite cosmetic differences: I/l/1 -> l, O/0 -> 0, and '/' dropped (a
    fraction may be written inline 'a/b' by one engine and '\\frac{a}{b}' by the
    other)."""
    return sorted(_CONFUSABLE.get(t, t) for t in tokens if t != '/')


def multiset_edit_distance(a, b) -> int:
    """Number of single-symbol insert/deletes to turn multiset a into b."""
    ca, cb = collections.Counter(a), collections.Counter(b)
    diff = (ca - cb) + (cb - ca)
    return sum(diff.values())


def symbol_match(gt_fingerprint, candidate_latex, tolerance=1):
    """(matched: bool, distance: int) between GT fingerprint and candidate."""
    cand = latex_symbol_multiset(candidate_latex)
    d = multiset_edit_distance(gt_fingerprint, cand)
    return d <= tolerance, d


if __name__ == "__main__":
    # quick self-check
    gt = symbol_multiset("H = ρ g π / 2  with α and tanh(x)")
    print("GT:", gt)
    ok, d = symbol_match(gt, r"H = \rho g \pi / 2 \text{ with } \alpha \text{ and } \tanh(x) \tag{II-1-1}")
    print("match:", ok, "dist:", d)
