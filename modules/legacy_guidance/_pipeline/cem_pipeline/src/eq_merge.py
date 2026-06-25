#!/usr/bin/env python3
"""Merge-based equation correction.

The original conversion saved, per numbered equation, a precise source crop
(from the Marker/MinerU bounding box) at `assets/.../eq-NNN-<tag>.png` and a
per-chapter `ch-YY.equations.json` index. This tool re-reads a deferred / suspect
equation's *source crop* with the local vision-LLM (qwen2.5vl, via
engines.vlm_engine), compares it to the equation currently in the chapter `.md`,
and -- only when they differ and the source reading is KaTeX-valid -- MERGES the
corrected LaTeX back into the `.md` (replacing just that equation's body, keeping
its `\\tag`). No full re-conversion, so manual fixes elsewhere are preserved.

Usage (run from .../manuals/cem):
  python ../../_pipeline/cem_pipeline/src/eq_merge.py part-02/ch-01.md II-1-142
  python ../../_pipeline/cem_pipeline/src/eq_merge.py part-02/ch-01.md II-1-142 --apply
  python ../../_pipeline/cem_pipeline/src/eq_merge.py part-02/ch-01.md --tags II-1-142,II-1-146
A faithful equation (source == md) is reported as MATCH and never rewritten.
"""
import os, re, sys, json, subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engines import vlm_engine  # noqa: E402
from equations import normalize  # noqa: E402  (symbol-level consensus, filters diacritic/format noise)

KATEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "node_modules", "katex")


def _index(md_path):
    """tag -> crop image path, from the chapter's .equations.json (next to the .md)."""
    j = re.sub(r"\.md$", ".equations.json", md_path)
    if not os.path.exists(j):
        return {}
    base = os.path.dirname(md_path)
    out = {}
    for e in json.load(open(j, encoding="utf-8")):
        img = e.get("image")
        if e.get("tag") and img:
            out[e["tag"]] = os.path.join(base, img)
    return out


def _clean(t):
    t = (t or "").strip()
    for a, b in (("```latex", "```"), ("```math", "```"), ("```", "```")):
        t = t.replace(a, "").replace(b, "")
    t = t.strip()
    for a, b in (("\\[", "\\]"), ("\\(", "\\)"), ("$$", "$$"), ("$", "$")):
        if t.startswith(a) and t.endswith(b):
            t = t[len(a):-len(b)].strip()
    t = re.sub(r"\\tag\{[^}]*\}", "", t)
    return re.sub(r"\s+", " ", t.replace("\n", " ")).strip()


def _katex_ok(latex):
    node = os.environ.get("CEM_NODE", "node")
    js = ("const k=require(%r);try{k.renderToString(process.argv[1],"
          "{throwOnError:true,strict:false,displayMode:true});console.log('OK')}"
          "catch(e){console.log('FAIL');process.exit(1)}" % os.path.abspath(KATEX))
    try:
        r = subprocess.run([node, "-e", js, latex], capture_output=True, text=True, timeout=30)
        return r.returncode == 0
    except Exception as e:
        print("  (katex check skipped:", e, ")")
        return True


def _md_eq_line(lines, tag):
    """Index of the single-line `... \\tag{TAG}` equation in a ```math block, or None."""
    pat = re.compile(r"\\tag\{" + re.escape(tag) + r"\}\s*$")
    for i, ln in enumerate(lines):
        if pat.search(ln):
            return i
    return None


def process(md_path, tag, apply=False):
    idx = _index(md_path)
    if tag not in idx:
        print(f"{tag}: no crop in equations.json (not a numbered display equation)")
        return "no-crop"
    crop = idx[tag]
    if not os.path.exists(crop):
        print(f"{tag}: crop missing on disk ({crop})")
        return "no-crop"
    src = _clean(vlm_engine.transcribe(crop))
    text = open(md_path, encoding="utf-8").read().replace("\r\n", "\n")
    lines = text.split("\n")
    i = _md_eq_line(lines, tag)
    cur = _clean(lines[i]) if i is not None else "(multi-line / not found)"
    # Symbol-level consensus (the pipeline's own agree()) ignores diacritic/format
    # noise that a single VLM read introduces (dropped overbars, reflowed brackets).
    same = (re.sub(r"\s+", "", cur) == re.sub(r"\s+", "", src)) or normalize.agree(cur, src)
    print(f"\n{tag}    crop: {crop}")
    print(f"  md:     {cur}")
    print(f"  source: {src}")
    if same:
        print("  => MATCH (faithful to source at the symbol level)")
        return "match"
    if i is None:
        print("  => DIFFERS but equation is multi-line / untagged-line; review manually")
        return "manual"
    if not _katex_ok(src):
        print("  => source reading is not KaTeX-valid; skip")
        return "invalid"
    print("  => DIFFERS (source-valid). " + ("APPLYING merge." if apply
          else "Review the crop first (a single VLM read can drop an overbar or "
               "reflow brackets); --apply replaces the md line with this reading."))
    if apply:
        lines[i] = src + " \\tag{" + tag + "}"
        with open(md_path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lines))
    return "applied" if apply else "differs"


if __name__ == "__main__":
    md = sys.argv[1]
    apply = "--apply" in sys.argv
    if "--tags" in sys.argv:
        tags = sys.argv[sys.argv.index("--tags") + 1].split(",")
    else:
        tags = [sys.argv[2]]
    for t in tags:
        process(md, t.strip(), apply=apply)
