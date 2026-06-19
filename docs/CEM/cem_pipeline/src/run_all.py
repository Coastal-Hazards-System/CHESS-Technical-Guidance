#!/usr/bin/env python3
"""Orchestrator (spec §7.12 / §8). Ensemble Marker + MinerU, verify every
equation against the born-digital text layer + KaTeX, self-correct the residual,
reconcile tables, assemble one Markdown per chapter. Manifest-driven & resumable.

  python run_all.py --src <CEM dir> --out <out dir> [--jobs N] [--only II-1,III-1] [--force]
"""
import argparse
import os
import sys
import json
import re
import glob
import collections
import statistics
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "engines"))
sys.path.insert(0, os.path.join(HERE, "equations"))

import fitz  # noqa: E402
import groundtruth as GT  # noqa: E402
import ensemble as ENS     # noqa: E402
import selfcorrect as SC   # noqa: E402
import verify as VF        # noqa: E402
import tables as TB        # noqa: E402
import assemble as ASM     # noqa: E402

_TAG_RE = re.compile(r'\(([IVXLC]+-\d+-\d+[a-z]?)\)')


def load_cfg(out_dir):
    cfg = {}
    p = os.path.join(os.path.dirname(HERE), "config.yaml")
    if os.path.exists(p):
        try:
            import yaml
            cfg = yaml.safe_load(open(p)) or {}
        except Exception:
            cfg = {}
    return cfg


def scale_bbox(bbox, page_dims, page, pdf_page):
    if not bbox:
        return None
    W, H = (page_dims.get(page) or [pdf_page.rect.width, pdf_page.rect.height])
    sx = pdf_page.rect.width / W if W else 1.0
    sy = pdf_page.rect.height / H if H else 1.0
    return fitz.Rect(bbox[0] * sx, bbox[1] * sy, bbox[2] * sx, bbox[3] * sy)


def find_tag(pdf_page, rect):
    # equation numbers sit at the right margin, at the equation's vertical level;
    # restrict to that column to avoid grabbing a neighbour row's number.
    W = pdf_page.rect.width
    band = fitz.Rect(W * 0.58, max(0, rect.y0 - 3), W, rect.y1 + 3)
    txt = pdf_page.get_text("text", clip=band)
    m = _TAG_RE.search(txt)
    return m.group(1) if m else None


def crop_eq(pdf_page, rect, assets_dir, eqid):
    r = fitz.Rect(rect.x0 - 6, rect.y0 - 6, rect.x1 + 6, rect.y1 + 6) & pdf_page.rect
    pix = pdf_page.get_pixmap(matrix=fitz.Matrix(4, 4), clip=r)
    safe = re.sub(r'[^A-Za-z0-9_-]', '_', str(eqid))
    rel = f"eq-{safe}.png"
    pix.save(os.path.join(assets_dir, rel))
    return rel


def html_table_to_gfm(html):
    if not html:
        return None
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table")
        if not table:
            return None
        rows = []
        for tr in table.find_all("tr"):
            cells = [re.sub(r'\s+', ' ', c.get_text(" ", strip=True))
                     for c in tr.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if len(rows) < 2:
            return None
        ncol = max(len(r) for r in rows)
        rows = [r + [""] * (ncol - len(r)) for r in rows]
        gfm = ["| " + " | ".join(rows[0]) + " |",
               "| " + " | ".join("---" for _ in range(ncol)) + " |"]
        for r in rows[1:]:
            gfm.append("| " + " | ".join(r) + " |")
        return gfm
    except Exception:
        return None


def _mineru_engines(cfg):
    """Build the optional self-correction engine callables per config."""
    eng = {}
    ecfg = cfg.get("engines", {})
    if ecfg.get("pix2tex"):
        try:
            import pix2tex_engine as PX
            eng["pix2tex"] = lambda crop: PX.transcribe(crop)
        except Exception:
            pass
    if ecfg.get("vlm") or cfg.get("selfcorrect", {}).get("enable_vlm_on_fail"):
        try:
            import vlm_engine as VL
            VL.configure(cfg.get("vlm", {}))
            if VL.available():
                eng["vlm"] = lambda crop: VL.transcribe(crop, temperature=0.0)
                eng["vlm2"] = lambda crop: VL.transcribe(crop, temperature=0.5)
                eng["vlm_repair"] = lambda crop, latex, miss, extra: VL.repair(crop, latex, miss, extra)
        except Exception:
            pass
    return eng


def _ov(a0, a1, b0, b1):
    return max(0.0, min(a1, b1) - max(a0, b0))


def match_mineru(marker_eqs, mineru_eqs):
    """Pair each Marker equation with a MinerU equation. Authoritative key is the
    source tag; otherwise match by page + bbox vertical/horizontal overlap
    (spec §8). Greedy, each MinerU equation used at most once. Returns per-marker
    MinerU latex (or None)."""
    by_tag = {}
    by_page = collections.defaultdict(list)
    for idx, e in enumerate(mineru_eqs):
        if e.get("tag"):
            by_tag.setdefault(e["tag"], idx)
        by_page[e["page"]].append(idx)
    used = set()
    out = []
    for me in marker_eqs:
        chosen = None
        # bbox geometry first (reliable; both engines share PDF-point coords) ...
        mr = me.get("_rect") or me.get("bbox")
        if mr:
            best, best_ov = None, 0.0
            for idx in by_page.get(me["page"], []):
                if idx in used:
                    continue
                eb = mineru_eqs[idx].get("bbox")
                if not eb or len(eb) < 4:
                    continue
                oy = _ov(mr[1], mr[3], eb[1], eb[3])
                ox = _ov(mr[0], mr[2], eb[0], eb[2])
                if oy > best_ov and ox > 0:
                    best, best_ov = idx, oy
            if best is not None and best_ov > 2.0:
                chosen = best
        # ... source tag only as a fallback (find_tag mis-tags worked-example lines)
        if chosen is None:
            tag = me.get("_tag") or me.get("tag")
            if tag and tag in by_tag and by_tag[tag] not in used:
                chosen = by_tag[tag]
        if chosen is not None:
            used.add(chosen)
            out.append(mineru_eqs[chosen]["latex"])
        else:
            out.append(None)
    return out


def split_merged_equations(blocks, mineru_eqs, page_dims, doc):
    """Marker sometimes merges a vertical stack of separate display equations
    (e.g. a column of worked-example values) into one tall block and transcribes
    only the top line. MinerU segments them individually. Where a tall Marker
    equation block contains >=2 MinerU equations, split it into one block per
    MinerU equation (tight bbox, MinerU LaTeX) so no equation is dropped."""
    heights = []
    for b in blocks:
        if b.get("type") == "equation" and b.get("bbox"):
            pg = min(b["page"], len(doc) - 1)
            r = scale_bbox(b["bbox"], page_dims, b["page"], doc[pg])
            if r:
                heights.append(r.y1 - r.y0)
    med = statistics.median(heights) if heights else 18.0
    by_page = collections.defaultdict(list)
    for e in mineru_eqs:
        if e.get("bbox") and len(e["bbox"]) >= 4:
            by_page[e["page"]].append(e)
    out, nsplit = [], 0
    for b in blocks:
        if b.get("type") != "equation" or not b.get("bbox"):
            out.append(b)
            continue
        pg = min(b["page"], len(doc) - 1)
        r = scale_bbox(b["bbox"], page_dims, b["page"], doc[pg])
        if not r:
            out.append(b)
            continue
        inside = [e for e in by_page.get(b["page"], [])
                  if r.y0 - 3 <= (e["bbox"][1] + e["bbox"][3]) / 2 <= r.y1 + 3
                  and _ov(r.x0, r.x1, e["bbox"][0], e["bbox"][2]) > 1]
        inside.sort(key=lambda e: e["bbox"][1])
        if len(inside) >= 2 and (r.y1 - r.y0) > max(1.8 * med, 40):
            nsplit += 1
            for k, e in enumerate(inside):
                out.append({"type": "equation", "page": b["page"],
                            "bbox": list(e["bbox"]), "_pts": True,
                            "latex": b.get("latex") if k == 0 else None,
                            "_forced_mineru": e["latex"], "_split": True})
        else:
            out.append(b)
    if nsplit:
        print(f"  split {nsplit} merged equation block(s) via MinerU segmentation", flush=True)
    return out


def process_chapter(m, src_chapters, out_dir, cfg, force=False):
    import marker_engine as MK
    cid = f"{m['part_roman']}-{m['chapter']}" if m['chapter'] else m['part_roman']
    partnum = m['portfolio'].split('-')[-1] if m['portfolio'].startswith('Part') else None
    partdir = f"part-{partnum}" if partnum else ("appendix" if m['kind'] == 'glossary' else "misc")
    outdir = os.path.join(out_dir, "markdown", partdir)
    os.makedirs(outdir, exist_ok=True)
    base = f"ch-{m['chapter']:02d}" if m['chapter'] else "appendix-a-glossary"
    final = os.path.join(outdir, base + ".md")
    if os.path.exists(final) and not force:
        print(f"skip {cid} (done)")
        return "skipped"
    pdf = os.path.join(src_chapters, m["work_file"])
    assets = os.path.join(outdir, "assets", f"{partdir}-{base}")
    os.makedirs(assets, exist_ok=True)
    assets_rel = f"assets/{partdir}-{base}"
    # clear regenerated crops (keep marker figure images) so there's exactly one
    # current source image per equation/table
    for old in glob.glob(os.path.join(assets, "eq-*.png")) + glob.glob(os.path.join(assets, "table-*.png")):
        try:
            os.remove(old)
        except OSError:
            pass
    print(f"=== {cid}: {m.get('title','')[:50]} ({m.get('pages')}pp) ===", flush=True)

    # 1. Marker backbone (cached for fast re-assembly / resumability)
    mk_cache = os.path.join(out_dir, "_work", f"{cid}.marker.json")
    os.makedirs(os.path.dirname(mk_cache), exist_ok=True)
    if os.path.exists(mk_cache) and os.environ.get("CEM_FORCE_MARKER") != "1":
        data = json.load(open(mk_cache, encoding="utf-8"))
        blocks = data["blocks"]
        page_dims = {int(k): v for k, v in data["page_dims"].items()}
    else:
        mk = MK.convert(pdf, assets)
        blocks = mk["blocks"]
        page_dims = mk.get("page_dims", {})
        json.dump({"blocks": blocks, "page_dims": page_dims},
                  open(mk_cache, "w", encoding="utf-8"))

    # 2. MinerU second opinion (own venv via CLI), cached for resumability
    mineru_eqs = []
    if cfg.get("engines", {}).get("mineru", True) and os.environ.get("CEM_DISABLE_MINERU") != "1":
        mu_cache = os.path.join(out_dir, "_work", f"{cid}.mineru.json")
        if os.path.exists(mu_cache) and os.environ.get("CEM_FORCE_MINERU") != "1":
            try:
                mineru_eqs = json.load(open(mu_cache, encoding="utf-8"))
            except Exception:
                mineru_eqs = []
        else:
            try:
                import mineru_engine as MU
                res = MU.convert(pdf, os.path.join(out_dir, "_work", cid),
                                 device=("cuda" if cfg.get("device", "auto") != "cpu" else "cpu"))
                mineru_eqs = res.get("equations", [])
                if res.get("error"):
                    print(f"  mineru: {res['error']}")
                json.dump(mineru_eqs, open(mu_cache, "w", encoding="utf-8"))
            except Exception as e:
                print(f"  mineru skipped: {e}")

    # 3. equations: split Marker-merged stacks, then fingerprint + crop + tag
    doc = fitz.open(pdf)
    if mineru_eqs:
        blocks = split_merged_equations(blocks, mineru_eqs, page_dims, doc)
    eq_blocks = [b for b in blocks if b["type"] == "equation"]
    for i, b in enumerate(eq_blocks):
        pg = min(b["page"], len(doc) - 1)
        pdf_page = doc[pg]
        rect = (fitz.Rect(b["bbox"]) if b.get("_pts")
                else scale_bbox(b["bbox"], page_dims, b["page"], pdf_page))
        gt_txt = GT.text_in_bbox(pdf_page, rect) if rect else ""
        # the equation number (e.g. "(III-1-1a)") often sits inside the bbox;
        # it is a label, not part of the math -> drop before fingerprinting.
        gt_txt = _TAG_RE.sub(' ', gt_txt)
        b["_gt"] = GT.symbol_multiset(gt_txt)
        b["_rect"] = [rect.x0, rect.y0, rect.x1, rect.y1] if rect else None
        b["_tag"] = b.get("tag") or (find_tag(pdf_page, rect) if rect else None)
        b["tag"] = b["_tag"]
        # unique per-equation crop id (index prefix avoids tag/synthetic collisions)
        crop_id = f"{i+1:03d}-{b['_tag'] or cid}"
        b["_crop"] = crop_eq(pdf_page, rect, assets, crop_id) if rect else None
        if os.environ.get("CEM_DEBUG_EQ") == "1":
            lf = GT.latex_symbol_multiset(b.get("latex") or "")
            print(f"  [eq {b['_tag']}] dist={GT.multiset_edit_distance(b['_gt'], lf)} "
                  f"gt={b['_gt']} | lx={lf}", flush=True)

    # de-duplicate equation tags: a source number belongs to exactly one equation
    # (keep the first in reading order; later duplicates become untagged).
    seen_tags = set()
    for b in eq_blocks:
        t = b.get("_tag")
        if t and t in seen_tags:
            b["_tag"] = None
            b["tag"] = None
        elif t:
            seen_tags.add(t)

    mineru_match = match_mineru(eq_blocks, mineru_eqs)
    engines = _mineru_engines(cfg)

    for i, b in enumerate(eq_blocks):
        crop_path = os.path.join(assets, b["_crop"]) if b.get("_crop") else None
        cands = []
        if b.get("latex"):
            cands.append({"engine": "marker", "latex": b["latex"]})
        mlatex = b.get("_forced_mineru") or mineru_match[i]
        if mlatex:
            cands.append({"engine": "mineru", "latex": mlatex})
        # crop is always passed; verify computes render-diff only when there is no
        # born-digital ground truth (Part II vector equations) or when configured.
        dec = ENS.decide(cands, b["_gt"], crop_path, cfg)
        # also self-correct when NO engine produced a candidate (Marker emitted an
        # empty/MathML equation and MinerU missed it): the VLM reads the crop directly.
        if dec["status"] in ("needs_selfcorrect", "no_candidates"):
            priors = [{"engine": e["engine"], "latex": e.get("sanitized") or e.get("latex")}
                      for e in dec.get("evidence", [])]
            dec = SC.correct(b["_tag"], crop_path, b["_gt"], priors, cfg, engines)
        verdict = dec.get("verdict") or {}
        b["resolved"] = {
            "latex": dec.get("latex"),
            "status": dec.get("status"),
            "tag": b["_tag"],
            "eqid": b["_tag"] or f"{cid}-{i+1}",
            "katex_valid": verdict.get("valid", False),
            "crop_rel": b.get("_crop"),
            "evidence": dec.get("evidence"),
        }

    # 4. tables: reconcile marker html with region reconstructor
    conf_min = cfg.get("tables", {}).get("confidence_min", 0.45)
    try:
        recon = TB.reconstruct_all(pdf, conf_min)
    except Exception:
        recon = {}
    _assign_tables(blocks, doc, page_dims, recon, assets, conf_min)
    doc.close()

    # 5. assemble
    meta = {
        "manual": "EM 1110-2-1100 (Coastal Engineering Manual)",
        "part": m["part_roman"], "chapter": m["chapter"] or 0,
        "title": m.get("title") or base, "source_pdf": m["work_file"],
        "pages": m.get("pages") or len(page_dims), "revision": "Change 3 (incl. errata)",
        "equations_total": len(eq_blocks),
    }
    review = os.path.join(outdir, base + "_flagged.md")
    qa = os.path.join(outdir, base + ".qa.json")
    counts = ASM.assemble(blocks, meta, assets_rel, final, review, qa)
    # per-equation index sidecar: every equation with its LaTeX, status and image
    eq_index = []
    for i, b in enumerate(eq_blocks):
        r = b.get("resolved") or {}
        eq_index.append({"n": i + 1, "eqid": r.get("eqid"), "tag": r.get("tag"),
                         "status": r.get("status"), "verified": r.get("status") in ASM.ACCEPTED,
                         "latex": r.get("latex"), "page": b.get("page"),
                         "image": f"{assets_rel}/{b['_crop']}" if b.get("_crop") else None})
    json.dump(eq_index, open(os.path.join(outdir, base + ".equations.json"), "w", encoding="utf-8"), indent=2)
    print(f"  -> {final}  | eq {counts['equations_verified']}✓/"
          f"{counts['equations_flagged']}⚑  tables {counts['tables_gfm']}gfm/"
          f"{counts['tables_image']}img  figs {counts['figures']}", flush=True)
    return "done"


def _table_rowcount(html):
    """(rows-with-content, plain-text) for a marker table block's html."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html or "", "html.parser")
        t = soup.find("table")
        if not t:
            return 0, soup.get_text(" ", strip=True)
        rows = [tr for tr in t.find_all("tr") if tr.get_text(strip=True)]
        return len(rows), soup.get_text(" ", strip=True)
    except Exception:
        return 0, ""


def _assign_tables(blocks, doc, page_dims, recon, assets, conf_min):
    """Attach a table_render to each marker table block."""
    # map captions: nearest 'Table X-Y-Z' text to a table block
    for idx, b in enumerate(blocks):
        if b["type"] != "table":
            continue
        tid, title = None, ""
        for j in range(idx, max(-1, idx - 4), -1):
            t = blocks[j].get("text", "") or ""
            mm = re.search(r'Table\s+([IVXLC]+-\d+-\d+[a-z]?)\.?\s*(.*)', t)
            if mm:
                tid, title = mm.group(1), mm.group(2).strip()
                break
        marker_gfm = html_table_to_gfm(b.get("html"))
        r = recon.get(tid) if tid else None
        chosen = None
        if r and r.get("ok") and (not marker_gfm or r["confidence"] >= 0.6):
            chosen = r["gfm"]
        elif marker_gfm:
            chosen = marker_gfm
        elif r and r.get("gfm"):
            chosen = r["gfm"]
        if chosen:
            b["table_render"] = {"id": tid or "", "title": title, "gfm": chosen}
        else:
            # Marker sometimes mislabels a continuation header ("Example Problem X
            # (Continued)") or an empty block as a table. Only a GENUINE multi-row
            # table warrants an image fallback; otherwise emit the text (or drop).
            nrows, txt = _table_rowcount(b.get("html"))
            if nrows < 2:
                b["type"] = "text"
                b["text"] = txt
                b.pop("table_render", None)
                continue
            # image fallback from region or marker bbox
            rel = None
            try:
                if r and r.get("region") is not None:
                    pg = r["_page"]
                    pix = doc[pg].get_pixmap(matrix=fitz.Matrix(3, 3), clip=r["region"])
                else:
                    pg = min(b["page"], len(doc) - 1)
                    rect = scale_bbox(b["bbox"], page_dims, b["page"], doc[pg])
                    pix = doc[pg].get_pixmap(matrix=fitz.Matrix(3, 3), clip=rect)
                safe = re.sub(r'[^A-Za-z0-9_-]', '_', str(tid or f"p{b['page']}"))
                rel = f"table-{safe}.png"
                pix.save(os.path.join(assets, rel))
            except Exception:
                rel = None
            b["table_render"] = {"id": tid or "", "title": title, "image_rel": rel}


def build_index(out_dir, manifest):
    lines = ["# Coastal Engineering Manual (EM 1110-2-1100)",
             "", "Machine-converted Markdown — one file per chapter.", ""]
    parts = {}
    for m in manifest:
        if m["kind"] not in ("chapter", "glossary"):
            continue
        parts.setdefault(m["part_roman"], []).append(m)
    for part in sorted(parts.keys()):
        lines.append(f"## Part {part}")
        for m in sorted(parts[part], key=lambda r: r["chapter"] or 0):
            partnum = m['portfolio'].split('-')[-1] if m['portfolio'].startswith('Part') else None
            partdir = f"part-{partnum}" if partnum else "appendix"
            base = f"ch-{m['chapter']:02d}" if m['chapter'] else "appendix-a-glossary"
            rel = f"markdown/{partdir}/{base}.md"
            if os.path.exists(os.path.join(out_dir, rel)):
                lines.append(f"- [{part}-{m['chapter'] or 'A'}: {m.get('title','')}]({rel})")
        lines.append("")
    open(os.path.join(out_dir, "index.md"), "w", encoding="utf-8").write("\n".join(lines))


def build_qa_report(out_dir, manifest):
    rows = []
    tot = {"eq": 0, "eqv": 0, "eqf": 0, "tg": 0, "ti": 0, "fig": 0}
    for root, _, files in os.walk(os.path.join(out_dir, "markdown")):
        for fn in files:
            if fn.endswith(".qa.json"):
                try:
                    q = json.load(open(os.path.join(root, fn)))
                except Exception:
                    continue
                rows.append(q)
                tot["eq"] += q.get("equations_total", 0)
                tot["eqv"] += q.get("equations_verified", 0)
                tot["eqf"] += q.get("equations_flagged", 0)
                tot["tg"] += q.get("tables_gfm", 0)
                tot["ti"] += q.get("tables_image", 0)
                tot["fig"] += q.get("figures", 0)
    rows.sort(key=lambda q: (str(q.get("part")), q.get("chapter", 0)))
    L = ["# CEM Conversion — QA Report", "",
         f"Chapters converted: **{len(rows)}**", "",
         f"Equations: **{tot['eq']}** total — {tot['eqv']} machine-verified, "
         f"{tot['eqf']} flagged "
         f"({100*tot['eqv']/tot['eq']:.1f}% verified)" if tot["eq"] else "Equations: 0",
         "", f"Tables: {tot['tg']} GFM, {tot['ti']} image-fallback   |   "
         f"Figures: {tot['fig']}", "",
         "| Part-Ch | Title | Pages | Eq total | Verified | Flagged | "
         "Tables GFM | Tables img | Figs |",
         "|---|---|---|---|---|---|---|---|---|"]
    for q in rows:
        L.append(f"| {q.get('part')}-{q.get('chapter')} | {str(q.get('title',''))[:40]} | "
                 f"{q.get('pages')} | {q.get('equations_total',0)} | "
                 f"{q.get('equations_verified',0)} | {q.get('equations_flagged',0)} | "
                 f"{q.get('tables_gfm',0)} | {q.get('tables_image',0)} | {q.get('figures',0)} |")
    open(os.path.join(out_dir, "qa_report.md"), "w", encoding="utf-8").write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", type=int, default=os.cpu_count())
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    cfg = load_cfg(a.out)
    os.environ.setdefault("CEM_NODE", os.environ.get("CEM_NODE", "node"))

    man_path = os.path.join(a.out, "manifest.json")
    if not os.path.exists(man_path):
        import extract
        extract.main(a.src, a.out)
    manifest = json.load(open(man_path))
    only = set(x.strip() for x in a.only.split(",") if x.strip())
    src_chapters = os.path.join(a.out, "chapters")
    chapters = [m for m in manifest if m["kind"] in ("chapter", "glossary")]
    done = errs = 0
    for m in chapters:
        cid = f"{m['part_roman']}-{m['chapter']}" if m['chapter'] else m['part_roman']
        if only and cid not in only:
            continue
        try:
            r = process_chapter(m, src_chapters, a.out, cfg, a.force)
            if r == "done":
                done += 1
                m["status"] = "done"
        except Exception as e:
            errs += 1
            m["status"] = f"error: {e}"
            print(f"!!! {cid} ERROR: {e}")
            traceback.print_exc()
        json.dump(manifest, open(man_path, "w"), indent=2)
    build_index(a.out, manifest)
    build_qa_report(a.out, manifest)
    try:
        import gallery
        gallery.build(a.out)
    except Exception as e:
        print(f"  gallery build skipped: {e}")
    print(f"DONE  ({done} converted, {errs} errors)")


if __name__ == "__main__":
    main()
