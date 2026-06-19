# CEM PDF → Faithful Markdown — fully-automated, machine-verified pipeline

Converts the USACE Coastal Engineering Manual (EM 1110-2-1100) PDF Portfolios
into one Markdown file per chapter: equations as **real KaTeX/MathJax LaTeX**
(never images, every one KaTeX-validated **and** symbol-checked against the PDF's
born-digital text layer), tables as **GFM**, figures as linked **PNGs**. No human
in the loop — the system verifies its own output and only *machine-flags* (with
evidence) the residual it genuinely cannot verify.

## How it works (per chapter)
1. **extract.py** — pull embedded chapter PDFs from the six Part Portfolios,
   de-dup by md5, copy the App-A glossary, write `manifest.json`.
2. **Ensemble layout + formula recognition** — run **two independent engines**:
   - **Marker** (`marker-pdf`) is the document backbone: reading order (handles
     two-column), headings, tables, figures, and per-equation LaTeX + bboxes.
   - **MinerU** (UniMERNet) is the independent second opinion on equation LaTeX.
3. **Ground-truth fingerprint** (`groundtruth.py`) — for each equation bbox, read
   the born-digital characters from the PDF text layer and reduce to a multiset of
   meaningful symbols (Greek→names, operators, digits). This is exact, no OCR.
4. **Verify** (`equations/verify.py`) — hard gates: (a) **KaTeX validity** via Node,
   (b) **symbol cross-check**: candidate LaTeX's symbol multiset must match the
   ground-truth fingerprint (≤1 edit tolerance). Render-diff SSIM is a soft signal.
5. **Ensemble decision** (`equations/ensemble.py`) — ≥2 engines agree & verify →
   accept (highest confidence); else single verified candidate → accept; else →
   self-correct.
6. **Self-correction** (`equations/selfcorrect.py`) — multi-pass, unattended:
   cheap pix2tex vote, then a **local vision-LLM** (Ollama/vLLM) transcription, then
   a targeted VLM *repair* prompt fed the symbol-diff. Accept the first that passes
   the hard gates; otherwise flag with full evidence.
7. **Tables** (`tables.py`) — Marker first; a region-constrained text-strategy
   reconstructor (caption→paragraph region, whole-word column bucketing) as
   fallback/cross-check; GFM out, flagged image fallback below confidence.
8. **Assemble** (`assemble.py`) — walk Marker's block stream → final chapter `.md`
   with YAML front-matter, `_flagged.md` (auditable residual), and `.qa.json`.
   Only KaTeX-valid LaTeX is ever emitted inside a ```` ```math ```` block.

## Environment (Windows, this machine)
- **Python 3.12** venv `.venv` (main: Marker + verification + assemble).
- **Python 3.12** venv `.venv-mineru` (MinerU only — it requires `pillow>=11`
  which conflicts with Marker/surya's `pillow<11`, so MinerU runs as a CLI
  subprocess in its own venv). Point the orchestrator at it via
  `CEM_MINERU_EXE=...\.venv-mineru\Scripts\mineru.exe`.
- **GPU**: torch `2.11.0+cu128` (NVIDIA RTX A4000). Engines auto-use CUDA.
- **Node + KaTeX**: `npm install katex`; the orchestrator passes Node via
  `CEM_NODE`.

## Setup
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
# GPU torch (CUDA index lags PyPI; pin a build that exists there):
.\.venv\Scripts\python -m pip install torch==2.11.0 torchvision==0.26.0 `
    --index-url https://download.pytorch.org/whl/cu128 --force-reinstall --no-deps
npm install katex
# MinerU in its own venv (pillow>=11):
py -3.12 -m venv .venv-mineru
.\.venv-mineru\Scripts\python -m pip install "mineru[core]"
```

## Run
```powershell
$env:CEM_NODE = "C:\Program Files\nodejs\node.exe"
$env:CEM_MINERU_EXE = "$PWD\.venv-mineru\Scripts\mineru.exe"
# pilot gate first:
.\.venv\Scripts\python src\run_all.py --src "..\" --out "..\out" --only II-1,III-1,III-2 --jobs 48
# then the full run (resumable; finished chapters skipped):
.\.venv\Scripts\python src\run_all.py --src "..\" --out "..\out" --jobs 48
```
Outputs land in `..\out\markdown\part-XX\ch-YY.md` (+ `_flagged.md`, `.qa.json`,
`assets/`), plus `index.md` and `qa_report.md` at the corpus root.

## Config (`config.yaml`)
Engine toggles, self-correct passes, verification thresholds, table confidence,
VLM backend. Defaults: Marker+MinerU on; pix2tex/VLM self-correct used if present.
