#!/usr/bin/env python3
"""Stage 0: extract embedded chapter PDFs from the six EM_1110-2-1100 Part
Portfolios, de-dup by content hash, copy the App_A glossary, and write
out/manifest.json. (spec §7.1)"""
import sys
import os
import json
import hashlib
import re
import shutil
from pypdf import PdfReader

ROMAN = {'01': 'I', '02': 'II', '03': 'III', '04': 'IV', '05': 'V', '06': 'VI'}


_RUNHDR = re.compile(r'^\s*(EM\s*1110|\(Part\s|Change\s|\d{1,2}\s+\w{3,9}\s+\d{2,4}|[IVX]+-\d+-\d+|Chapter\s+\d+\s*$)', re.I)


def _page_count(pdf_path):
    """Robust page count via fitz (pypdf chokes on these embedded PDFs)."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        n = len(doc)
        doc.close()
        return n
    except Exception:
        try:
            return len(PdfReader(pdf_path).pages)
        except Exception:
            return None


def _read_title(pdf_path, chapter):
    """Best-effort chapter title: line after 'Chapter N', else first ALL-CAPS
    title-ish line near the top of page 1 (skipping running headers)."""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        lines = [ln.strip() for ln in doc[0].get_text("text").splitlines() if ln.strip()]
        doc.close()
        for i, ln in enumerate(lines[:40]):
            if re.match(r'^Chapter\s+(\d+)\b', ln, re.I):
                # title is the next non-running-header line
                for nxt in lines[i + 1:i + 5]:
                    if not _RUNHDR.match(nxt):
                        return nxt.strip()
        for ln in lines[:40]:
            if _RUNHDR.match(ln):
                continue
            letters = [c for c in ln if c.isalpha()]
            if len(ln) >= 8 and letters and sum(c.isupper() for c in letters) / len(letters) > 0.8:
                return ln.strip()
    except Exception:
        pass
    return f"Chapter {chapter}" if chapter else ""


def main(src_dir, out_dir):
    chdir = os.path.join(out_dir, "chapters")
    os.makedirs(chdir, exist_ok=True)
    seen = {}
    recs = []
    for part in ['01', '02', '03', '04', '05', '06']:
        f = os.path.join(src_dir, f"EM_1110-2-1100_Part-{part}.pdf")
        if not os.path.exists(f):
            print(f"  (missing {f})")
            continue
        try:
            attachments = PdfReader(f).attachments
        except Exception as e:
            print(f"  ! cannot read attachments from Part-{part}: {e}")
            continue
        for name, content in attachments.items():
            data = content[0] if isinstance(content, list) else content
            h = hashlib.md5(data).hexdigest()
            if h in seen:
                continue
            seen[h] = 1
            clean = name.replace('<0>', '').strip()
            wf = f"P{part}__{clean}"
            wpath = os.path.join(chdir, wf)
            with open(wpath, 'wb') as out:
                out.write(data)
            try:
                pc = _page_count(wpath)
            except Exception:
                pc = None
            m = re.search(r'Ch_?(\d+)', clean)
            chapter = int(m.group(1)) if m else None
            kind = "chapter" if m else ("glossary" if re.search(r'gloss', clean, re.I) else "admin")
            recs.append({
                "portfolio": f"Part-{part}", "orig_name": clean, "work_file": wf,
                "md5": h, "part_roman": ROMAN[part], "chapter": chapter,
                "kind": kind, "title": _read_title(wpath, chapter) if kind == "chapter" else "",
                "pages": pc, "status": "pending",
            })
    appa = os.path.join(src_dir, "EM_1110-2-1100_App_A.pdf")
    if os.path.exists(appa):
        dst = os.path.join(chdir, "App_A.pdf")
        shutil.copy(appa, dst)
        pc = _page_count(dst)
        recs.append({
            "portfolio": "App_A", "orig_name": "App_A.pdf", "work_file": "App_A.pdf",
            "md5": hashlib.md5(open(appa, 'rb').read()).hexdigest(),
            "part_roman": "App-A", "chapter": None, "kind": "glossary",
            "title": "Glossary", "pages": pc, "status": "pending",
        })
    man = os.path.join(out_dir, "manifest.json")
    os.makedirs(out_dir, exist_ok=True)
    json.dump(recs, open(man, "w"), indent=2)
    nch = sum(1 for r in recs if r["kind"] == "chapter")
    print(f"Extracted {len(recs)} files ({nch} chapters) -> {chdir}")
    print(f"Manifest -> {man}")
    return recs


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ".")
