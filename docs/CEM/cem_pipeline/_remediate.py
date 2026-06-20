#!/usr/bin/env python3
"""One-off remediation across all converted chapters:
  * Part II WordPerfect-Greek glyph corruption in body prose (notation.fix_prose)
  * equation-LaTeX artifacts from the spaced-out engine output:
      \\ :              split medium-space -> \\:   (was rendering a stray colon)
      \\mathcal { H }   misread of the unit ft      -> \\mathrm{ft}
      \\mathcal { X }   script letter that is plain  -> X  (incl. \\greek)
Run from docs/CEM/out:  python ../cem_pipeline/_remediate.py
"""
import os
import re
import sys
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import notation  # noqa: E402

MATHCAL_FT = re.compile(r"\\mathcal\s*\{\s*H\s*\}")
MATHCAL = re.compile(r"\\mathcal\s*\{\s*(\\?[A-Za-z]+)\s*\}")
SPLIT_COLON = re.compile(r"\\ :")


def fix_equations(text):
    text = notation.fix_symbol(text)        # Symbol-font PUA glyphs -> Unicode (before subscripts)
    text = MATHCAL_FT.sub(r"\\mathrm{ft}", text)
    text = MATHCAL.sub(r"\1", text)
    text = SPLIT_COLON.sub(r"\\:", text)
    text = notation.fix_degree(text)
    text = notation.fix_currency(text)
    return text


def main():
    tot_prose = tot_eq = 0
    for md in sorted(glob.glob("markdown/**/*.md", recursive=True)):
        if "_flagged" in md:
            continue
        head = open(md, encoding="utf-8").read()
        m = re.search(r'source_pdf:\s*"([^"]+)"', head)
        pdf = "chapters/" + m.group(1) if m else None
        prose = 0
        if pdf and os.path.exists(pdf):
            prose, _, _ = notation.fix_prose(md, pdf, set(notation.find_pages(pdf)))
        text = open(md, encoding="utf-8").read().replace("\r\n", "\n")
        new = fix_equations(text)
        n_eq = 0
        if new != text:
            n_eq = (len(SPLIT_COLON.findall(text)) + len(MATHCAL.findall(text)))
            with open(md, "w", encoding="utf-8", newline="\n") as f:
                f.write(new)
        nav = notation.fix_nav(md, pdf if (pdf and os.path.exists(pdf)) else None)  # TOC from PDF coords
        deflists = notation.fix_deflists(md)   # "where:" blocks -> bullet lists
        subsup = 0
        if pdf and os.path.exists(pdf):        # restore flattened sub/superscripts
            subsup = notation.fix_subscripts(md, pdf)
        tot_prose += prose
        tot_eq += n_eq
        if prose or n_eq or nav or deflists or subsup:
            print(f"{md}: prose={prose} eq={n_eq} nav={nav} deflists={deflists} subsup={subsup}")
    # auxiliary gallery pages carry the same equation LaTeX (single-backslash, as
    # in the .md). equations.json is a pretty-printed data index that nothing on
    # the site renders, so it is left untouched to avoid reformatting churn.
    for gh in glob.glob("markdown/**/*.gallery.html", recursive=True):
        t = open(gh, encoding="utf-8").read()
        new = fix_equations(t)
        if new != t:
            open(gh, "w", encoding="utf-8", newline="\n").write(new)
    print(f"TOTAL prose patterns={tot_prose}, equation fixes={tot_eq}")


if __name__ == "__main__":
    main()
