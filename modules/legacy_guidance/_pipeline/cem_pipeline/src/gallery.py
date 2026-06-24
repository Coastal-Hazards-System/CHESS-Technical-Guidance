#!/usr/bin/env python3
"""Build a per-chapter HTML 'equation gallery': every equation rendered with
KaTeX next to its source-PDF crop, with verified/flagged status. Lets a human
visually scan all equations. Reads the *.equations.json sidecars written by
run_all. Also writes a master gallery index."""
import os
import sys
import json
import glob
import html

_HEAD = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"
 onload="renderMathInElement(document.body,{{delimiters:[{{left:'$$',right:'$$',display:true}}],throwOnError:false}})"></script>
<style>
 body{{font-family:system-ui,Arial,sans-serif;margin:24px;color:#222}}
 table{{border-collapse:collapse;width:100%}}
 td,th{{border:1px solid #ddd;padding:8px 10px;vertical-align:middle;text-align:left}}
 th{{background:#f4f4f4}}
 .v{{color:#1a7f37;font-weight:600}} .f{{color:#bf8700;font-weight:600}}
 .rendered{{font-size:1.15em}} img{{max-height:60px;max-width:380px}}
 .src{{background:#fafafa}}
</style></head><body>
<h1>{title}</h1>
<p>{summary}</p>
<table><tr><th>#</th><th>ID</th><th>Status</th><th>Rendered (KaTeX)</th><th>Source crop (PDF)</th></tr>
"""
_FOOT = "</table></body></html>"


def _row(e):
    latex = e.get("latex") or ""
    rendered = ("$$" + html.escape(latex, quote=False) + "$$") if latex else "<i>—</i>"
    cls = "v" if e.get("verified") else "f"
    status = html.escape(str(e.get("status") or ""))
    img = e.get("image")
    imgcell = f'<img src="{html.escape(img)}" loading="lazy">' if img else "—"
    return (f"<tr><td>{e.get('n')}</td><td>{html.escape(str(e.get('eqid') or ''))}</td>"
            f"<td class='{cls}'>{status}</td>"
            f"<td class='rendered'>{rendered}</td>"
            f"<td class='src'>{imgcell}</td></tr>\n")


def build(out_dir):
    sidecars = sorted(glob.glob(os.path.join(out_dir, "markdown", "**", "*.equations.json"),
                                recursive=True))
    index = ["# Equation galleries", "",
             "Per-chapter visual review: every equation rendered (KaTeX) next to its "
             "source-PDF crop. Open the HTML files in a browser.", ""]
    for sc in sidecars:
        eqs = json.load(open(sc, encoding="utf-8"))
        chdir = os.path.dirname(sc)
        base = os.path.basename(sc).replace(".equations.json", "")
        nver = sum(1 for e in eqs if e.get("verified"))
        title = f"Equation gallery — {os.path.basename(chdir)}/{base}"
        summary = (f"{len(eqs)} equations — {nver} machine-verified, {len(eqs)-nver} flagged. "
                   f"Green = verified, amber = flagged (still shows best LaTeX + source crop).")
        out = os.path.join(chdir, base + ".gallery.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(_HEAD.format(title=html.escape(title), summary=html.escape(summary)))
            for e in eqs:
                f.write(_row(e))
            f.write(_FOOT)
        rel = os.path.relpath(out, out_dir).replace(os.sep, "/")
        index.append(f"- [{os.path.basename(chdir)}/{base}]({rel}) — {len(eqs)} eqs, {nver} verified")
    with open(os.path.join(out_dir, "equation_galleries.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(index))
    print(f"Built {len(sidecars)} equation galleries")
    return len(sidecars)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
