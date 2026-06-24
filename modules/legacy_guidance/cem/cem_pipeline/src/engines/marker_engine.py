#!/usr/bin/env python3
"""Marker engine adapter (spec §7.3).

Runs marker-pdf once with the JSON renderer to obtain a block tree with
reading order, block types, bboxes, per-equation LaTeX, table HTML, and figure
images. Normalizes everything to the common block schema used by assemble.py.

Normalized block:
  {type, page, bbox, level?, text?, latex?, html?, image_rel?, tag?}
where type in {heading,text,equation,table,figure,caption,list}.
"""
import os
import re
import io
import base64

_MODELS = None          # marker artifact dict (load once per process)


def _load_models():
    global _MODELS
    if _MODELS is None:
        from marker.models import create_model_dict
        _MODELS = create_model_dict()
    return _MODELS


def _converter(output_format="json", use_llm=False, extra=None):
    from marker.converters.pdf import PdfConverter
    from marker.config.parser import ConfigParser
    cfg = {"output_format": output_format, "disable_image_extraction": False}
    if use_llm:
        cfg["use_llm"] = True
    if extra:
        cfg.update(extra)
    parser = ConfigParser(cfg)
    return PdfConverter(
        config=parser.generate_config_dict(),
        artifact_dict=_load_models(),
        processor_list=parser.get_processors(),
        renderer=parser.get_renderer(),
        llm_service=parser.get_llm_service() if use_llm else None,
    )


_PAGE_RE = re.compile(r'/page/(\d+)/')
_TAG_RE = re.compile(r'\(([IVXLC]+-\d+-\d+[a-z]?)\)')


def _page_of(block_id):
    m = _PAGE_RE.search(block_id or "")
    return int(m.group(1)) if m else 0


def _bbox(b):
    bb = getattr(b, "bbox", None)
    if bb and len(bb) == 4:
        return [float(x) for x in bb]
    poly = getattr(b, "polygon", None)
    if poly:
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return [min(xs), min(ys), max(xs), max(ys)]
    return None


def _strip_tags(html):
    if not html:
        return ""
    t = re.sub(r'<[^>]+>', ' ', html)
    t = (t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
          .replace('&nbsp;', ' ').replace('&#39;', "'").replace('&quot;', '"'))
    return re.sub(r'[ \t]+', ' ', t).strip()


def _extract_latex(html):
    """Pull LaTeX from a marker Equation block's html."""
    if not html:
        return None
    # MathML? marker emits LaTeX by default, but guard.
    if re.search(r'<m(row|i|o|n|frac|sqrt)\b', html):
        # MathML -> we can't trust a clean latex; let other engines/crop decide
        inner = _strip_tags(html)
        return inner or None
    # $$...$$ or \[...\]
    for pat in (r'\$\$(.+?)\$\$', r'\\\[(.+?)\\\]', r'\\\((.+?)\\\)', r'\$(.+?)\$'):
        m = re.search(pat, html, re.S)
        if m:
            return m.group(1).strip()
    # <math ...>latex</math> (marker latex-in-mathtag)
    m = re.search(r'<math[^>]*>(.+?)</math>', html, re.S)
    if m and not re.search(r'<m(row|i|o)\b', m.group(1)):
        return _strip_tags(m.group(1)).strip()
    txt = _strip_tags(html)
    return txt if ('\\' in txt or '^' in txt or '_' in txt) else txt or None


def _heading_level(b):
    ht = getattr(b, "block_type", "")
    # marker SectionHeader may carry a heading level in html <h1>..<h6>
    html = getattr(b, "html", "") or ""
    m = re.search(r'<h([1-6])', html)
    if m:
        return int(m.group(1))
    sh = getattr(b, "section_hierarchy", None)
    if isinstance(sh, dict) and sh:
        try:
            return min(6, max(1, max(int(k) for k in sh.keys())))
        except Exception:
            pass
    return 2


def _iter_blocks(node):
    """Depth-first leaf-ish traversal preserving reading order."""
    children = getattr(node, "children", None)
    btype = getattr(node, "block_type", "")
    # containers we descend into rather than emit
    CONTAINERS = {"Page", "Document", "ListGroup", "TableGroup", "FigureGroup",
                  "PictureGroup", "ListItem"}
    if children and (btype in CONTAINERS or btype == ""):
        for c in children:
            yield from _iter_blocks(c)
    else:
        yield node
        # some emit-blocks still have children (e.g. captions inside figures)
        if children and btype in ("Figure", "Picture", "Table"):
            for c in children:
                if getattr(c, "block_type", "") == "Caption":
                    yield c


def _save_images(b, assets_dir, counter):
    """Decode any base64 images on a block; return first saved relative path."""
    images = getattr(b, "images", None)
    if not images:
        return None
    from PIL import Image
    rel = None
    for name, data in images.items():
        try:
            raw = base64.b64decode(data) if isinstance(data, str) else data
            img = Image.open(io.BytesIO(raw))
            if img.width < 40 or img.height < 40:
                continue
            counter[0] += 1
            fn = f"marker-img-{counter[0]:03d}.png"
            img.convert("RGB").save(os.path.join(assets_dir, fn))
            if rel is None:
                rel = fn
        except Exception:
            continue
    return rel


def _page_dims(rendered):
    """Marker page pixel dimensions per page index (for bbox->PDF scaling)."""
    dims = {}
    for pg in getattr(rendered, "children", None) or []:
        pid = _page_of(getattr(pg, "id", "") or "")
        bb = _bbox(pg)
        if bb:
            dims[pid] = [bb[2] - bb[0], bb[3] - bb[1]]
    return dims


def convert(pdf_path, assets_dir, use_llm=False):
    os.makedirs(assets_dir, exist_ok=True)
    conv = _converter("json", use_llm=use_llm)
    rendered = conv(pdf_path)
    page_dims = _page_dims(rendered)
    blocks = []
    counter = [0]
    for b in _iter_blocks(rendered):
        bt = getattr(b, "block_type", "") or ""
        bid = getattr(b, "id", "") or ""
        page = _page_of(bid)
        bbox = _bbox(b)
        html = getattr(b, "html", "") or ""
        if bt in ("Equation",):
            latex = _extract_latex(html)
            tagm = _TAG_RE.search(_strip_tags(html))
            blocks.append({"type": "equation", "page": page, "bbox": bbox,
                           "latex": latex, "html": html,
                           "tag": tagm.group(1) if tagm else None})
        elif bt in ("Table",):
            blocks.append({"type": "table", "page": page, "bbox": bbox, "html": html})
        elif bt in ("Figure", "Picture"):
            rel = _save_images(b, assets_dir, counter)
            blocks.append({"type": "figure", "page": page, "bbox": bbox,
                           "image_rel": rel, "text": _strip_tags(html)})
        elif bt in ("Caption", "Footnote"):
            blocks.append({"type": "caption", "page": page, "bbox": bbox,
                           "text": _strip_tags(html)})
        elif bt in ("SectionHeader", "Title"):
            blocks.append({"type": "heading", "page": page, "bbox": bbox,
                           "level": _heading_level(b), "text": _strip_tags(html)})
        elif bt in ("ListItem",):
            blocks.append({"type": "list", "page": page, "bbox": bbox,
                           "text": _strip_tags(html)})
        else:  # Text, TextInlineMath, PageHeader/Footer, Equation-less, etc.
            txt = _strip_tags(html)
            if txt:
                blocks.append({"type": "text", "page": page, "bbox": bbox,
                               "btype": bt, "text": txt, "html": html})
    return {"engine": "marker", "blocks": blocks, "page_dims": page_dims}
