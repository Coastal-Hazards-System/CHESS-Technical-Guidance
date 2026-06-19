# Pilot QA Findings — CEM PDF → Markdown (Phase 0–1)

## What was done
- **Extracted** all 50 unique files from the six PDF Portfolios (43 chapters + glossary + admin pages), de-duplicated by content hash.
- **Built** `_work/manifest.json` mapping every chapter to part/number/pages/target path.
- **Converted** 3 representative chapters with a PyMuPDF pipeline (`_work/convert.py`):
  - I-4 — small (5 pp)
  - III-1 — medium (45 pp), *Coastal Sediment Properties*
  - II-1 — equation-heavy (127 pp), *Water Wave Mechanics*

## Results

| Chapter | Pages | Text coverage* | Equations snapshotted | Raster images | 
|--------|------:|---------------:|----------------------:|--------------:|
| I-4 | 5 | 98.5% | 0 | 0 |
| III-1 | 45 | 97.1% | 17 | 5 |
| II-1 | 127 | 97.4% | 176 | 39 |

*Markdown word count vs. `pdftotext` baseline. The 2–3% gap is mostly intended (stripped running headers, footers, page numbers).

## What works well ✅
- **Prose extraction is excellent.** Born-digital text layer → clean, accurate body text with no OCR errors. Special characters (φ, σ, °) survive.
- **Section headings** map correctly from the manual's numbering (`III-1-2.` → `###`, sub-items → `####`).
- **Equation snapshots are pixel-faithful.** Each numbered equation is captured as a sharp 3× PNG and linked inline with its number. Verified: `φ = −log₂ D (III-1-1a)` renders perfectly.
- **Running headers/footers** ("EM 1110-2-1100 (Part III)", dates, page numbers) are detected and stripped.
- **Figures** are extracted as PNG assets.

## Known rough edges (fixable in Phase 2–3) ⚠️
1. **Table of Contents** is treated as body text — the dot-leader lines (". . . . .") come through verbatim and TOC entries get mis-tagged as headings. *Fix:* detect the TOC region (first 1–3 pages) and either drop it or render it as a clean linked list.
2. **Tables dump as flat text.** Multi-column tables (e.g., Table III-1-1) lose their grid. *Fix:* use PyMuPDF's `find_tables()` for regular tables → GFM; fall back to an image snapshot for complex/merged ones. This matches the plan's table strategy.
3. **Equation clip band slightly too tall** — occasionally captures a sliver of the next text line. *Fix:* tighten vertical padding to the line bbox.
4. **Figures not yet placed inline** — images are extracted but not positioned next to their captions. *Fix:* pair by page + caption proximity in Phase 2.
5. **Chapter titles** need to be read from the cover line (e.g., "COASTAL SEDIMENT PROPERTIES"), not the generic "Chapter 1".

## Equations → LaTeX: tested and working (your requirement)
Requirement locked: **equations must be Markdown LaTeX**, not images. Tested `pix2tex` (LaTeX-OCR) in this environment — it runs (torch 2.5.1 + torchvision 0.20.1, CPU) at **~1–2 s per equation** after model load. Results on real crops:

| Equation | pix2tex output | Verdict |
|----------|----------------|---------|
| III-1-1a | `\Phi = -\log_{2}D` | ✅ correct (minor: `\Phi` vs `\phi` case) |
| II-1-10 (wavelength) | `L = \frac{gT^2}{\gamma_\rightarrow}\tanh[\frac{2\pi d}{r}]...` | ⚠️ structure right, misread `2\pi`→`\gamma`, `L`→`r` |
| III-1-10 (fall velocity) | mangled | ❌ failed — crop clipped the fraction denominators |

**Two lessons:** (1) crop quality is everything — equations must be cropped with **full fraction height**; the failures came from clipped denominators. (2) Even good crops produce occasional OCR slips, so a **KaTeX validation gate + human review queue** is mandatory for an engineering manual. This is exactly the Pass A/B QA layering in the plan. Output target syntax (confirmed from the GitHub doc you shared): inline `$...$`, block ```` ```math ```` / `$$...$$`, rendered by MathJax.

## Tables → faithful recreation (your requirement)
Requirement locked: **tables must be recreated faithfully** (not flat text, not images by default). Findings:
- PyMuPDF's basic `find_tables()` is **unreliable** on this document — it caught bordered "Example Problem" text boxes as tables and missed the real data tables (Wentworth size scale, material densities), which use whitespace alignment rather than full ruling lines.
- **`pymupdf4llm`** is a much better foundation: it produced clean structured Markdown (correct heading levels, prose) in one pass and has built-in table detection. It will be the base extractor; detected tables still need per-table verification (cell counts, multi-tier headers) and manual reconstruction for the hardest ones, with an image fallback only as a flagged last resort.

## Recommendation
Foundations are solid and the full toolchain is now proven: **`pymupdf4llm`** (text + structure + tables) + **`pix2tex`** (equation LaTeX) + **KaTeX validation** + figure export. Before the full ~3,700-page run (Phase 2–3):
1. Integrate the validated tools into one resumable pipeline; replace the hand-rolled text pass with `pymupdf4llm`.
2. Fix the two pilot issues: TOC handling and full-fraction-height equation crops.
3. Stand up the multi-pass QA/QC harness (Passes A–E) and re-run the 3-chapter pilot as the gate.
