#!/usr/bin/env python3
"""Stage 3: sanitize pix2tex LaTeX, validate with KaTeX (via node), substitute
valid equations into the skeleton as ```math blocks; route failures to a
per-chapter _review.md. Requires node + katex (npm i katex)."""
import sys, json, re, os, subprocess, tempfile

KATEX_NODE = os.path.join(os.path.dirname(__file__), "katex_validate.js")

def sanitize(s):
    t=s
    t=re.sub(r'\\boldmath','',t)
    t=re.sub(r'\{\\bf\s*([^}]*)\}',r'\\mathbf{\1}',t)
    t=re.sub(r'\{\\cal\s*([^}]*)\}',r'\\mathcal{\1}',t)
    t=re.sub(r'\\cal\s*','',t); t=re.sub(r'\\bf\s*','',t)
    t=t.replace('~','\\,').replace('\\enspace','\\,')
    L=len(re.findall(r'\\left',t)); R=len(re.findall(r'\\right',t))
    if L!=R: t=t.replace('\\left','').replace('\\right','')
    return t.strip()

def validate_batch(latex_map):
    """Return {id: bool} via node+katex."""
    with tempfile.NamedTemporaryFile('w',suffix='.json',delete=False) as f:
        json.dump(latex_map,f); inp=f.name
    out=subprocess.run(["node",KATEX_NODE,inp],capture_output=True,text=True)
    os.unlink(inp)
    return json.loads(out.stdout)

def assemble(skeleton, latex_json, assets_rel, out_md, review_md):
    md=open(skeleton).read(); raw=json.load(open(latex_json))
    san={k:sanitize(v) for k,v in raw.items() if not v.startswith("__")}
    valid=validate_batch(san) if san else {}
    review=["# Equation review queue\n",
            "Failed automatic transcription/validation. Interim image shown in chapter.\n"]
    nv=nr=0
    def repl(m):
        nonlocal nv,nr
        eqid=m.group(1)
        if valid.get(eqid):
            nv+=1; return f"```math\n{san[eqid]} \\tag{{{eqid}}}\n```"
        nr+=1
        review.append(f"## Equation {eqid}\n\n![Equation {eqid}]({assets_rel}/eq-{eqid}.png)\n\n"
                      f"OCR (needs fixing):\n\n```\n{raw.get(eqid,'')}\n```\n")
        return (f"> ⚠️ **Equation {eqid}** — transcription needs review (see `_review.md`).\n>\n"
                f"> ![Equation {eqid}]({assets_rel}/eq-{eqid}.png)")
    md=re.sub(r"\{\{EQ:([^}]+)\}\}",repl,md)
    open(out_md,"w").write(md); open(review_md,"w").write("\n".join(review))
    return nv,nr

if __name__=="__main__":
    a=sys.argv
    nv,nr=assemble(a[1],a[2],a[3],a[4],a[5])
    print(f"equations: {nv} inline LaTeX, {nr} -> review")
