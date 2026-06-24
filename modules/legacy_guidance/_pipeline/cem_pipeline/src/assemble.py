#!/usr/bin/env python3
"""Assemble the final chapter Markdown from Marker's block stream plus the
verified equation decisions, reconciled tables, and figures (spec §7.11).

run_all attaches to each block:
  equation block -> block["resolved"] = {latex, status, tag, katex_valid, crop_rel}
  table block    -> block["table_render"] = {"gfm":[...]} | {"image_rel": "..."}
Only KaTeX-valid LaTeX is ever emitted inside a ```math block (spec §12), so the
final file has zero KaTeX failures; anything unverifiable is clearly flagged.
"""
import os
import re
import json

ACCEPTED = {"agreed", "agreed_gt", "single_verified", "multi_verified",
            "self_corrected", "resolved"}

_DOTS = re.compile(r'\s*(?:\.\s*){4,}')
_TOC_HINT = re.compile(r'(Table of Contents|List of Tables|List of Figures)', re.I)


def _front_matter(meta):
    lines = ["---"]
    for k in ["manual", "part", "chapter", "title", "source_pdf", "pages",
              "revision", "equations_total", "equations_verified",
              "tables_gfm", "tables_image", "figures"]:
        v = meta.get(k, "")
        if isinstance(v, str):
            lines.append(f'{k}: "{v}"')
        else:
            lines.append(f'{k}: {v}')
    lines.append("---")
    lines.append("")
    return lines


def _emit_equation(block, assets_rel, counts, flagged):
    r = block.get("resolved") or {}
    latex = r.get("latex")
    status = r.get("status", "no_candidates")
    tag = r.get("tag") or block.get("tag")
    tagsfx = f" \\tag{{{tag}}}" if tag else ""
    eqid = tag or r.get("eqid") or "?"
    crop_rel = r.get("crop_rel")

    if status in ACCEPTED and latex and r.get("katex_valid", True):
        counts["equations_verified"] += 1
        counts[f"eq_{status}"] = counts.get(f"eq_{status}", 0) + 1
        return [f"```math\n{latex}{tagsfx}\n```"]

    # flagged
    counts["equations_flagged"] += 1
    flagged.append({"eqid": eqid, "status": status, "latex": latex,
                    "crop_rel": crop_rel, "evidence": r.get("evidence")})
    if latex and r.get("katex_valid"):
        # valid LaTeX but symbols not confirmed -> emit it, clearly marked
        return [f"> ⚠️ Equation {eqid}: best machine candidate; symbol match "
                f"unconfirmed — see `_flagged.md`.",
                f"```math\n{latex}{tagsfx}\n```"]
    # no valid LaTeX -> source-crop fallback (never emit invalid math)
    if crop_rel:
        return [f"> ⚠️ Equation {eqid}: automatic transcription unverified — "
                f"source image shown; see `_flagged.md`.",
                f"![Equation {eqid}]({assets_rel}/{crop_rel})"]
    return [f"> ⚠️ Equation {eqid}: could not transcribe; see `_flagged.md`."]


def _emit_table(block, assets_rel, counts):
    tr = block.get("table_render") or {}
    tid = tr.get("id", "")
    title = tr.get("title", "")
    head = [f"**Table {tid}. {title}**".rstrip()] if tid else []
    if tr.get("gfm"):
        counts["tables_gfm"] += 1
        return ["", *head, "", *tr["gfm"], ""]
    if tr.get("image_rel"):
        counts["tables_image"] += 1
        return ["", *head, "",
                f"> ⚠️ Table {tid} not auto-gridded; image fallback.",
                f"![Table {tid}]({assets_rel}/{tr['image_rel']})", ""]
    # marker gave html but no reconstruction -> fall through to raw text drop
    return []


def assemble(blocks, meta, assets_rel, out_md, flagged_md, qa_json):
    counts = {"equations_verified": 0, "equations_flagged": 0,
              "tables_gfm": 0, "tables_image": 0, "figures": 0}
    flagged = []
    md = []
    for b in blocks:
        t = b.get("type")
        if t == "heading":
            lvl = max(1, min(6, b.get("level", 2)))
            txt = b.get("text", "").strip()
            if txt:
                md += ["", "#" * lvl + " " + txt, ""]
        elif t == "equation":
            md += ["", *_emit_equation(b, assets_rel, counts, flagged), ""]
        elif t == "table":
            md += _emit_table(b, assets_rel, counts)
        elif t == "figure":
            counts["figures"] += 1
            cap = b.get("text", "").strip()
            rel = b.get("image_rel")
            if rel:
                md += ["", f"![{cap or 'Figure'}]({assets_rel}/{rel})", ""]
            if cap:
                md += [f"*{cap}*", ""]
        elif t == "caption":
            cap = b.get("text", "").strip()
            if cap:
                md += ["", f"*{cap}*", ""]
        elif t == "list":
            txt = b.get("text", "").strip()
            if txt:
                md.append(f"- {txt}")
        else:  # text
            txt = b.get("text", "").strip()
            if not txt:
                continue
            if _DOTS.search(txt):  # TOC dot-leader line
                txt = _DOTS.sub("  —  ", txt)
            md.append(txt)

    text = re.sub(r"\n{3,}", "\n\n", "\n".join(md)).strip() + "\n"

    meta = dict(meta)
    meta["equations_verified"] = counts["equations_verified"]
    meta["tables_gfm"] = counts["tables_gfm"]
    meta["tables_image"] = counts["tables_image"]
    meta["figures"] = counts["figures"]
    full = "\n".join(_front_matter(meta)) + text
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(full)

    # flagged file
    fl = ["# Machine-flagged residual\n",
          "Equations/tables the pipeline could not fully auto-verify. Each entry "
          "has the source crop and every engine candidate with scores. No human "
          "step is required; this is an auditable list.\n"]
    for item in flagged:
        fl.append(f"## Equation {item['eqid']}  (status: {item['status']})\n")
        if item.get("crop_rel"):
            fl.append(f"![Equation {item['eqid']}]({assets_rel}/{item['crop_rel']})\n")
        fl.append(f"Best candidate:\n\n```\n{item.get('latex') or ''}\n```\n")
        ev = item.get("evidence")
        if ev:
            fl.append("Candidates / evidence:\n\n```json\n"
                      + json.dumps(ev, indent=2)[:4000] + "\n```\n")
    with open(flagged_md, "w", encoding="utf-8") as f:
        f.write("\n".join(fl))

    qa = dict(meta)
    qa.update(counts)
    qa["equations_total"] = counts["equations_verified"] + counts["equations_flagged"]
    with open(qa_json, "w", encoding="utf-8") as f:
        json.dump(qa, f, indent=2)
    return counts
