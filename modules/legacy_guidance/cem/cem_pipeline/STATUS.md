# CEM site & remediation — status and TODOs

Last updated: 2026-06-19.

## Live site
- GitHub Pages: https://coastal-hazards-system.github.io/CHESS-Technical-Guidance/
- Branch `main`. Pages serves the repo root (`.nojekyll` lets the viewer fetch raw `.md`).
- Pages: `modules/legacy_guidance/cem/out/index.html` (CHESS-TG landing: Living | Legacy + search),
  `search.html` (split search results), `cem.html` (Coastal Engineering Manual browse:
  stats, Parts, chapters), `chapter.html` (marked.js + KaTeX viewer), and the per-chapter
  `markdown/part-XX/ch-YY.md`. Styling mirrors the sibling CHESS-QC site (Trail vibe:
  13px/1.45 type, amber diagonal texture, Original palette).
- Site generator: `python src/build_site.py <out_dir> <repo_root>`.

## Conversion + remediation (all deployed)
The manual was converted with an ensemble pipeline (Marker + MinerU, KaTeX validation,
born-digital symbol cross-check, local vision-LLM self-correction for the no-text-layer
vector equations). After publishing, a set of **deterministic, re-runnable passes driven
by the source PDF** cleaned up glyph/format issues (chosen over training a local model:
the errors are mechanical and the ground truth is in the PDF — font codes, glyph
size/baseline).

Re-run (from `modules/legacy_guidance/cem/out`, with the `.venv`):
```
python ../cem_pipeline/_remediate.py            # apply all passes to every chapter .md
python ../cem_pipeline/src/build_site.py . ..\..\..\..   # regenerate the site + search index
```

Passes (in `src/notation.py`, orchestrated by `_remediate.py`):
- `fix_symbol` — Adobe/Monotype Symbol-font glyphs stranded in the Private Use Area
  (U+F0xx) → Unicode (runs first, before subscripts).
- `fix_prose` / `_words` — WordPerfect-Greek font (Part II) → Unicode, in prose and the
  reconstructed "Definitions of Symbols" tables.
- `fix_subscripts` — restore sub/superscripts the converter flattened, from PDF glyph
  size + baseline (`H0`→`$H_0$`, `10-3`→`$10^{-3}$`, `log10`→`$\log_{10}$`).
- `fix_nav` (+ `_pdf_toc`, `_pdf_list`) — rebuild Table of Contents (nested), List of
  Figures, and List of Tables from PDF row coordinates; text-split fallback when a
  chapter's source list has no dotted leaders.
- `fix_deflists` — "where:" definition runs → bullet lists.
- `fix_degree`, `fix_currency`, and equation-LaTeX cleanup (`\:`, `\mathcal{X}`, ft unit).
- Chapter viewer wraps bare in-text math (letter/digit base + sub/superscripts, accents,
  `\command`s) and drops repeated running-header pseudo-headings.

Verification (whole corpus): every display-math block and inline `$…$` expression
validates in KaTeX with **0 failures**; **0 Private-Use glyphs** remain.

## Open TODOs / known limitations
1. A few chapters' source TOCs have no dotted leaders / a title-first column order
   (e.g. II-2): they fall back to the text split — readable and one-per-line, but not
   deeply nested. Could special-case that layout.
2. Minor TOC continuation-line artifacts on a couple of chapters (e.g. VI-1): a wrapped
   sub-item title can appear as its own bullet.
3. Whitepaper of the conversion + remediation methodology (ensemble OCR, vision-LLM
   transcription, two-model cross-validation + third-model decision, deterministic
   PDF-driven glyph/format remediation). Requested as a later deliverable.
4. Optional: make TOC / List of Figures / List of Tables entries clickable links to the
   in-chapter section anchors.
5. Optional: regenerate per-chapter `.gallery.html` / `.equations.json` to match the
   remediated LaTeX (`.md` is canonical; `.equations.json` left as-is to avoid reformat
   churn).
