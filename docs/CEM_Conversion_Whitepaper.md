# Verified Conversion of a Large Engineering Reference from PDF to Web-Native Markdown

### An ensemble recognition and deterministic remediation pipeline, applied to the USACE Coastal Engineering Manual (EM 1110-2-1100)

**CHESS Technical Guidance Project**

_Author(s): [to be completed]. Corresponding author: [to be completed]._
_Manuscript prepared 2026-06-25._

---

## Abstract

**Background.** Long-lived engineering references are commonly distributed as PDF, with
mathematics frozen as images or encoded in legacy fonts. This format resists search,
accessibility, reuse, and incremental revision, and it is a poor substrate for the live,
web-delivered guidance that modern practice expects.

**Objective.** We convert the U.S. Army Corps of Engineers Coastal Engineering Manual
(EM 1110-2-1100), approximately 3,700 pages across six Parts and an appendix glossary, into
web-native Markdown and HTML in which every equation is real, renderable LaTeX rather than a
raster image, tables are reconstructed as text, and figures are exported and linked.

**Method.** The conversion is performed by an automated pipeline organized around a
verification-first principle: no equation is published unless it passes two independent
gates, and any expression that cannot be verified is set aside with machine-readable
evidence rather than guessed. Each page is read by two independent recognition engines. For
every equation, the symbols stored in the document's text layer are reduced to a reference
fingerprint, and a candidate LaTeX rendering is accepted only if it renders under KaTeX and
its symbol set matches the reference within a length-proportional tolerance. Expressions
that fail both engines enter a self-correction cascade that adds a third recognizer, a local
vision-language model, and a targeted repair step. A separate stage of deterministic,
geometry-driven passes then corrects the predictable errors introduced by the manual's
legacy fonts, because those errors are mechanical and their correct values are recoverable
from the file itself.

**Results.** All 2,377 numbered equations passed the verification protocol, and no display
or inline expression failed to render across the corpus. The published output contains 444
reconstructed tables, 1,161 linked figures, no residual unreadable font codes, and no broken
internal links, across 37 published chapters. Agreement between the two engines accounted
for roughly two thirds of accepted equations, and dense, previously unexamined chapters
reached full verification without per-chapter tuning.

**Conclusion.** Combining ensemble recognition, an auditable per-item reject option,
verification against the document's own symbols, and deterministic remediation of legacy
encodings yields a conversion suitable for an accuracy-critical reference. We discuss, in
detail, the difference between the pipeline's verification pass rate and certified editorial
correctness, and the role of expert sign-off in closing that gap.

**Keywords:** document engineering, PDF conversion, mathematical expression recognition,
ensemble methods, verification, vision-language models, digital preservation, technical
documentation.

---

## 1. Introduction

Engineering design references encode hard-won, accuracy-critical knowledge, and they tend to
outlive the software that produced them. The Coastal Engineering Manual is representative: it
was drafted between approximately 1998 and 2008, last materially revised by Change 3 in 2011,
and distributed as a set of PDF Portfolios, which are container PDFs that wrap embedded
chapter PDFs. Its body prose carries an embedded text layer and converts cleanly, but its
mathematics does not. Equations appear either as vector drawings with no recoverable text or
as text encoded in legacy mathematical fonts whose code points do not correspond to the
glyphs a reader sees.

Two properties make a naive conversion unacceptable. First, a coastal-engineering reference
cannot tolerate a silently corrupted coefficient or a dropped term; a plausible-but-wrong
equation is worse than a visible gap. Second, the corpus is large and dense enough that
manual transcription is impractical at the required fidelity. These two properties are in
tension: automation is necessary, yet automation that optimizes only average accuracy will,
at this scale, emit a meaningful number of confident errors with no signal of where they are.

We resolve the tension by making verification, rather than recognition, the organizing
concern. Recognition engines are treated as untrusted proposers. A proposed equation is
admitted to the output only if it (i) renders under a real web math engine and (ii) agrees,
within a defined tolerance, with the symbols actually present in the source. Anything that
fails is escalated through a cascade of additional recognizers and, if still unresolved, is
flagged with full evidence for human attention. A second concern, the legacy-font corruption
in prose, tables, and navigation, is handled separately by deterministic passes that read
the font codes and glyph geometry directly from the PDF, because for those errors the correct
answer is present in the file and a fixed rule is more reliable and more transparent than a
learned model.

**Contributions.** This article makes the following contributions.

1. A verification-first conversion architecture for accuracy-critical documents, in which
   per-equation acceptance is gated by renderability and by agreement with the source
   symbols, and in which an auditable reject option replaces silent best-guessing.
2. A concrete, reproducible instantiation that combines two layout-and-formula engines, a
   text-layer symbol fingerprint, a third lightweight recognizer, and a local
   vision-language model in a staged self-correction cascade.
3. A family of deterministic, idempotent remediation passes that recover legacy-font Greek,
   private-range symbol fonts, and geometry-flattened subscripts and superscripts, and that
   rebuild navigation structures from PDF coordinates.
4. A corpus-scale evaluation, with an explicit and honest account of what the verification
   pass rate does and does not certify, and of how an independent editorial review
   complements it.

**Organization.** Section 2 characterizes the corpus and its failure modes. Section 3
reviews related work. Sections 4 through 7 describe the system. Section 8 reports the
evaluation. Sections 9 and 10 discuss findings and threats to validity. Section 11 concludes.

## 2. The source corpus and its failure modes

The manual comprises six Parts and an Appendix A glossary. Extraction recovered 50 embedded
PDFs from the six Part containers, covering the chapters, the glossary, and administrative
front matter, de-duplicated by content hash. The largest single chapter, VI-5, is 378 pages.
The body text is digitally typeset with a usable text layer, so prose requires no optical
character recognition.

The mathematics fails in three distinct ways, and the failures are not uniform across the
manual. Table 1 summarizes the encoding failure modes by Part.

**Table 1. Mathematical encoding failure modes by Part.**

| Part | Equation encoding | Observed corruption |
|---|---|---|
| I, III | Legacy math font in the text layer | Operator code points are substituted: `=` stored as `'`, minus as `&`, plus as `%`, and a subscript script-l as `R`. |
| II | Vector drawings, no text layer | Only the equation number is real text; the equation body has no recoverable characters. |
| II (prose) | WordPerfect Greek font | Greek letters return as the wrong Latin letters; the velocity-potential symbol reads as "M," with further letters reading as "Q," "0," "B," and "T." |
| Several | Adobe Symbol font in a private code range | Greek letters and operators are stranded in the Unicode Private Use Area and return as unreadable boxes. |

The central consequence is that the text layer is not a trustworthy source of truth for the
mathematics. A pipeline that reads the stored characters and emits them verbatim would
faithfully reproduce the corruption. This observation motivates the core design decision of
Section 4: agreement between independent recognizers is the primary correctness signal, the
stored characters are used as a corroborating cross-check only where they are clean, and a
rendered-image comparison serves as a fallback where they are not.

## 3. Related work

**Document layout analysis and extraction.** General-purpose tools recover reading order,
headings, tables, and figures from PDF. We use Marker [1] as the document backbone for layout,
reading order, tables, figures, and a first reading of each equation, and MinerU [2], built on
the UniMERNet expression recognizer [3], as an independent second reading of equations.
Low-level geometry, image export, and text-layer access use PyMuPDF [10].

**Mathematical expression recognition.** Image-to-markup models map rendered mathematics to
LaTeX, beginning with coarse-to-fine attention models [6] and continuing through specialized
recognizers such as LaTeX-OCR (pix2tex) [4] and document-scale models such as Nougat [5]. We
use pix2tex [4] as a lightweight third recognizer during self-correction. These systems are
typically evaluated by average match accuracy over a benchmark; they do not, by themselves,
provide a per-expression, source-anchored acceptance test.

**Vision-language models.** General multimodal models can transcribe an image region to text
on demand. We use a locally hosted Qwen2.5-VL model [7], served through Ollama [8], to re-read
the small number of equations that the dedicated recognizers cannot resolve, including the
Part II equations that have no text layer.

**Ensembles and verification.** Combining diverse learners to improve reliability is a
long-standing idea [12]. Our use is narrower and verification-oriented: rather than averaging
predictions, we require agreement and treat disagreement as a trigger for escalation. The
renderability gate uses KaTeX [9], the same engine that renders the published site, so the
acceptance test and the delivery path are identical. The soft visual signal uses the
structural similarity index [11] between the rendered candidate and the source crop.

**Gap.** Prior pipelines largely optimize aggregate recognition accuracy and emit a best
guess for every input. For an accuracy-critical reference, the more useful object is a
per-item verdict with a principled reject option, anchored to the source document and to the
exact renderer used downstream. The system described here is organized around that object.

## 4. System overview

The pipeline processes one chapter at a time, is resumable, and skips completed chapters. It
caches each engine's output so that repeated runs are inexpensive. Table 2 lists the eight
stages; Sections 5 through 7 detail the parts that carry the most engineering risk.

**Table 2. Pipeline stages.**

| # | Stage | Function |
|---|---|---|
| 1 | Extract | Recover embedded chapter PDFs from the Part containers, de-duplicate by hash, copy the glossary, write an index. |
| 2 | Two-engine read | Marker reads layout, reading order, headings, tables, figures, and a first LaTeX reading of each equation; MinerU re-reads the equations independently. |
| 3 | Reference fingerprint | For each equation, reduce the source text-layer characters to a normalized symbol set. |
| 4 | Verify | Admit a candidate only if it renders under KaTeX and its symbol set matches the reference within tolerance; record a structural-similarity score as a soft signal. |
| 5 | Decide | If both engines agree and verify, accept with highest confidence; else accept a single verified candidate; else escalate. |
| 6 | Self-correct | Add a third recognizer, then a vision-language transcription, then a targeted repair; accept the first that verifies, otherwise flag with evidence. |
| 7 | Tables and figures | Reconstruct tables as Markdown with a region-constrained fallback; export figures and pair them with captions. |
| 8 | Assemble | Emit one Markdown file per chapter with front-matter, a flagged-items file, and a machine-readable quality record. |

The guiding rule across all stages is that only LaTeX which has passed the render gate is
ever written into a chapter, and that unresolved expressions are recorded, with evidence, in
a per-chapter flagged-items file rather than approximated.

## 5. Equation recognition and verification

Equations concentrate the engineering risk, and Stage 4 is where correctness is decided. We
describe candidate generation, the reference fingerprint, the two gates, the decision rule,
and the self-correction cascade.

### 5.1 Candidate generation

For each equation, the pipeline collects candidate LaTeX strings from Marker [1] and MinerU
[2]. Matching a candidate to the correct equation is done primarily by overlap of bounding
boxes on the page, not by locating the printed equation number. The number is an unreliable
anchor because worked-example lines are frequently mis-tagged; it is therefore used only as a
fallback, and only when it appears in the right-hand margin where equation numbers occur.
Duplicate numbers are removed before matching.

Marker occasionally merges a vertical stack of worked-example equations into one tall block
and transcribes only its top line. The pipeline detects such blocks and splits them into
their constituent equations using the per-equation bounding boxes reported by MinerU, then
treats each constituent as a separate verification target.

### 5.2 Reference fingerprint from the text layer

For an equation `e`, let the source region yield a set of text-layer characters. The
fingerprint `S(e)` is the multiset of meaningful symbols obtained by normalization: Greek
letters are mapped to canonical names, operators and digits are retained, and decorative or
layout-only characters are discarded. Normalization also unifies commonly confused glyphs
into single classes, so that the lowercase letter l, the capital letter I, and the digit 1
are equivalent; the two encodings of a script-l are equivalent; and a forward slash is
equivalent to a fraction. The fingerprint is computed directly from the stored characters,
with no optical character recognition, and is therefore exact for whatever the file contains.

Where the stored characters are corrupted (Table 1), the fingerprint inherits a corresponding
corruption. This is acceptable because, by construction, the same normalization is applied to
the candidate before comparison, and because the fingerprint is one of two gates rather than
the sole arbiter. Where the corruption is total, as in the Part II vector equations that have
no text layer, the fingerprint is empty and the visual gate and self-correction cascade carry
the decision (Sections 5.3 and 5.5).

### 5.3 Verification gates

A candidate LaTeX string `c` for equation `e` is admitted only if it passes both gates.

**Gate 1, renderability.** `c` must render without error under KaTeX [9], evaluated through
Node. KaTeX is also the engine that renders the published site, so a candidate that passes
this gate is guaranteed to display for end users, and a candidate that fails is never written
to the output. This eliminates the failure mode in which a syntactically invalid expression
reaches the reader.

**Gate 2, symbol agreement.** Let `S(c)` be the normalized symbol multiset of the candidate
and `S(e)` the reference fingerprint. Let the disagreement `d = |S(c) △ S(e)|` be the number
of unmatched symbol occurrences in the multiset symmetric difference. The candidate passes if

```
d ≤ max(1, ceil(τ · |S(e)|)),   τ ≈ 0.06.
```

That is, a short equation may differ by at most one symbol, and the allowance grows to about
six percent of the reference length for long equations. The tolerance absorbs benign
differences in normalization while still rejecting a candidate that has dropped a term or
mis-read a symbol. When several candidates pass, ties are broken toward the most complete
candidate, the one with the largest `|S(c)|`, so that a reading which quietly dropped a term
never wins over a fuller reading.

**Soft signal.** Independently, the pipeline renders `c` and computes the structural
similarity index [11] between the rendered image and the cropped source. This score does not
gate acceptance on its own; it is recorded for ranking and for rescuing expressions that lack
a usable fingerprint.

### 5.4 Decision rule

Stage 5 combines the gates with the ensemble. Algorithm 1 states the rule.

```
Algorithm 1: per-equation decision
input:  candidates C from Marker and MinerU; reference fingerprint S(e)
output: accepted LaTeX, or escalation to self-correction

V <- { c in C : Gate1(c) and Gate2(c, S(e)) }      # verified candidates
if |V| >= 2 and the verified candidates agree:
    return the agreed candidate            # highest confidence
else if |V| == 1:
    return the single verified candidate
else if |V| >= 2:                          # both verify but disagree
    return the most complete verified candidate, recording the disagreement
else:
    escalate(e) to self-correction (Section 5.5)
```

Agreement between two independently trained engines is the strongest available evidence short
of an expert check, because the engines fail in different ways and are unlikely to produce the
same valid, fingerprint-consistent error. A single verified candidate is accepted because it
has still cleared both gates. Genuine disagreement among verified candidates, which is rare,
is resolved toward completeness and is recorded.

### 5.5 Self-correction cascade

When no candidate verifies, the equation enters a staged cascade, ordered by cost.

1. **Third recognizer.** pix2tex [4] proposes an additional candidate, which is subjected to
   the same two gates. A cheap third reading often breaks a tie or supplies a verified
   candidate where the first two failed.
2. **Vision-language transcription.** A locally hosted Qwen2.5-VL model [7], served by Ollama
   [8], transcribes the cropped source image to LaTeX. Document wrappers that such models tend
   to emit are stripped before gating.
3. **Targeted repair.** If transcription still does not verify, the model is given the
   specific symbol disagreement and asked to repair the candidate, focusing the correction on
   the exact discrepancy rather than re-transcribing from scratch.

The first product of the cascade that passes both gates is accepted. If none passes, the
equation is written to the per-chapter flagged-items file with its candidates, fingerprint,
and scores, so that a human reviewer can resolve it with full context. No unverified LaTeX is
placed in the chapter body.

### 5.6 Per-equation artifacts

Every equation yields a uniquely named crop of its source, an entry in a per-chapter index,
and a place in a per-chapter gallery that shows the rendered LaTeX beside the source crop.
These artifacts make Stage B of the quality process (Section 8.1) a direct visual comparison
rather than a re-derivation.

## 6. Deterministic remediation of legacy encodings

Verification yields correct LaTeX for equations, but the prose, tables, and navigation still
carry the font corruption of Table 1. These are corrected by deterministic passes rather than
by a learned model. The justification is specific and bears stating, because it runs against
a reflex to apply learning everywhere: the corruption is mechanical and bijective, and the
correct value is present in the file as a font code and as the size and position of each
glyph. A fixed rule that reads those facts is more reliable, more auditable, and trivially
re-runnable, whereas a learned corrector would add an error rate where none need exist. A
learned model is reserved for the one place it is genuinely required, namely the Part II
vector equations with no text layer (Section 5.5).

Each pass is idempotent, so the full set can be re-applied at any time and converges to the
same result. The principal passes are as follows.

- **Private-range symbol recovery.** Map Adobe Symbol-font characters stranded in the Unicode
  Private Use Area back to their intended Greek letters and operators. This runs first, before
  subscript reconstruction, so that recovered symbols participate correctly in later passes.
- **Legacy Greek recovery.** Map the WordPerfect Greek font to Unicode in body prose and in
  the reconstructed "Definitions of Symbols" tables. The mapping is keyed on the font and on
  the Latin tokens adjacent to each symbol, so that literal Latin letters and digits are left
  untouched.
- **Subscript and superscript reconstruction.** Restore vertical structure that the
  conversion flattened, using each glyph's size and baseline offset from the PDF. A glyph
  sufficiently smaller than the surrounding text and set below the baseline becomes a
  subscript; one set above becomes a superscript. A flattened velocity "U 5400" returns to a
  subscripted form, "10-3" to ten to the negative three, and "log10" to log base ten. The
  pass is anchored so that it never produces an empty base, and it leaves already-structured
  expressions unchanged.
- **Navigation reconstruction.** Rebuild the Table of Contents as a nested list, and the Lists
  of Figures and Tables as one-per-line lists, from the row coordinates of those pages in the
  PDF. A small number of chapters whose source lists lack dotted leaders fall back to a
  text-based split.
- **Definition lists.** Convert runs of two or more consecutive "symbol = definition" lines,
  the "where:" clauses that follow equations, into bullet lists, so that they do not collapse
  into a single paragraph.
- **Minor passes.** Restore degree signs, and protect literal currency amounts so the viewer
  does not interpret a dollar sign as the start of inline mathematics.

## 7. Tables, figures, and assembly

Tables are taken from Marker first. A second method that reconstructs a table from the text in
its page region, by bucketing whole words into columns relative to the caption, serves as a
fallback and cross-check. Output is GitHub-flavored Markdown; only a table whose structure
genuinely cannot be recovered falls back to an image, and that fallback is flagged. Figures
are exported as PNG and paired to captions by page and proximity.

Assembly walks the document block stream into one Markdown file per chapter, with a
front-matter block recording the manual, Part, chapter, title, source, and revision. It also
emits a flagged-items file and a machine-readable quality record per chapter. The published
site is generated by a build step that writes the shared landing page and the per-module
chapter viewer; the viewer renders Markdown with marked.js and mathematics with KaTeX [9],
and search runs in the browser against a prebuilt index. The site is hosted on GitHub Pages.

## 8. Evaluation

### 8.1 What "verified" means

We state the construct precisely, because the headline numbers are otherwise easy to
over-read. In this work, an equation is **verified** if and only if a candidate LaTeX string
passed both gates of Section 5.3: it renders under KaTeX, and its normalized symbol set
matches the source fingerprint within the tolerance. Verification in this sense certifies
renderability and source-anchored symbol fidelity. It does not, by itself, certify full
editorial correctness, and Section 10 examines the gap directly. The quality process layers
this automated gate with human review, summarized below and in Table 5.

The conversion was checked through five layers, applied close to the step that could
introduce an error.

**Table 5. Quality layers.**

| Layer | When | Scope |
|---|---|---|
| A. Inline | Every step | Render check per equation; table row and header sanity; text-coverage ratio against the source; link resolution. |
| B. Checkpoint | After each major step | Focused review of one element type, for example a gallery of all equations against their source crops. |
| C. Whole chapter | After assembly | Side-by-side read of PDF against rendered HTML for flow, ordering, and orphaned captions. |
| D. Corpus | After the full run | Cross-chapter consistency of headings, notation, and cross-references; master-index link integrity. |
| E. Sampling audit | Final gate | Random, math-weighted sample scored against the PDF; any failing chapter recycles through B and C. |

### 8.2 Corpus-level outcomes

Table 3 reports the published outcome over the full manual.

**Table 3. Corpus-level results.**

| Metric | Value |
|---|---|
| Numbered equations verified | 2,377 of 2,377 (100%) |
| Equations left flagged | 0 |
| Display or inline expressions failing to render | 0 |
| Residual Private-Use / unreadable font codes | 0 |
| Tables reconstructed as Markdown | 444 |
| Tables falling back to images | 0 |
| Figures exported and linked | 1,161 |
| Broken figure or cross-reference links | 0 |
| Chapters published | 37 |

### 8.3 Acceptance-path distribution

The path by which equations were accepted indicates where the reliability came from. In a
representative full run, agreement between the two engines accounted for approximately 66
percent of accepted equations; a single verified candidate accounted for approximately 22
percent, these being the cleanly encoded, modern-font expressions; agreement corroborated by
a clean match against the source text accounted for approximately 12 percent; and only a
fraction of a percent required the self-correction cascade. Table 4 summarizes the
distribution.

**Table 4. Approximate acceptance-path distribution.**

| Path | Share |
|---|---|
| Two engines agree and verify | ~66% |
| Single verified candidate (clean modern encoding) | ~22% |
| Agreement plus clean source-text match | ~12% |
| Resolved via self-correction | <1% |

### 8.4 Generalization

The verification protocol and tolerances were not tuned per chapter. Dense, previously
unexamined chapters reached full verification under the same settings as the pilot chapters,
which indicates that the approach generalizes across the manual rather than being fitted to a
small sample. The caching and resumability of the pipeline meant that scaling from a
three-chapter pilot to the full corpus changed run time but not method.

### 8.5 Independent editorial review

A separate editorial review read the converted text and inspected the figure images. It
identified several hundred items across typography, grammar, formatting, equation presentation,
and figure defects, recorded with file and line citations in a companion findings document.
This review is complementary to, not redundant with, the automated gate. The gate targets
renderability and source-anchored symbol fidelity of equations; the editorial review also
covers prose quality, figure integrity, and the class of equation issues that the symbol gate
cannot detect by construction (Section 10). The two together, rather than either alone, define
the path to a certified edition, and the open items are the subject of an expert sign-off step.

## 9. Discussion

**Verification as the organizing concern.** The decisive design choice was to treat
recognition engines as untrusted proposers and to make admission contingent on an explicit,
source-anchored test. This inverts the usual emphasis on average accuracy. At corpus scale it
is the inversion that matters: it converts an unknown number of confident errors into a known,
small number of explicit flags, each carrying the evidence a reviewer needs.

**Agreement over the stored text.** Because the stored characters are themselves corrupted in
much of the manual (Table 1), trusting the text layer would have reproduced the corruption.
Using cross-engine agreement as the primary signal, with the stored symbols as a corroborating
gate only where clean, is what allowed correct output to be produced from an unreliable source.

**Determinism where the answer is in the file.** The remediation passes show the value of
matching the tool to the error. Where corruption is mechanical and the correct value is
present as a font code or a glyph position, a deterministic, idempotent pass is more reliable
and more auditable than a learned corrector, and it can be re-run at no cost. Learning is then
reserved for the genuinely under-determined case of vector equations with no text layer.

**Reproducibility.** Because every stage is deterministic given its inputs, caches its engine
outputs, and is resumable, the conversion can be rebuilt and improved as guidance and review
findings evolve, without re-incurring the cost of the parts that have not changed.

## 10. Threats to validity and limitations

**Construct validity of "verified."** The pass rate of Table 3 certifies that each equation
renders and that its symbol set matches the source within tolerance. It does not certify that
the equation is editorially correct. Two failure modes are possible by construction. First,
the symbol-set comparison is order-insensitive and tolerance-bounded, so a candidate that
permutes or compensates symbols while preserving the multiset within tolerance could pass
despite a structural error. Second, where the source fingerprint is itself corrupt or empty,
Gate 2 is weak or inert and the decision leans on rendering and on the visual signal. The
independent editorial review (Section 8.5) found equation-presentation items consistent with
these limits, which is why an expert sign-off step is part of the path to a certified edition
rather than an optional extra. We therefore report the 100 percent figure strictly as a
verification pass rate under the stated protocol, not as certified transcription accuracy.

**Dependence on the text layer.** The strength of Gate 2 scales with the cleanliness of the
stored symbols. The Part II vector equations, which have no text layer, are the weakest case
and rely on the vision-language path; their residual risk is higher than for equations with a
usable fingerprint.

**Navigation edge cases.** A small number of chapters have a contents layout without dotted
leaders, or with the title column first, and fall back to a flat list. Occasionally a wrapped
sub-item appears as its own bullet. These are cosmetic and bounded.

**External validity.** The results are demonstrated on one manual. The architecture is
general, but the specific font mappings and the tolerance were chosen for this corpus, and
transfer to other legacy references would require re-deriving the mappings and re-validating
the tolerance.

## 11. Conclusion and future work

We have described and evaluated a pipeline that converts a large, accuracy-critical
engineering reference from PDF into web-native Markdown and HTML, with mathematics as
verified, renderable LaTeX. The pipeline is organized around verification rather than
recognition: two independent engines propose, the source symbols and a real web renderer
dispose, a staged cascade rescues the difficult minority, and an auditable reject option
replaces silent guessing. Deterministic, geometry-driven passes then repair the predictable
legacy-font corruption that no recognizer should be asked to learn. Over the full manual,
every numbered equation passed the verification protocol and no expression failed to render,
while an independent editorial review defines the remaining path to a certified edition.

Future work includes turning the contents and figure and table lists into in-document
hyperlinks, special-casing the title-first contents layout for deeper nesting, folding the
accepted editorial findings into the published text, and strengthening Gate 2 with an
order-sensitive structural check to narrow the construct-validity gap identified in Section 10.

## Acknowledgments

This work was carried out under the CHESS Technical Guidance Project. We thank the
maintainers of the open-source tools on which the pipeline depends.

## References

[1] V. Paruchuri and Datalab. _Marker: PDF to Markdown and structured output._ Open-source
software. https://github.com/datalab-to/marker

[2] B. Wang et al. _MinerU: An Open-Source Solution for Precise Document Content Extraction._
arXiv preprint, 2024. https://github.com/opendatalab/MinerU

[3] B. Wang et al. _UniMERNet: A Universal Network for Real-World Mathematical Expression
Recognition._ arXiv preprint, 2024.

[4] L. Blecher. _LaTeX-OCR (pix2tex): Optical character recognition for LaTeX mathematics._
Open-source software. https://github.com/lukas-blecher/LaTeX-OCR

[5] L. Blecher, G. Cucurull, T. Scialom, and R. Stojnic. _Nougat: Neural Optical Understanding
for Academic Documents._ arXiv preprint, 2023.

[6] Y. Deng, A. Kanervisto, J. Ling, and A. M. Rush. _Image-to-Markup Generation with
Coarse-to-Fine Attention._ In Proceedings of the 34th International Conference on Machine
Learning (ICML), 2017.

[7] Qwen Team. _Qwen2.5-VL Technical Report._ arXiv preprint, 2025.

[8] _Ollama: Run large language models locally._ Open-source software. https://ollama.com

[9] _KaTeX: The fastest math typesetting library for the web._ Open-source software.
https://katex.org

[10] _PyMuPDF: Python bindings for the MuPDF rendering library._ Open-source software.
https://pymupdf.readthedocs.io

[11] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli. _Image Quality Assessment: From
Error Visibility to Structural Similarity._ IEEE Transactions on Image Processing, 13(4),
600 to 612, 2004.

[12] T. G. Dietterich. _Ensemble Methods in Machine Learning._ In Multiple Classifier Systems
(MCS), Lecture Notes in Computer Science, 2000.

[13] U.S. Army Corps of Engineers. _Coastal Engineering Manual, EM 1110-2-1100._ 2002, with
changes through Change 3, 2011.

---

## Appendix A. Reproducibility

**Environment.** The pipeline runs on Windows with two Python 3.12 environments: a primary
environment for Marker, verification, and assembly, and a separate environment for MinerU,
which requires a newer imaging library and is invoked as a subprocess. Recognition and the
vision-language model use an NVIDIA RTX A4000 GPU. KaTeX validation runs through Node. The
self-correction vision-language model is served by Ollama.

**Procedure.** A run proceeds in two commands: convert the source PDFs, which is resumable and
caches each engine's output, then regenerate the site from the repository root. The
deterministic remediation passes can be re-applied independently at any time, because they are
idempotent.

## Appendix B. Confusable-symbol normalization

Gate 2 unifies the following classes before comparison, to prevent benign glyph ambiguity from
causing false rejections:

- the lowercase letter l, the capital letter I, and the digit 1;
- the two encodings of a script-l;
- a forward slash and a fraction of the same operands.

The same normalization is applied to both the candidate and the reference fingerprint, so the
unification cannot mask a genuine difference in the count of distinct symbols beyond the stated
tolerance.
