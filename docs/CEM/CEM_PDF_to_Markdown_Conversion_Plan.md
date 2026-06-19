# Plan: Convert the Coastal Engineering Manual (EM 1110-2-1100) PDFs to Faithful Markdown

*Version 2 — updated after the Phase 0–1 pilot and with output requirements locked.*

## Goal

Convert the USACE Coastal Engineering Manual from PDF into clean, web-renderable Markdown — **one `.md` file per chapter** — that reproduces the source faithfully:

- **Prose & headings** → Markdown text with the manual's section numbering preserved.
- **Equations** → **real Markdown LaTeX** (not images), rendered by KaTeX / MathJax / GitHub.
- **Tables** → **faithfully recreated** as GitHub-Flavored-Markdown (GFM) tables.
- **Figures & plots** → extracted as image files (PNG) and linked.

"100% faithful" = every element preserved and rendering correctly as HTML; exact pagination/layout is not reproduced.

## Locked output decisions
| Element | Decision |
|--------|----------|
| End use | Markdown that renders as HTML for web content, blog posts, READMEs (GFM). |
| Equations | **Markdown-based LaTeX.** Inline `$ ... $`; display as ```` ```math ```` fenced blocks (or `$$ ... $$`). GitHub renders these via MathJax. **No equation images.** |
| Tables | **Faithfully recreated** as GFM pipe tables; image fallback only for tables whose structure genuinely cannot be recovered (flagged for review). |
| Figures / plots | Extracted as PNG, linked with caption. |
| File structure | One `.md` per chapter, foldered by Part, shared `assets/` tree, master `index.md`. |

### GitHub / MathJax math syntax (confirmed from the doc you shared)
- Inline: `$\sqrt{3x-1}+(1+x)^2$` — or `` $`...`$ `` when the expression contains markdown-conflicting characters.
- Block: open a line with `$$` … `$$`, **or** use a ```` ```math ```` fenced block (preferred — no delimiter ambiguity).
- A literal `$` inside math is escaped `\$`; outside math on a math line, wrap it in `<span>$</span>`.

## What the source is (confirmed)
The six `Part-0X.pdf` files are **PDF Portfolios** wrapping embedded chapter PDFs; `App_A.pdf` is a standalone Glossary. **50 unique files extracted** (43 chapters + glossary + admin), de-duplicated by hash. Chapters are **born-digital with a real text layer — no OCR needed for prose.** Total ≈ **3,700+ pages**; largest chapter (VI-5) is 378 pp. Inventory and per-chapter page counts are in `_work/manifest.json`.

## Validated toolchain (proven in the pilot)
1. **`pymupdf4llm`** — primary text/structure/table extractor. In testing it produced clean Markdown with correct heading levels and prose in one pass; it also has built-in table detection and optional OCR. This replaces the hand-rolled text pass from the first pilot.
2. **`pix2tex` (LaTeX-OCR)** — equation → LaTeX. Confirmed working in this environment (torch 2.5.1 + torchvision 0.20.1 CPU). After model load (~once), inference is **~1–2 s per equation**. Accuracy is high on clean, fully-captured crops and drops on complex/clipped ones — so cropping quality and validation are critical.
3. **KaTeX (headless)** — validation gate: every produced LaTeX string is test-rendered; failures are flagged, never shipped silently.
4. **PyMuPDF (fitz)** — figure/equation region detection, image export, geometry.

## Pipeline (per chapter)

**Step 1 — Base conversion.** Run `pymupdf4llm` to get structured Markdown (headings, prose, lists, and first-pass tables). Strip running headers/footers ("EM 1110-2-1100 (Part III) / 30 Apr 02", page numbers) by repeated-line detection.

**Step 2 — Equations → LaTeX.** Detect each numbered equation (regex on the `(II-1-12)` markers + geometry). For each: crop the equation body tightly **with full fraction height** (the pilot showed too-tight vertical crops clip denominators and cause OCR errors), run `pix2tex`, then **validate with KaTeX**. Emit as:
````
```math
L = \frac{gT^2}{2\pi}\,\tanh\!\left(\frac{2\pi d}{L}\right) \tag{II-1-10}
```
````
Equations that fail validation are written to a per-chapter `_review.md` queue for human correction (kept out of the final file until fixed).

**Step 3 — Tables → GFM.** Take `pymupdf4llm`'s detected tables; verify each against the source (cell count, header row). Reconstruct clean GFM. Tables that can't be recovered structurally (merged/multi-tier headers) get reconstructed manually or, as a last resort, flagged with an image fallback. The reference tables here (Wentworth size scale, material densities) are accuracy-critical and get explicit QA.

**Step 4 — Figures.** Export raster figures/plots to `assets/part-XX/ch-YY/`, pair each with its `Figure N` caption by page + proximity, link inline with caption as alt text.

**Step 5 — Assemble.** Add YAML front matter (manual, part, chapter, title, source, revision date, pages). Normalize asset paths. Write the chapter `.md`.

## Phases & sequencing
- **Phase 0 — Extraction & manifest.** ✅ Done (50 files extracted + `manifest.json`).
- **Phase 1 — Pilot.** ✅ Done on 3 chapters; toolchain validated (see QA findings).
- **Phase 2 — Harden the pipeline.** Integrate `pymupdf4llm` + equation crop/OCR/validate + table reconstruction + figure pairing into one resumable, manifest-driven script. Fix the two pilot issues (TOC handling, fraction-height crops).
- **Phase 3 — Second pilot.** Re-run the same 3 chapters end-to-end, looping through QA Passes A→C until accuracy targets are met. **Gate before scaling.**
- **Phase 4 — Full run.** Convert all 43 chapters + glossary in batches (chunk the 378-pp chapter). Each batch runs Passes A→C and must pass before the next starts; produce per-chapter `_review.md` queues and QA logs.
- **Phase 5 — Verification (mandatory).** Corpus pass (D) + independent sampling audit (E); recycle any chapter that fails its sample back through B/C. See the Multi-pass QA/QC strategy below for the full layered approach.
- **Phase 6 — Packaging.** `index.md` master TOC, per-part READMEs, final delivery of `markdown/` tree.

## Multi-pass QA/QC strategy

Faithfulness is earned through **layered, repeated verification**, not a single check at the end. The most efficient pattern mixes cheap automated checks that run constantly with deeper review passes at natural checkpoints — catching errors when they're cheapest to fix (closest to the step that caused them) rather than letting them compound.

**Pass A — Inline validation (automated, every step, every chapter).** Runs as part of the pipeline, near-zero cost:
- Equations: KaTeX render check on every LaTeX string the moment it's produced; anything that doesn't render is routed to `_review.md` instead of the output.
- Tables: cell-count and header-row sanity check against the detected source table.
- Text: running text-coverage ratio vs. `pdftotext` baseline; flag any chapter dropping >~3%.
- Assets/links: every figure/equation link resolves to a file that exists.

**Pass B — Per-step checkpoint review (after each major step, per chapter).** A focused look right after the step that's most error-prone, while context is fresh:
- After Step 2 (equations): render the chapter's equations to a contact-sheet HTML and diff visually against the source crops; correct the `_review.md` queue.
- After Step 3 (tables): render tables and compare to the PDF; fix structure.
- After Step 4 (figures): confirm figure count and caption pairing.
This is more efficient than deferring everything to the end because each step's reviewer only looks at one element type at a time.

**Pass C — Whole-chapter review (after a chapter is assembled).** Side-by-side PDF ↔ rendered-HTML read of the full chapter to catch flow problems, mis-ordered blocks, orphaned captions, and TOC artifacts that only show in context. Equation/table-heavy chapters (II-1, V-3/4/5/6, VI-5) get a heavier read.

**Pass D — Cross-chapter / corpus pass (after the full run).** Consistency across the whole manual: uniform heading scheme, symbol/notation consistency, cross-reference integrity, no duplicated or missing chapters, master `index.md` links all resolve.

**Pass E — Independent sampling audit (final).** A reviewer (ideally a second person, or a separate verification agent) randomly samples N pages per chapter — weighted toward math/tables — and scores fidelity against the PDF. If a chapter's sample exceeds an agreed error threshold, that chapter is **recycled** through Pass B/C. This sampling-and-recycle loop is what turns "mostly right" into "verified faithful."

**Iteration / gates.** The second pilot (Phase 3) and each batch in the full run (Phase 4) loop through A→C until they pass before moving on; Passes D–E gate final delivery. Each pass writes a short QA log per chapter so progress and known issues are auditable. Tooling for the passes is built once and reused across all chapters, so the marginal cost per chapter is low.

| Pass | When | Scope | Automated? |
|------|------|-------|-----------|
| A — Inline validation | During every step | Per element | Fully |
| B — Step checkpoint | After each major step | One element type / chapter | Automated + human spot |
| C — Whole-chapter | After chapter assembled | Full chapter | Human, automation-assisted |
| D — Corpus | After full run | All chapters | Automated + human |
| E — Sampling audit | Final gate | Random weighted sample | Human / verification agent → recycle |

## Effort & honest expectations
The bottleneck is **not** prose (that's ~97% accurate and largely automatic) — it's **equation and table verification**. With ~3,700 pages and (extrapolating from the pilot) on the order of a few thousand numbered equations plus hundreds of tables, math-OCR + table reconstruction will produce a meaningful error rate that **requires human review** for an engineering reference where a wrong coefficient matters. Realistic shape: pipeline hardening + second pilot first, then the full run is automatable but followed by a substantial, chapter-by-chapter human QA pass. Equation-heavy chapters (II-1, V-3/4/5/6, VI-5) carry most of the QA cost.

## Risks & mitigations
| Risk | Mitigation |
|------|-----------|
| Math-OCR errors (e.g. `2π`→`γ`, `L`→`r`, case slips) | Full-height crops; KaTeX validation gate; `_review.md` human queue; never ship unvalidated LaTeX |
| Tables with merged/multi-tier headers | `pymupdf4llm` first pass + manual reconstruction; image fallback only as last resort, flagged |
| TOC dot-leaders / false headings | Detect TOC region; render as clean linked list or drop |
| Figure–caption mismatch | Pair by page + caption-number regex; verify counts in Phase 5 |
| Special symbols (°, Greek, sub/superscripts) | Preserved natively in prose; validated in math via KaTeX |
| Scale / long runs | Manifest-driven, resumable, batched; chunk the 378-pp chapter |

## Open items to confirm
1. **Change pages / revisions** (`Chg`/`chg` docs): fold corrections into each chapter (recommended, with a front-matter `revision` field) or keep separate?
2. **Cross-references** ("see Equation II-1-12 / Figure III-2-4"): plain text, or upgrade to clickable links across files (extra pass)?
3. **Administrative pages** (signed cover sheets, cover letters, outline): convert or exclude?
4. **Accuracy bar for equations**: target % auto-accepted vs. routed to human review — sets the QA budget.
