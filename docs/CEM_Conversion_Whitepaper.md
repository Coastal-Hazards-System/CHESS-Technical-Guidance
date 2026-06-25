# Converting the Coastal Engineering Manual to the Web

### A methodology whitepaper on the AI-assisted conversion of EM 1110-2-1100 to Markdown and HTML

_CHESS Technical Guidance. Prepared 2026-06-25._

---

## Abstract

The U.S. Army Corps of Engineers Coastal Engineering Manual (EM 1110-2-1100) is a
reference of roughly 3,700 pages held in PDF. This document describes how that manual
was converted into accurate, web-readable Markdown and HTML, with equations rendered as
real LaTeX rather than pictures, tables rebuilt as text, and figures exported as linked
images. The work was carried out by an automated pipeline that checks its own output and
only flags, with evidence, the small share of material it cannot verify. The pipeline
reads each page with two independent engines, compares each equation against the symbols
already stored in the PDF, repairs the few equations that do not pass on the first try,
and then applies a set of repeatable, rule-based passes that correct the predictable
errors left behind by the manual's legacy fonts. The end result is the full manual,
converted with every numbered equation verified and with zero equation-display failures
across the whole corpus, published as a searchable website.

---

## 1. Background and objective

The Coastal Engineering Manual was drafted between roughly 1998 and 2008 and last
materially updated by Change 3 in 2011. It is organized into six Parts plus an Appendix A
glossary. The source is delivered as Adobe PDF Portfolios, which are PDF files that wrap a
set of embedded chapter PDFs. The largest single chapter, VI-5, runs to 378 pages.

The objective was a faithful, web-renderable copy of the manual:

- **Text and headings** as Markdown, with the manual's section numbering kept intact.
- **Equations** as real LaTeX, displayed by KaTeX or MathJax, never as images.
- **Tables** rebuilt as GitHub-flavored Markdown pipe tables.
- **Figures and plots** exported as PNG images and linked with their captions.

Here, "faithful" means every element is preserved and renders correctly as HTML. Exact
page-for-page layout is not reproduced; the goal is correct, readable web content.

## 2. Why the source is harder than it looks

The manual has a real text layer for its prose, so the body text converts cleanly without
optical character recognition. The difficulty is in the mathematics and the fonts.

The text stored in the PDF is **not** a clean source of truth for the equations. The
legacy math fonts encode their symbols in non-standard ways, and they do so differently in
different Parts of the manual:

- In Parts I and III, equation characters are stored with substitutions such as `=` saved
  as `'`, a minus sign saved as `&`, a plus sign saved as `%`, and a subscript script-l
  saved as `R`.
- In Part II, the equations are line drawings with no text behind them at all. Only the
  equation number is real text.
- In Part II prose, Greek letters were typed in an old WordPerfect Greek font, so they
  come back as the wrong Latin letters. For example the symbol for velocity potential
  reads as the letter "M," and other Greek letters read as "Q," "0," "B," and "T."
- Across several Parts, Adobe Symbol-font characters are stranded in a private range of
  character codes, so they come back as unreadable boxes rather than Greek letters or math
  operators.

Because the stored text cannot be trusted on its own, the conversion was designed so that
**agreement between two independent readings is the main signal of correctness**, with the
PDF's own characters used as a cross-check where they are clean, and a visual comparison
used as a backup where they are not.

## 3. Design principle: check first, publish second

The manual is large and dense with mathematics, which rules out retyping it by hand. At
the same time, an engineering reference cannot ship a wrong coefficient. The pipeline is
therefore built around one rule:

> Never publish anything that has not been checked, and flag, with evidence, the few items
> that genuinely cannot be verified.

Three properties follow from that rule:

1. **It checks its own work.** Every equation is rendered and its symbols are compared
   against the PDF before it is published. Nothing that passes needs a person to review it.
2. **It is anchored to the PDF.** The characters already stored in the PDF are used as the
   reference. Two separate engines must agree before a result is accepted.
3. **It is honest about gaps.** Anything that cannot be verified is flagged with evidence,
   not quietly guessed, so review effort goes only where it is actually needed.

## 4. Pipeline overview

The pipeline runs one chapter at a time, is resumable, and skips chapters that are already
finished. It has eight stages.

1. **Extract.** Pull the embedded chapter PDFs out of the six Part Portfolios, remove
   duplicates by content hash, copy the Appendix A glossary, and write an index of what
   was found. Extraction recovered 50 embedded PDFs, covering the chapters, the glossary,
   and administrative front matter.
2. **Two-engine read.** Two separate engines read each page. Marker provides the document
   backbone: reading order (including two-column pages), headings, tables, figures, and a
   first reading of each equation as LaTeX with its position on the page. MinerU reads the
   equations again as an independent second opinion.
3. **Read the PDF's own symbols.** For each equation, read the actual characters under its
   position straight from the PDF text. Reduce them to the set of meaningful symbols it
   contains, with Greek letters mapped to their names and operators and digits kept. This
   is exact and uses no optical character recognition. The result is a reference
   fingerprint for that equation.
4. **Verify.** A LaTeX result is accepted only if it clears two checks. First, it must
   render in KaTeX, confirmed by running KaTeX through Node; anything that fails to render
   is never published. Second, its symbols must match the PDF fingerprint, allowing at most
   one difference, which catches dropped terms and mis-read symbols. A visual comparison of
   the rendered equation against the source image is used as a softer, backup signal.
5. **Decide.** For each equation, if the two engine readings agree and pass the checks,
   accept the result with the highest confidence. If only one reading passes, accept it. If
   neither passes, move the equation to self-correction.
6. **Self-correct.** A third, cheaper reader (pix2tex) casts a vote. If that does not
   settle it, a local vision model re-reads the cropped image of the equation, and a
   focused repair step is given the specific symbol mismatch to fix. The first result that
   passes both checks is accepted. If nothing passes, the equation is flagged with the full
   evidence rather than guessed.
7. **Tables and figures.** Tables are taken from Marker first, with a second method that
   rebuilds a table from the text in its region used as a fallback and cross-check. Tables
   come out as GitHub-flavored Markdown; only a table whose structure genuinely cannot be
   recovered falls back to an image, and that is flagged. Figures are exported as PNGs and
   matched to their captions by page and proximity.
8. **Assemble.** Combine everything into one Markdown file per chapter, with a short block
   of front-matter at the top. Alongside it, write a flagged-items file listing anything
   that could not be verified, and a small machine-readable quality file. Only LaTeX that
   passed the render check is ever written into the chapter.

## 5. Reading and verifying the equations

Equations are where most of the engineering risk and most of the effort sit, so they
receive the most care.

**Locating each equation.** Matching a reading to the right equation is done primarily by
overlap of page position, not by trying to find the equation number in the text. The
number is unreliable as an anchor because worked-example lines can be mis-tagged, so it is
used only as a fallback, and only when it appears in the right-hand margin where equation
numbers belong. Duplicate numbers are removed.

**Choosing among readings.** When several readings are available, the pipeline picks the
one best supported by the others. Ties are broken toward the most complete reading, the
one with the longest list of symbols, so that a reading which quietly dropped a term never
wins. The symbol comparison uses a tolerance that scales with the length of the equation,
on the order of a few percent, and it treats commonly confused characters as equal: the
letter l, a capital I, and the digit 1; the two ways of writing a script-l; and a forward
slash versus a fraction.

**Splitting stacked equations.** Marker sometimes merges a vertical stack of worked-example
equations into one tall block and transcribes only its top line. The pipeline detects these
and splits them back apart using the per-equation positions reported by MinerU.

**Outputs per equation.** Every equation gets a unique cropped image of its source, an
entry in a per-chapter index, and a place in a per-chapter gallery page that shows the
rendered equation next to its source image for easy review.

## 6. Cleaning up the legacy fonts

Verification produces correct LaTeX for the equations, but the prose, tables, and
navigation still carry the font problems described in Section 2. These were corrected by a
set of repeatable, rule-based passes rather than by training a model.

This choice was deliberate. The font errors are mechanical and predictable, and the
correct value is sitting in the PDF itself, in the form of font codes and the size and
position of each character. A fixed-rule pass that reads those facts is more reliable, more
transparent, and easier to re-run than a trained model would be. A trained model is used
only where it is genuinely needed, namely for the Part II equations that have no text layer
at all.

Each pass is safe to re-run and produces the same result every time. The main passes are:

- **Symbol-font repair.** Map the Adobe Symbol-font characters that were stranded in the
  private code range back to proper Unicode Greek letters and math operators. This runs
  first, before the subscript pass.
- **Greek-prose repair.** Map the old WordPerfect Greek font back to Unicode, both in the
  body prose and in the reconstructed "Definitions of Symbols" tables. The mapping is keyed
  on the font and on the Latin neighbors around each symbol, so literal Latin letters and
  digits are left untouched.
- **Subscript and superscript repair.** Restore subscripts and superscripts that the
  conversion flattened, using the size and vertical position of each character in the PDF.
  A character noticeably smaller than the base text and set low becomes a subscript, and one
  set high becomes a superscript. This turns flattened strings back into proper math, for
  example a velocity written as "U 5400" becomes a subscripted form, "10-3" becomes ten to
  the minus three, and "log10" becomes log base ten.
- **Navigation rebuild.** Rebuild the Table of Contents as a properly nested list, and the
  Lists of Figures and Tables as clean one-per-line lists, by reading the row positions of
  those pages directly from the PDF. A small number of chapters whose source lists have no
  dotted leaders fall back to a simpler text split.
- **Definition lists.** Turn runs of "symbol = definition" lines, the "where:" clauses that
  follow equations, into bullet lists so they do not collapse into a single paragraph.
- **Smaller fixes.** Restore degree signs, and protect literal dollar amounts so the
  viewer does not mistake them for the start of an inline equation.

## 7. Quality assurance

Faithfulness was earned through layered, repeated checking rather than a single review at
the end. Errors are caught close to the step that caused them, where they are cheapest to
fix.

| Layer | When it runs | What it checks |
|---|---|---|
| A. Inline | Every step, every chapter | Each equation renders; tables have sane row and header counts; text coverage stays close to the source; every figure and link resolves. |
| B. Checkpoint | After each major step | A focused review of one element type at a time, for example a contact sheet of all equations, while the context is fresh. |
| C. Whole chapter | After a chapter is assembled | A side-by-side read of the PDF against the rendered HTML, to catch flow, ordering, orphaned captions, and navigation artifacts. |
| D. Corpus | After the full run | Consistency across all chapters: headings, notation, cross-references, and a master index whose links all resolve. |
| E. Sampling audit | Final gate | A random, math-weighted sample scored against the PDF; any chapter that fails its sample is recycled through layers B and C. |

## 8. Results

The full manual was converted and published.

- **2,377 numbered equations verified**, which is 100 percent, with zero left flagged.
- **Zero equation-display failures** across the whole corpus. Every display block and
  every inline expression renders in KaTeX.
- **Zero unreadable font codes** remaining anywhere in the published text.
- **444 tables** rebuilt as Markdown, with no table left as an image fallback.
- **1,161 figures** exported and linked with captions.
- **Zero broken** figure or cross-reference links.
- **37 chapters** published on the live website.

For the verified equations, agreement between the two engine readings carried most of the
load. In a representative full run, about 66 percent of equations were accepted because the
two readings agreed, about 22 percent were accepted on a single reading that passed the
checks (these are the cleanly stored, modern-font equations), about 12 percent were
confirmed by agreement plus a clean match against the PDF text, and only a fraction of a
percent needed the self-correction path to resolve. Dense, previously unseen chapters
reached full verification with no per-chapter tuning, which indicates the approach
generalizes across the manual rather than being fitted to a few chapters.

## 9. Environment and reproducibility

The pipeline runs on Windows with two Python 3.12 environments. The main environment holds
Marker, the verification code, and the assembly code. MinerU runs in a second environment
of its own because it needs a newer imaging library than Marker does; it is called as a
separate program. Equation reading and the vision model use an NVIDIA RTX A4000 GPU. KaTeX
validation runs through Node. The local vision model used for self-correction is served by
Ollama.

The site is generated by a build script that writes the shared landing page and the
per-module pages, including the chapter viewer. The viewer renders the Markdown with
marked.js and the math with KaTeX, and search runs entirely in the browser against a
prebuilt index. The site is hosted on GitHub Pages.

A re-run is two commands: run the conversion over the source PDFs, which is resumable and
caches each engine's output so repeat runs are fast, then regenerate the site from the
repository root. The deterministic cleanup passes can be re-applied on their own at any
time, since they are safe to run repeatedly.

## 10. Limitations and next steps

- A few chapters have a source Table of Contents with no dotted leaders or with the title
  column first. These fall back to a flat, one-per-line list that is readable but not deeply
  nested. This layout could be handled as a special case.
- On a couple of chapters, a wrapped sub-item in the Table of Contents can appear as its
  own bullet. This is a minor cosmetic artifact.
- A separate quality review of the converted text and figures produced a remaining list of
  typographic, formatting, and equation items for expert sign-off. These are tracked in the
  review findings document and are candidates for a follow-up cleanup pass.

Planned improvements include making the Table of Contents and the Lists of Figures and
Tables into clickable links into the chapters, special-casing the title-first contents
layout for deeper nesting, and folding the accepted review findings back into the published
text.

## Appendix. Glossary of terms

- **Marker.** The primary engine. It reads page layout, reading order, headings, tables,
  figures, and a first version of each equation.
- **MinerU.** The second engine. It re-reads the equations as an independent check.
- **pix2tex.** A lightweight third reader used to break ties during self-correction.
- **KaTeX.** The math renderer. It is also used as a gate: if an equation will not render
  in KaTeX, it is never published.
- **LaTeX.** The text notation used to write mathematics, which KaTeX and MathJax turn into
  properly formatted equations.
- **GitHub-flavored Markdown.** The text format the chapters are written in, including its
  pipe-table syntax for tables.
- **Fingerprint.** The set of symbols an equation actually contains, read from the PDF and
  used to check a candidate LaTeX result.
