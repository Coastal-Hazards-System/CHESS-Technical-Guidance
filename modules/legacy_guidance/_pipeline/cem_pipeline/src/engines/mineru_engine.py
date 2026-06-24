#!/usr/bin/env python3
"""MinerU engine adapter (spec §7.4).

Drives MinerU (CLI, pipeline backend) and parses its output for display/inline
equation LaTeX (UniMERNet). Used as the independent second opinion for the
equation ensemble. Returns per-page ordered equation candidates with bbox when
available (from middle.json), so they can be matched to Marker's bboxed
equations by source tag / page+order.
"""
import os
import re
import json
import glob
import shutil
import subprocess
import tempfile

_TAG_RE = re.compile(r'\(([IVXLC]+-\d+-\d+[a-z]?)\)')
# engines render the equation number variously: (III-1-8), \tag{III-1-8}, or bare
_ANYTAG_RE = re.compile(r'\\tag\s*\*?\s*\{\s*\(?([IVXLC]+-\d+-\d+[a-z]?)\)?\s*\}'
                        r'|\(([IVXLC]+-\d+-\d+[a-z]?)\)'
                        r'|\b([IVXLC]+-\d+-\d+[a-z]?)\s*$')


def detect_tag(latex):
    m = _ANYTAG_RE.search(latex or "")
    return next((g for g in m.groups() if g), None) if m else None


def _find_outputs(out_root):
    """Locate MinerU's middle.json and content_list.json under out_root."""
    mids = glob.glob(os.path.join(out_root, "**", "*middle.json"), recursive=True)
    cls = glob.glob(os.path.join(out_root, "**", "*content_list.json"), recursive=True)
    return (mids[0] if mids else None), (cls[0] if cls else None)


def _block_latex(block):
    """Pull LaTeX from a MinerU interline_equation block (lines[].spans[].content)."""
    parts = []
    for ln in block.get("lines", []) or []:
        for sp in ln.get("spans", []) or []:
            if "interline_equation" in str(sp.get("type", "")) or sp.get("content"):
                c = sp.get("content") or sp.get("latex")
                if c and c.strip():
                    parts.append(c.strip())
    if not parts:
        c = block.get("content") or block.get("latex")
        if c and c.strip():
            parts.append(c.strip())
    return " ".join(parts).strip()


def _walk_equations_middle(mid_json):
    """Collect interline-equation blocks {page, bbox, latex, order} from
    para_blocks (the finalized stream) only, to avoid the preproc duplicates."""
    eqs = []
    pdf_info = mid_json.get("pdf_info") or mid_json.get("pages") or []
    for pidx, page in enumerate(pdf_info):
        page_idx = page.get("page_idx", pidx)
        blocks = page.get("para_blocks") or page.get("preproc_blocks") or []
        order = 0
        for b in blocks:
            if not isinstance(b, dict):
                continue
            if "interline_equation" in str(b.get("type", "")):
                latex = _block_latex(b)
                if latex:
                    order += 1
                    eqs.append({"page": page_idx, "bbox": b.get("bbox"),
                                "latex": latex, "order": order})
    return eqs


def _walk_equations_contentlist(cl_json):
    eqs = []
    order = {}
    for item in cl_json:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "equation":
            latex = item.get("text") or item.get("latex")
            page = item.get("page_idx", 0)
            if latex and latex.strip():
                order[page] = order.get(page, 0) + 1
                eqs.append({"page": page, "bbox": item.get("bbox"),
                            "latex": latex.strip(), "order": order[page]})
    return eqs


def convert(pdf_path, workdir, device="cuda", timeout=3600):
    os.makedirs(workdir, exist_ok=True)
    out_root = tempfile.mkdtemp(prefix="mineru_", dir=workdir)
    exe = os.environ.get("CEM_MINERU_EXE") or shutil.which("mineru") or "mineru"
    env = dict(os.environ)
    env["MINERU_DEVICE_MODE"] = device  # MinerU 3.x: device via env, not a CLI flag
    # pipeline backend, formula parsing on (default), text method
    cmd = [exe, "-p", pdf_path, "-o", out_root, "-b", "pipeline", "-m", "auto", "-f", "true"]
    log = os.path.join(workdir, "_mineru_run.log")
    try:
        r = subprocess.run(cmd, capture_output=True, encoding="utf-8",
                           errors="replace", timeout=timeout, env=env)
        try:
            with open(log, "w", encoding="utf-8") as lf:
                lf.write((r.stdout or "") + "\n=== STDERR ===\n" + (r.stderr or ""))
        except Exception:
            pass
        if r.returncode != 0:
            tail = (r.stderr or r.stdout or "").strip().replace("\n", " ")[-300:]
            return {"engine": "mineru", "equations": [], "error": f"exit {r.returncode}: {tail}"}
    except Exception as e:
        return {"engine": "mineru", "equations": [], "error": f"run failed: {e}"}

    mid, cl = _find_outputs(out_root)
    eqs = []
    if mid:
        try:
            eqs = _walk_equations_middle(json.load(open(mid, encoding="utf-8")))
        except Exception:
            eqs = []
    if not eqs and cl:
        try:
            eqs = _walk_equations_contentlist(json.load(open(cl, encoding="utf-8")))
        except Exception:
            eqs = []
    # detect a source tag inside each latex if present
    for e in eqs:
        e["tag"] = detect_tag(e["latex"])
    return {"engine": "mineru", "equations": eqs, "out_root": out_root,
            "middle": mid, "content_list": cl}


if __name__ == "__main__":
    import sys
    res = convert(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
    print(f"mineru equations: {len(res.get('equations', []))}; err={res.get('error')}")
    for e in res.get("equations", [])[:5]:
        print(" p", e["page"], "tag", e.get("tag"), "|", e["latex"][:70])
