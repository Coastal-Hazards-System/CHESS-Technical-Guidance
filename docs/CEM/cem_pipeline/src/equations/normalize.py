#!/usr/bin/env python3
"""LaTeX sanitization (make engine output KaTeX-safe) and canonicalization
(aggressive normalization used only to test whether two engines *agree*)."""
import re


def sanitize(latex: str) -> str:
    """Make pix2tex / MinerU / Marker output KaTeX-renderable.

    Fixes the common KaTeX-rejection causes seen in testing without changing
    mathematical meaning: \\boldmath, {\\bf x}, {\\cal x}, stray \\bf/\\cal,
    ~ spacing, \\enspace, unbalanced \\left/\\right.
    """
    if not latex:
        return ""
    t = latex.strip()
    # strip full-document wrappers a vision-LLM sometimes emits
    t = re.sub(r'\\documentclass\s*(\[[^\]]*\])?\s*\{[^}]*\}', '', t)
    t = re.sub(r'\\usepackage\s*(\[[^\]]*\])?\s*\{[^}]*\}', '', t)
    t = re.sub(r'\\(begin|end)\s*\{document\}', '', t)
    t = re.sub(r'\\(begin|end)\s*\{equation\*?\}', '', t)
    t = re.sub(r'\\(begin|end)\s*\{(displaymath|math|gather\*?)\}', '', t)
    # equation-number label is re-added canonically by assemble; drop any here
    t = re.sub(r'\\tag\s*\*?\s*\{[^}]*\}', '', t)
    # strip surrounding math delimiters an engine may have included
    t = re.sub(r'^\s*\$\$?', '', t)
    t = re.sub(r'\$\$?\s*$', '', t)
    t = re.sub(r'^\s*\\\[', '', t)
    t = re.sub(r'\\\]\s*$', '', t)
    t = re.sub(r'^\s*\\\(', '', t)
    t = re.sub(r'\\\)\s*$', '', t)
    # \boldmath / \unboldmath are document-level, meaningless inline
    t = re.sub(r'\\(?:un)?boldmath', '', t)
    # {\bf x} -> \mathbf{x} ; {\cal X} -> \mathcal{X}
    t = re.sub(r'\{\s*\\bf\s*([^{}]*)\}', r'\\mathbf{\1}', t)
    t = re.sub(r'\{\s*\\cal\s*([^{}]*)\}', r'\\mathcal{\1}', t)
    t = re.sub(r'\{\s*\\it\s*([^{}]*)\}', r'\\mathit{\1}', t)
    t = re.sub(r'\{\s*\\rm\s*([^{}]*)\}', r'\\mathrm{\1}', t)
    # stray font switches KaTeX won't take
    t = re.sub(r'\\(?:bf|cal|it|rm|sf|tt|sl|sc)\b\s*', '', t)
    # spacing oddities
    t = t.replace('~', '\\,').replace('\\enspace', '\\,').replace('\\thinspace', '\\,')
    t = re.sub(r'\\(?:vspace|hspace)\s*\{[^}]*\}', '', t)
    # \mbox -> \text (KaTeX supports \text)
    t = re.sub(r'\\mbox\b', r'\\text', t)
    # balance \left / \right; if unbalanced, neutralize both
    if len(re.findall(r'\\left', t)) != len(re.findall(r'\\right', t)):
        t = t.replace('\\left', '').replace('\\right', '')
    # collapse whitespace
    t = re.sub(r'[ \t]+', ' ', t).strip()
    return t


_CANON_DROP = [
    r'\\,', r'\\;', r'\\:', r'\\!', r'\\quad', r'\\qquad', r'\\ ',
    r'\\left', r'\\right', r'\\displaystyle', r'\\limits', r'\\!',
]


def canonical(latex: str) -> str:
    """Aggressive normalization for engine-agreement comparison.

    Order of tokens is preserved (math is non-commutative here); only spelling
    of spacing/delimiters/fractions is unified and all whitespace removed.
    """
    if latex is None:
        return ""
    t = sanitize(latex)
    t = re.sub(r'\\tag\s*\{[^}]*\}', '', t)
    t = t.replace('\\dfrac', '\\frac').replace('\\tfrac', '\\frac')
    t = t.replace('\\cdot', '*').replace('\\times', '*').replace('\\ast', '*')
    t = t.replace('\\left', '').replace('\\right', '')
    for d in _CANON_DROP:
        t = re.sub(d, '', t)
    # unify delimiter spelling
    t = t.replace('\\{', '{').replace('\\}', '}')
    # drop all whitespace
    t = re.sub(r'\s+', '', t)
    return t


def agree(a: str, b: str) -> bool:
    """Do two candidate LaTeX strings represent the same expression?"""
    ca, cb = canonical(a), canonical(b)
    return bool(ca) and ca == cb


if __name__ == "__main__":
    s = sanitize(r"$$ H = {\bf c} \cdot \frac{1}{2} ~ g \boldmath \tag{II-1-1}$$")
    print("sanitize:", s)
    print("agree:", agree(r"\dfrac{a}{b}", r"\frac{a}{b} \,"))
