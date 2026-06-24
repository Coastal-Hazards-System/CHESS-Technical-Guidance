# CEM PDF → Markdown Conversion Pipeline

Converts the USACE Coastal Engineering Manual (EM 1110-2-1100) from its PDF
Portfolios into faithful, web-renderable Markdown — **one `.md` per chapter**
with equations as real LaTeX (KaTeX/MathJax), tables as GitHub-Flavored Markdown,
and figures as linked images.

## What it produces
```
<out>/
  manifest.json
  chapters/                 extracted source chapter PDFs
  markdown/
    part-02/ch-01.md        final chapter (LaTeX math, GFM tables, figures)
    part-02/ch-01_review.md  equations that need human correction
    part-02/assets/...       figure PNGs (+ equation/table fallback images)
```

## Requirements
- Python 3.10+ with: `pip install -r requirements.txt`
  (pymupdf, pymupdf4llm, pillow, pix2tex, torch, torchvision — CPU is fine)
- Node.js with KaTeX: `npm install katex` (run inside this folder, or set NODE_PATH)
- First pix2tex run downloads ~115 MB of model weights (once).

## Run
```bash
# full manual, using all CPU cores for equation OCR
python run_all.py --src /path/to/CEM --out /path/to/output --jobs 48

# a subset of chapters
python run_all.py --src /path/to/CEM --out ./out --only III-1,II-1 --jobs 48
```
The run is **resumable** — finished chapters are skipped (use `--force` to redo).
On a 48-core machine, equation OCR fans out across all cores (one model per worker).

## Pipeline stages (per chapter)
1. **extract.py** — pull embedded chapter PDFs from the Portfolios, de-dup by hash, build `manifest.json`.
2. **convert_chapter.py** — clean text + heading mapping, strip running headers/footers, handle the TOC, detect & crop equations (full fraction height) leaving `{{EQ:id}}` placeholders, reconstruct tables (`tables.py`) as GFM (image fallback if low-confidence), export figures.
3. **ocr_equations.py** — OCR equation crops → LaTeX in parallel (per-equation timeout guard).
4. **validate_assemble.py** — sanitize LaTeX → validate with KaTeX (`katex_validate.js`) → substitute valid equations as ```` ```math ```` blocks; route failures to `_review.md`.

## QA / faithfulness
- Every equation is KaTeX-validated; only valid LaTeX ships inline, the rest are
  flagged with an interim image and queued in `_review.md`.
- Tables below a confidence threshold fall back to a flagged image rather than a wrong grid.
- Pilot results (chapter III-1): ~97% text coverage, 5/6 tables auto-gridded,
  ~82% of equations auto-accepted after sanitization; remainder routed to review.
- **Human review of the `_review.md` queues is the expected final step** — this is
  an engineering manual where a wrong coefficient matters.

## Tuning
- `--jobs` controls OCR parallelism (default = CPU count).
- Table confidence threshold: `ok = conf >= 0.45` in `tables.py`.
- Equation crop padding / scale: `crop_eq()` in `convert_chapter.py`.
