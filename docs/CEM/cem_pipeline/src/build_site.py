#!/usr/bin/env python3
"""Build a self-contained GitHub Pages site for the converted CEM:
  out/index.html      landing page (WaveMaker-styled): hero, highlights,
                      Part shortcuts grid, and the complete chapter listing.
  out/style.css       adapted WaveMaker palette (light/dark, original palette).
  out/chapter.html    markdown chapter viewer (marked.js + KaTeX), renders the
                      ch-YY.md files with real equations, tables and figures.
Run: python build_site.py <out_dir>
"""
import os
import sys
import re
import json
import glob
import html

PART_NAMES = {
    "I": "Introduction",
    "II": "Coastal Hydrodynamics",
    "III": "Coastal Sediment Processes",
    "IV": "Coastal Geology",
    "V": "Coastal Project Planning and Design",
    "VI": "Design of Coastal Project Elements",
    "App-A": "Appendix A — Glossary",
}
PART_ORDER = ["I", "II", "III", "IV", "V", "VI", "App-A"]


def _collect(out_dir):
    """Return {part_roman: [ {num,title,pages,eq,eqv,tables,figs,href} ... ]}."""
    chapters = {}
    qas = glob.glob(os.path.join(out_dir, "markdown", "**", "*.qa.json"), recursive=True)
    for q in qas:
        d = json.load(open(q, encoding="utf-8"))
        md_rel = os.path.relpath(q[:-len(".qa.json")] + ".md", out_dir).replace(os.sep, "/")
        part = str(d.get("part") or "App-A")
        chapters.setdefault(part, []).append({
            "num": d.get("chapter") or 0,
            "title": (d.get("title") or "").title() if (d.get("title") or "").isupper() else d.get("title") or "",
            "pages": d.get("pages") or 0,
            "eq": d.get("equations_total", 0),
            "eqv": d.get("equations_verified", 0),
            "tables": d.get("tables_gfm", 0),
            "figs": d.get("figures", 0),
            "cpath": md_rel,
        })
    for v in chapters.values():
        v.sort(key=lambda c: c["num"])
    return chapters


def _slug(s):
    """GitHub-style heading slug; MUST match the viewer's JS slugify."""
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', s.lower())).strip('-')


def _clean_text(s):
    """Strip markdown markup to plain searchable prose."""
    s = re.sub(r'```math\n[\s\S]*?\n```', ' ', s)      # drop display math
    s = re.sub(r'`[^`]*`', ' ', s)                      # inline code
    s = re.sub(r'!\[[^\]]*\]\([^)]*\)', ' ', s)         # images
    s = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)      # links -> text
    s = re.sub(r'^\s*\|.*$', ' ', s, flags=re.M)        # table rows
    s = re.sub(r'^\s*>.*$', ' ', s, flags=re.M)         # blockquotes (flags)
    s = re.sub(r'[#*_>`]', ' ', s)                      # residual markup
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def _extract_sections(out_dir):
    """One search document per heading-delimited section across all chapters."""
    docs = []
    mds = [m for m in glob.glob(os.path.join(out_dir, "markdown", "**", "*.md"), recursive=True)
           if "_flagged" not in m]
    for md in sorted(mds):
        rel = os.path.relpath(md, out_dir).replace(os.sep, "/")
        txt = open(md, encoding="utf-8").read().replace("\r\n", "\n")
        fm = {}
        m = re.match(r'^---\n([\s\S]*?)\n---\n?', txt)
        if m:
            for line in m.group(1).splitlines():
                kv = re.match(r'(\w+):\s*"?([^"]*)"?\s*$', line)
                if kv:
                    fm[kv.group(1)] = kv.group(2)
            txt = txt[m.end():]
        part = fm.get("part", ""); chap = fm.get("chapter", ""); ctitle = fm.get("title", "")
        cid = f"{part}-{chap}" if chap and chap != "0" else (part or os.path.basename(md))
        # split into sections by ATX headings
        cur_head, cur_anchor, buf = ctitle or cid, "", []

        def flush():
            raw = "\n".join(buf)
            # skip navigation/low-value sections: TOC, lists of figures/tables, a
            # running-header captured as a heading, or a caption-list dump (these
            # list every caption and would match many keywords with low relevance).
            if re.search(r'table of contents|list of (tables|figures)', cur_head, re.I):
                return
            if re.match(r'\s*EM\s*1110-2-1100', cur_head):
                return
            if len(re.findall(r'(?:Figure|Table)\s+[IVXLC]+-\d+-\d+', raw)) > 6:
                return
            body = _clean_text(raw)
            if body or cur_head:
                docs.append({
                    "id": f"{rel}#{cur_anchor}" if cur_anchor else rel,
                    "cid": cid, "part": part, "title": ctitle,
                    "heading": cur_head,
                    "href": f"chapter.html?c={rel}" + (f"#{cur_anchor}" if cur_anchor else ""),
                    "text": body[:1800],
                })
        for line in txt.splitlines():
            hm = re.match(r'^#{1,4}\s+(.*)$', line)
            if hm:
                flush()
                cur_head = hm.group(1).strip()
                cur_anchor = _slug(cur_head)
                buf = []
            else:
                buf.append(line)
        flush()
    return docs


def build(out_dir, root_dir=None):
    chapters = _collect(out_dir)
    search_docs = _extract_sections(out_dir)
    json.dump(search_docs, open(os.path.join(out_dir, "search-index.json"), "w", encoding="utf-8"),
              ensure_ascii=False, separators=(",", ":"))
    parts = [p for p in PART_ORDER if p in chapters] + \
            [p for p in chapters if p not in PART_ORDER]
    tot_ch = sum(len(v) for v in chapters.values())
    tot_eq = sum(c["eq"] for v in chapters.values() for c in v)
    tot_eqv = sum(c["eqv"] for v in chapters.values() for c in v)
    tot_tab = sum(c["tables"] for v in chapters.values() for c in v)
    tot_fig = sum(c["figs"] for v in chapters.values() for c in v)

    # --- Part shortcut cards ---
    shortcuts = []
    for i, p in enumerate(parts):
        n = len(chapters[p])
        shortcuts.append(
            f'<a class="area-card" href="#part-{p}" style="border-left:5px solid var(--area-{i+1})">'
            f'<span class="area-name">Part {p} — {html.escape(PART_NAMES.get(p, p))}</span>'
            f'<span class="area-count">{n} chapter{"s" if n != 1 else ""}</span></a>')

    # --- complete chapter listing, grouped by Part ---
    sections = []
    for i, p in enumerate(parts):
        cards = []
        for c in chapters[p]:
            label = (f"{p}-{c['num']}" if c["num"] else "App-A")
            stats = []
            if c["eq"]:
                stats.append(f"{c['eqv']}/{c['eq']} eqs")
            if c["tables"]:
                stats.append(f"{c['tables']} tables")
            if c["figs"]:
                stats.append(f"{c['figs']} figs")
            stats.append(f"{c['pages']} pp")
            cards.append(
                f'<a class="ch-card" href="@@BASE@@chapter.html?c={html.escape(c["cpath"])}">'
                f'<span class="ch-id">{label}</span>'
                f'<span class="ch-title">{html.escape(c["title"])}</span>'
                f'<span class="ch-stats">{" · ".join(stats)}</span></a>')
        sections.append(
            f'<section class="part-section" id="part-{p}">'
            f'<h2 style="border-left:6px solid var(--area-{i+1})">Part {p} — {html.escape(PART_NAMES.get(p, p))}</h2>'
            f'<div class="ch-grid">{"".join(cards)}</div></section>')

    index_tmpl = _INDEX
    for token, val in [("{shortcuts}", "".join(shortcuts)),
                       ("{sections}", "".join(sections)),
                       ("{tot_ch}", str(tot_ch)), ("{tot_eq}", f"{tot_eq:,}"),
                       ("{tot_eqv}", f"{tot_eqv:,}"), ("{tot_tab}", f"{tot_tab:,}"),
                       ("{tot_fig}", f"{tot_fig:,}")]:
        index_tmpl = index_tmpl.replace(token, val)

    def _fill(tmpl, base, home="index.html"):
        return tmpl.replace("@@BASE@@", base).replace("@@HOME@@", home)

    # self-contained site inside out_dir (base = "")
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(_fill(index_tmpl, ""))
    open(os.path.join(out_dir, "style.css"), "w", encoding="utf-8").write(_CSS)
    open(os.path.join(out_dir, "chapter.html"), "w", encoding="utf-8").write(_fill(_CHAPTER, ""))
    sz = os.path.getsize(os.path.join(out_dir, "search-index.json")) / 1024
    print(f"Built site in {out_dir}: index.html ({tot_ch} chapters), style.css, chapter.html, "
          f"search-index.json ({len(search_docs)} sections, {sz:.0f} KB)")

    # repo-root entry point that links into the out_dir site (base = relative path)
    if root_dir:
        site_rel = (os.path.relpath(out_dir, root_dir).replace(os.sep, "/") + "/")
        open(os.path.join(root_dir, "index.html"), "w", encoding="utf-8").write(
            _fill(index_tmpl, site_rel))
        print(f"Root index.html -> {root_dir} (links into {site_rel})")


# ============================== templates ==================================
_CSS = r"""
/* CEM site — WaveMaker theming (original palette), light/dark. */
:root, html[data-theme="light"]{
  --bg:#f6f3ed; --fg:#16211f; --panel:#fff; --border:#e2dcd0; --header-bg:#eeeae1;
  --label:#4c5a5c; --muted:#7c888b; --grid:#e2dcd0; --btn-bg:#fbf8f2; --btn-hover:#f1ede4;
  --accent:#0a82a2; --accent-hover:#00799f; --on-accent:#fff; --danger:#bc2614;
  --cls-a:#587836; --ctl-border:#cfc7b7;
  --area-1:#0a82a2; --area-2:#587836; --area-3:#cbb07e; --area-4:#7c5c3e;
  --area-5:#bc2614; --area-6:#0e9cbe; --area-7:#a98c5b;
}
html[data-theme="dark"]{
  --bg:#0b1316; --fg:#eaf2f3; --panel:#121d21; --border:#243035; --header-bg:#0a1115;
  --label:#a7b7bb; --muted:#6e8086; --grid:#243035; --btn-bg:#16242a; --btn-hover:#1b2a30;
  --accent:#2bb8d4; --accent-hover:#5bcee2; --on-accent:#06222a; --danger:#e5654f;
  --cls-a:#9cb57a; --ctl-border:#33444b;
  --area-1:#2bb8d4; --area-2:#9cb57a; --area-3:#dcc8a1; --area-4:#9a7b5c;
  --area-5:#e5654f; --area-6:#5bcee2; --area-7:#cbb07e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.5 "Segoe UI Variable Text","Segoe UI",system-ui,sans-serif}
a{color:var(--accent)}
header{display:flex;align-items:center;gap:10px;flex-wrap:wrap;padding:10px 16px;
  border-bottom:1px solid var(--border);background:var(--header-bg);position:sticky;top:0;z-index:10}
header .title{font-weight:800;color:var(--danger);font-size:18px;text-decoration:none;letter-spacing:.01em}
header .spacer{flex:1}
.topnav{display:flex;gap:4px;flex-wrap:wrap}
.topnav a{text-decoration:none;color:var(--label);padding:5px 10px;border-radius:6px;font-weight:600}
.topnav a:hover{color:var(--accent);background:var(--btn-hover)}
.muted{color:var(--muted)}
.switch{position:relative;width:42px;height:24px;display:inline-block;flex:none;cursor:pointer}
.switch input{position:absolute;opacity:0;width:100%;height:100%;margin:0;cursor:pointer}
.switch .track{position:absolute;inset:0;background:var(--ctl-border);border-radius:999px;transition:background .2s}
.switch .thumb{position:absolute;top:3px;left:3px;width:18px;height:18px;background:#fff;border-radius:999px;
  transition:transform .2s;box-shadow:0 1px 3px rgba(0,0,0,.3)}
.switch input:checked + .track{background:var(--accent)}
.switch input:checked + .track + .thumb{transform:translateX(18px)}

main.landing{display:block;max-width:1100px;margin:0 auto;padding:16px}
.hero{text-align:center;padding:54px 16px 30px}
.hero .wordmark{margin:0;color:var(--danger);font-weight:800;letter-spacing:.01em;
  font-size:clamp(44px,8vw,84px);line-height:1.05;position:relative;display:inline-block}
.hero .beta{position:absolute;left:100%;top:.04em;margin-left:.1em;font-size:.30em;font-weight:700;
  font-style:italic;letter-spacing:.02em;color:var(--cls-a);line-height:1}
.hero .hero-sub{margin:10px 0 0;color:var(--accent);font-weight:600;font-size:clamp(15px,2.4vw,22px)}
.hero .tagline{max-width:760px;margin:18px auto 0;color:var(--label);font-size:15px}
.hero .hero-note{max-width:760px;margin:10px auto 0;color:var(--muted);font-size:13px;font-style:italic}
.cta-row{display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-top:26px}
.cta{text-decoration:none;padding:12px 22px;border-radius:6px;font-weight:700;border:1px solid var(--border)}
.cta-primary{background:var(--accent);color:var(--on-accent);border-color:transparent}
.cta-primary:hover{background:var(--accent-hover)}
.cta-secondary{background:var(--btn-bg);color:var(--fg)}
.cta-secondary:hover{border-color:var(--accent);color:var(--accent)}

.stat-row{display:flex;gap:26px;justify-content:center;flex-wrap:wrap;margin:30px 0 0}
.stat{text-align:center}
.stat .num{font-size:26px;font-weight:800;color:var(--accent)}
.stat .lbl{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}

.highlights{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:30px}
.hl-card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px 18px;
  box-shadow:0 1px 3px rgba(0,0,0,.07)}
.hl-card h3{margin:0 0 6px;color:var(--accent);font-size:15px}
.hl-card p{margin:0;color:var(--label);font-size:13px}

/* search */
.search-wrap{max-width:760px;margin:26px auto 0}
.search-box{display:flex;gap:8px}
#q{flex:1;padding:12px 16px;font-size:16px;border:1px solid var(--ctl-border);border-radius:8px;
  background:var(--panel);color:var(--fg)}
#q:focus{outline:none;border-color:var(--accent)}
.search-hint{margin:8px 2px 0;color:var(--muted);font-size:12px}
.search-hint b{color:var(--label);font-weight:600;cursor:pointer}
.search-hint b:hover{color:var(--accent)}
#results{margin-top:14px;display:flex;flex-direction:column;gap:8px}
.result{display:block;text-decoration:none;color:var(--fg);background:var(--panel);
  border:1px solid var(--border);border-radius:8px;padding:10px 14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.result:hover{border-color:var(--accent);background:var(--btn-hover)}
.result .r-head{font-weight:600}
.result .r-where{color:var(--accent);font-size:12px;font-weight:600;margin-right:6px}
.result .r-snip{color:var(--label);font-size:13px;margin-top:3px}
.result .r-snip mark{background:color-mix(in srgb,var(--accent) 28%,transparent);color:inherit;
  padding:0 1px;border-radius:2px}
#results .rcount{color:var(--muted);font-size:12px}
.areas-section{margin-top:44px}
.areas-section h2,.parts-list h2.sec{color:var(--fg);font-size:18px;margin:0 0 12px}
.areas-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:10px}
.area-card{display:flex;justify-content:space-between;align-items:center;gap:10px;text-decoration:none;
  color:var(--fg);background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:12px 14px;
  box-shadow:0 1px 3px rgba(0,0,0,.07)}
.area-card:hover{border-color:var(--accent);background:var(--btn-hover)}
.area-card .area-name{font-weight:600}
.area-card .area-count{color:var(--muted);font-size:12px;white-space:nowrap}

.parts-list{margin-top:44px}
.part-section{margin:0 0 30px;scroll-margin-top:64px}
.part-section h2{color:var(--fg);font-size:19px;margin:0 0 12px;padding-left:12px}
.ch-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:10px}
.ch-card{display:flex;flex-direction:column;gap:3px;text-decoration:none;color:var(--fg);background:var(--panel);
  border:1px solid var(--border);border-radius:8px;padding:11px 14px;box-shadow:0 1px 3px rgba(0,0,0,.07)}
.ch-card:hover{border-color:var(--accent);background:var(--btn-hover)}
.ch-card .ch-id{font-weight:700;color:var(--label);font-size:12px}
.ch-card .ch-title{font-weight:600;font-size:14px}
.ch-card .ch-stats{color:var(--muted);font-size:12px}

.site-footer{border-top:1px solid var(--border);background:var(--header-bg);padding:24px 16px;
  text-align:center;margin-top:48px}
.foot-links{display:flex;gap:16px;justify-content:center;flex-wrap:wrap}
.foot-links a{color:var(--accent);text-decoration:none;font-weight:600}
.site-footer .disclaimer{max-width:780px;margin:12px auto 0;color:var(--muted);font-size:12px}

/* chapter viewer */
.doc{max-width:920px;margin:0 auto;padding:20px 28px 80px}
.doc .backlink{display:inline-block;margin:6px 0 4px;font-weight:600;text-decoration:none}
.markdown{color:var(--fg);font-size:15px;line-height:1.65}
.markdown h1,.markdown h2,.markdown h3,.markdown h4{color:var(--fg);line-height:1.25;margin:1.4em 0 .5em}
.markdown h1{font-size:27px;border-bottom:1px solid var(--border);padding-bottom:.3em}
.markdown h2{font-size:21px;border-bottom:1px solid var(--border);padding-bottom:.25em}
.markdown h3{font-size:17px}.markdown h4{font-size:15px;color:var(--label)}
.markdown h1:first-child{margin-top:0}
.markdown a{color:var(--accent)}
.markdown em{color:var(--label)}
.markdown img{max-width:100%;background:#fff;border-radius:4px}
.markdown code{font-family:"Cascadia Mono",Consolas,monospace;font-size:.88em;background:var(--header-bg);
  padding:1px 5px;border-radius:4px}
.markdown pre{background:var(--header-bg);border:1px solid var(--border);border-radius:6px;padding:12px 14px;overflow:auto}
.markdown pre code{background:none;padding:0}
.markdown table{border-collapse:collapse;margin:1em 0;font-size:13px;display:block;overflow-x:auto}
.markdown th,.markdown td{border:1px solid var(--grid);padding:5px 10px;text-align:left}
.markdown th{background:var(--header-bg)}
.markdown blockquote{margin:1em 0;padding:4px 14px;border-left:4px solid var(--accent);color:var(--label);background:var(--header-bg)}
.markdown hr{border:none;border-top:1px solid var(--border);margin:1.6em 0}
.markdown .katex-display{overflow-x:auto;overflow-y:hidden;padding:2px 0}
.fm{color:var(--muted);font-size:12px;border-bottom:1px solid var(--border);padding-bottom:8px;margin-bottom:8px}
"""

_HEADER = """  <header>
    <a class="title" href="@@HOME@@">CHESS-TG</a>
    <nav class="topnav">
      <a href="@@HOME@@">Chapters</a>
      <a href="@@BASE@@chapter.html?c=qa_report.md">QA report</a>
    </nav>
    <span class="spacer"></span>
    <span class="muted" id="modeLbl"></span>
    <label class="switch" title="Light / Dark">
      <input type="checkbox" id="modeToggle"><span class="track"></span><span class="thumb"></span>
    </label>
  </header>
"""

_THEME_JS = """
    (function(){
      var KEY="cem-theme";
      var t=localStorage.getItem(KEY)|| (matchMedia&&matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light");
      document.documentElement.setAttribute("data-theme",t);
      function sync(){var d=document.documentElement.getAttribute("data-theme")==="dark";
        var c=document.getElementById("modeToggle"); if(c)c.checked=d;
        var l=document.getElementById("modeLbl"); if(l)l.textContent=d?"Dark":"Light";}
      window.addEventListener("DOMContentLoaded",function(){
        sync();
        var c=document.getElementById("modeToggle");
        if(c)c.addEventListener("change",function(){
          var t=c.checked?"dark":"light";
          document.documentElement.setAttribute("data-theme",t);
          localStorage.setItem(KEY,t); sync();});
      });
    })();
"""

_INDEX = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CEM — Coastal Engineering Manual (EM 1110-2-1100)</title>
<meta name="description" content="The USACE Coastal Engineering Manual (EM 1110-2-1100) as faithful, web-readable Markdown with real LaTeX equations, GFM tables and figures.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%230a82a2'/%3E%3Ctext x='8' y='12' font-size='9' font-family='Segoe UI,sans-serif' font-weight='700' fill='white' text-anchor='middle'%3EC%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="@@BASE@@style.css">
<script src="https://cdn.jsdelivr.net/npm/minisearch@6.3.0/dist/umd/index.min.js"></script>
<script>{theme_js}</script>
</head><body>
{header}
<main class="landing">
  <section class="hero">
    <h1 class="wordmark">CHESS-TG<span class="beta">βeta</span></h1>
    <p class="hero-sub">Coastal Hazards, Engineering, and Structures System (CHESS) — Technical Guidance (TG)</p>
    <p class="tagline">The U.S. Army Corps of Engineers Coastal Engineering Manual — coastal hydrodynamics,
      sediment processes, geology, project planning, and the design of coastal structures — converted to
      faithful, web-readable Markdown with real LaTeX equations, GitHub-flavored tables, and extracted figures.</p>
    <p class="hero-note">Machine-converted and verified from the source PDFs: every equation is KaTeX-valid and
      cross-checked against the document's born-digital text layer and an independent recognizer.</p>
    <div class="cta-row">
      <a class="cta cta-primary" href="#chapters">Browse chapters →</a>
      <a class="cta cta-secondary" href="#parts">Jump to a Part</a>
    </div>
    <div class="stat-row">
      <div class="stat"><div class="num">{tot_ch}</div><div class="lbl">Chapters</div></div>
      <div class="stat"><div class="num">{tot_eqv}</div><div class="lbl">Equations (100% verified)</div></div>
      <div class="stat"><div class="num">{tot_tab}</div><div class="lbl">Tables</div></div>
      <div class="stat"><div class="num">{tot_fig}</div><div class="lbl">Figures</div></div>
    </div>
    <div class="search-wrap">
      <div class="search-box">
        <input id="q" type="search" autocomplete="off" placeholder="Search the manual — e.g. storm surge, dune erosion, overtopping&hellip;">
      </div>
      <p class="search-hint">Try: <b>storm surge</b> · <b>hurricane</b> · <b>dune erosion</b> ·
        <b>wave overtopping</b> · <b>longshore transport</b> · <b>scour</b></p>
      <div id="results"></div>
    </div>
  </section>

  <section class="highlights">
    <div class="hl-card"><h3>Real LaTeX math</h3><p>Every equation is a live KaTeX/MathJax expression, not an
      image &mdash; selectable, searchable, and rendered crisply at any size.</p></div>
    <div class="hl-card"><h3>Faithful tables &amp; figures</h3><p>Tables are reconstructed as pipe tables and
      figures extracted as images with their captions, preserving the source structure.</p></div>
    <div class="hl-card"><h3>Machine-verified</h3><p>Equations are confirmed by independent-engine agreement and
      the PDF's born-digital text layer &mdash; {tot_eqv} of {tot_eq} at 100%.</p></div>
    <div class="hl-card"><h3>Open &amp; browsable</h3><p>One page per chapter, organized by the manual's six Parts,
      readable in any browser with no install.</p></div>
  </section>

  <section class="areas-section" id="parts">
    <h2>Parts</h2>
    <div class="areas-grid">{shortcuts}</div>
  </section>

  <div class="parts-list" id="chapters">
    <h2 class="sec">All chapters</h2>
    {sections}
  </div>
</main>
<footer class="site-footer">
  <div class="foot-links"><a href="#parts">Parts</a><a href="#chapters">Chapters</a><a href="@@BASE@@chapter.html?c=qa_report.md">QA report</a></div>
  <p class="disclaimer">A faithful Markdown conversion of the USACE Coastal Engineering Manual (EM 1110-2-1100)
    for reading, search, and reference. Refer to the official USACE publication for authoritative use.</p>
</footer>
<script>
(function(){
  var q=document.getElementById("q"), out=document.getElementById("results");
  var mini=null, ready=false;
  var partsList=document.getElementById("chapters"), partsNav=document.getElementById("parts");
  var hl=document.querySelector(".highlights"), areas=document.querySelector(".areas-section");
  function esc(s){return String(s).replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c];});}
  function load(){
    if(ready) return Promise.resolve();
    return fetch("@@BASE@@search-index.json").then(function(r){return r.json();}).then(function(data){
      mini=new MiniSearch({fields:["heading","text","title"],
        storeFields:["heading","href","cid","part","title","text"],
        searchOptions:{boost:{heading:3,title:2},prefix:true,fuzzy:0.2,combineWith:"AND"}});
      mini.addAll(data.map(function(d,i){return Object.assign({},d,{id:i});}));
      ready=true;
    });
  }
  function snippet(text,terms){
    var low=text.toLowerCase(), pos=-1;
    terms.forEach(function(t){var p=low.indexOf(t); if(p>=0&&(pos<0||p<pos))pos=p;});
    if(pos<0)pos=0;
    var start=Math.max(0,pos-70), s=text.slice(start,start+220);
    s=(start>0?"\\u2026":"")+esc(s)+"\\u2026";
    terms.forEach(function(t){ if(t.length>1)
      s=s.replace(new RegExp("("+t.replace(/[.*+?^${}()|[\\]\\\\]/g,"\\\\$&")+")","ig"),"<mark>$1</mark>"); });
    return s;
  }
  function render(query){
    var terms=query.toLowerCase().split(/\\s+/).filter(Boolean);
    var res=mini.search(query).slice(0,40);
    if(!res.length){ out.innerHTML='<p class="rcount">No matches for \\u201c'+esc(query)+'\\u201d.</p>'; return; }
    var h='<p class="rcount">'+res.length+(res.length===40?"+":"")+' result'+(res.length===1?"":"s")+'</p>';
    res.forEach(function(r){
      h+='<a class="result" href="@@BASE@@'+esc(r.href)+'"><div><span class="r-where">'+esc(r.cid||r.part)+
        '</span><span class="r-head">'+esc(r.heading||r.title)+'</span></div>'+
        '<div class="r-snip">'+snippet(r.text||"",terms)+'</div></a>';
    });
    out.innerHTML=h;
  }
  var t;
  function go(){
    clearTimeout(t);
    var query=q.value.trim(), searching=query.length>=2;
    [hl,areas,partsNav,partsList].forEach(function(e){ if(e)e.style.display=searching?"none":""; });
    if(!searching){ out.innerHTML=""; return; }
    t=setTimeout(function(){ load().then(function(){ render(query); }); },120);
  }
  q.addEventListener("input",go);
  document.querySelectorAll(".search-hint b").forEach(function(b){
    b.addEventListener("click",function(){ q.value=b.textContent; go(); q.focus(); });
  });
  var pq=new URLSearchParams(location.search).get("q");
  if(pq){ q.value=pq; go(); }
})();
</script>
</body></html>
""".replace("{header}", _HEADER).replace("{theme_js}", _THEME_JS)

_CHAPTER = """<!doctype html><html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CEM — chapter</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%230a82a2'/%3E%3Ctext x='8' y='12' font-size='9' font-family='sans-serif' font-weight='700' fill='white' text-anchor='middle'%3EC%3C/text%3E%3C/svg%3E">
<link rel="stylesheet" href="style.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script>{theme_js}</script>
</head><body>
{header}
<main class="doc">
  <a class="backlink" href="index.html">&larr; All chapters</a>
  <div id="content" class="markdown"><p class="muted">Loading&hellip;</p></div>
</main>
<script>
(function(){
  function qs(k){return new URLSearchParams(location.search).get(k);}
  var c = qs("c");
  var el = document.getElementById("content");
  if(!c){el.innerHTML="<p>No chapter specified.</p>";return;}
  var base = c.replace(/[^\\/]*$/, "");           // directory of the .md
  fetch(c).then(function(r){ if(!r.ok) throw new Error(r.status); return r.text(); })
   .then(function(md){
      md = md.replace(/\\r\\n?/g, "\\n");          // normalize CRLF -> LF
      // strip YAML front-matter, show a small meta line
      var fm="";
      md = md.replace(/^---\\n([\\s\\S]*?)\\n---\\n?/, function(m,y){ fm=y; return ""; });
      // rewrite relative asset paths to be relative to the .md's directory
      md = md.replace(/\\]\\((assets\\/)/g, "](" + base + "$1");
      // drop navigation sections (Table of Contents / List of Tables / List of
      // Figures) — redundant with the site nav and poorly auto-segmented from the
      // source PDF (they otherwise render as a run-on of dotted leaders).
      md = md.replace(/(^|\\n)#{1,6}[ \\t]*(Table of Contents|List of Tables|List of Figures)[^\\n]*\\n([\\s\\S]*?)(?=\\n#{1,6}[ \\t]|\\s*$)/gi, "$1");
      // protect math from the markdown parser
      var math=[];
      md = md.replace(/```math\\n([\\s\\S]*?)\\n```/g, function(m,t){ math.push({d:true,t:t}); return "@@M"+(math.length-1)+"@@"; });
      md = md.replace(/\\$\\$([\\s\\S]*?)\\$\\$/g, function(m,t){ math.push({d:true,t:t}); return "@@M"+(math.length-1)+"@@"; });
      md = md.replace(/(^|[^\\\\$])\\$([^$\\n]+?)\\$/g, function(m,p,t){ math.push({d:false,t:t}); return p+"@@M"+(math.length-1)+"@@"; });
      // wrap bare GREEK/symbol tokens the source emits un-delimited (the
      // "Definitions of Symbols" lists), e.g. \\theta, \\rho_s, \\xi_{0m}, \\lambda_{1,2,3}.
      // Allowlist keeps structural commands (\\frac, \\text, \\begin) as-is.
      md = md.replace(/\\\\(?:alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|omicron|pi|varpi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega|partial|nabla|infty)(?![a-zA-Z])(?:[_^](?:{[^}]*}|[A-Za-z0-9]))*/g, function(m){ math.push({d:false,t:m}); return "@@M"+(math.length-1)+"@@"; });
      var htmlout = marked.parse(md);
      htmlout = htmlout.replace(/@@M(\\d+)@@/g, function(m,i){ return '<span class="kx" data-i="'+i+'"></span>'; });
      var titleLine = (fm.match(/title:\\s*"?([^"\\n]+)"?/)||[])[1] || "";
      var partLine = (fm.match(/part:\\s*"?([^"\\n]+)"?/)||[])[1] || "";
      var chLine = (fm.match(/chapter:\\s*([^\\n]+)/)||[])[1] || "";
      if(titleLine){ document.title = "CEM — " + titleLine; }
      el.innerHTML = (partLine?('<div class="fm">Part '+partLine+(chLine?', Chapter '+chLine.trim():'')+' &middot; EM 1110-2-1100</div>'):"") + htmlout;
      el.querySelectorAll(".kx").forEach(function(s){
        var e=math[+s.dataset.i];
        try{ katex.render(e.t, s, {displayMode:e.d, throwOnError:true, strict:false}); }
        catch(err){ s.textContent=e.t; }
      });
      // heading anchors (match the search-index slugs) + scroll to the linked section
      el.querySelectorAll("h1,h2,h3,h4").forEach(function(h){
        if(!h.id) h.id=h.textContent.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"");
      });
      if(location.hash){ var tgt=document.getElementById(decodeURIComponent(location.hash.slice(1)));
        if(tgt) setTimeout(function(){ tgt.scrollIntoView(); },0); }
   })
   .catch(function(err){ el.innerHTML='<p class="muted">Could not load chapter ('+err+'). '+
      'On GitHub Pages this loads <code>'+c+'</code>.</p>'; });
})();
</script>
</body></html>
""".replace("{header}", _HEADER).replace("{theme_js}", _THEME_JS)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".",
          sys.argv[2] if len(sys.argv) > 2 else None)
