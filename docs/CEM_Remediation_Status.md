# CEM Conversion — Remediation Status

_Status of the QA review findings (see `CEM_Review_Findings.md`) after the first deterministic remediation pass. Generated 2026-06-25._

## Automatically remediated

A set of deterministic, idempotent passes (in `notation.py`, run by `_remediate.py`) cleared the mechanical, high-frequency issue classes. These edits were verified to leave all mathematics untouched (identical `$` counts) and to delete no body content.

| Pass | What it fixed | Scope |
| --- | --- | --- |
| `fix_headers` | Removed PDF running-header / page-footer text that leaked into the body (chapter-start `Chapter N EM 1110-2-1100 …` lines, repeated `EM 1110-2-1100 (Part X) … (Change N)` and `Change N (date)` pseudo-headings, and `<title> <page-id>` footers) | 595 lines across 26 chapters |
| `fix_apostrophe` | Restored apostrophes saved as the glyph `í` in contractions and possessives (Part I-3) | 5 occurrences |
| `fix_merges` | Repaired specific line-break word merges (`masstransport`, `welldefined`, `wellestablished`, `ofthe`, `crossshore`, `wedgeshaped`, `navigationrelated`) | 8 distinct merges |

This resolves **56** of the review findings (primarily the running-header / page-footer class, plus the listed apostrophe and word-merge items).

## Open — requires expert sign-off

**656** text findings remain open. They need engineering or editorial judgment and were intentionally not auto-fixed (a wrong subscript that still renders, a grammar rewrite, a table re-layout, or a real-word typo cannot be corrected mechanically without risk). Counts by category:

| Category | High | Medium | Low | Total |
| --- | --: | --: | --: | --: |
| Equation correctness (semantic) | 82 | 97 | 18 | 197 |
| Typos | 6 | 57 | 88 | 151 |
| Formatting (other) | 6 | 37 | 49 | 92 |
| Table structure | 33 | 27 | 8 | 68 |
| Headings / TOC / lists | 9 | 22 | 20 | 51 |
| Grammar | 2 | 25 | 16 | 43 |
| Glyph substitutions (math) | 7 | 13 | 0 | 20 |
| Duplicated text | 3 | 5 | 5 | 13 |
| Apostrophe glyphs (non-í) | 1 | 4 | 4 | 9 |
| Word merges (context-specific) | 4 | 2 | 2 | 8 |
| Other | 0 | 4 | 0 | 4 |
| **Total** | 153 | 293 | 210 | **656** |

Plus **69 figure defects** (Category 5 of `CEM_Review_Findings.md`), which are image issues and are addressed separately from the text passes.

## High-severity open items (sign-off queue)

The high-severity open items, listed first for review. Each cites the file and line in the converted Markdown; full detail and the remaining medium/low items are in `CEM_Review_Findings.md`.

### Typos

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| appendix/appendix-a-glossary.md | 411 | "br" is an OCR typo for "be". | Change "br" to "be". |
| appendix/appendix-a-glossary.md | 1721 | Term misspelled; the correct word is HALOCLINE (and the entry is mis-alphabetized; cross-ref at line 3136 correctly spells HALOCLINE). | Change heading to `### HALOCLINE`. |
| appendix/appendix-a-glossary.md | 3242 | Misspelling: should be "SECCHI DISK" (cf. line 2682 "SECCHI DISK"). Doubled wrong letter. | Change to `### SECCHI DISK`. |
| appendix/appendix-a-glossary.md | 1886 | "tp" is an OCR typo for "to". | Change "tp" to "to". |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-01/ch-02.md | 97 | Malformed math: significant wave height should be $H_{mo}$ (subscript), not $H^{m}O$; "Tp" should be $T_p$ | `$H_{mo}$ and $T_p$ averaged` |

### Duplicated text

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 543, 559 | Eq II-1-31 has duplicated `{\theta}{\theta}` -> renders `\sin^2\theta\theta`. | Remove duplicate; should be `\sin^2\theta = [...]`. |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 177 | The velocity potential symbol Φ was OCR'd as the letter "M" (a recurring Symbol-font decoding error). | "...the potential function, Φ." |
| part-02/ch-01.md | 209, 372 | Eckart approximation argument should be 4π²d/(gT²); written as (4π²/T²)(d/g) which is dimensionally inconsistent (g in denominator should be gT²). Compare line  | Argument should be `\frac{4\pi^2 d}{gT^2}` (equivalently `\frac{2\pi d}{L_0}`). |
| part-02/ch-01.md | 404 | Missing `/L`: the prefactor should be (H/2)(gT/L) to match Eq. II-1-22 (line 400) `\frac{H}{2}\frac{gT}{L}`. As written it reads HgT/2. | Change to `\frac{H}{2}\frac{gT}{L}\frac{\sinh[...]}{\cosh(...)}\sin\theta`. |
| part-02/ch-01.md | 497, 523 | The cosh argument uses `2π(15-5)/81.7` but z=-5, d=15 so (z+d)=10 is right; however the displayed cosh value (1.1306) does not match cosh(0.7691)=1.3106 compute | Reconcile: u should use cosh[2π(10)/81.7]; result line should use 1.3106 (per line 511), not 1.1306. |
| part-02/ch-01.md | 711, 714, 741, 754 | Mass density ρ rendered as literal `p`/`\mathsf{p}` in several equations (II-1-44, II-1-46), conflicting with pressure p; e.g. line 741 `\mathsf{p}g(\eta K_z -  | Replace the density `p`/`\mathsf{p}` with `\rho`. |
| part-02/ch-01.md | 864 | Malformed: parenthesis mis-placed and `.` for ≈; intended "sinh(4πd/L) ≈ 4πd/L". | Rewrite as "sinh(4πd/L) ≈ 4πd/L". |
| part-02/ch-01.md | 1278, 1339 | (a) "0.K." is OCR of "O.K." inside math. (b) line 1339 mislabels H/y_t = 0.349 as L²H/d³ (the L²H/d³ value is 290, per line 1258). | (a) Move "O.K." out of math. (b) line 1339 LHS should be `\frac{H}{y_t}`, not `\frac{L^2H}{d^3}`. |
| part-02/ch-01.md | 1377, 1381 | Denominator uses `Mx/D` (capital D) while numerator uses `Mx/d`; should both be lowercase d (Eqs II-1-92, II-1-93). | `\cosh(Mx/d)`. |
| part-02/ch-01.md | 1498 | A stray trailing `a` appears after the closing brace of the fraction (II-1-105), garbling the equation. | Remove the stray `a` (the RHS is the rational function only). |
| part-02/ch-01.md | 1539 | Density ρ rendered as literal `p`, colliding with pressure p on the LHS. | `p(x,z) = \rho(R - gd - gz) - \tfrac12\rho(u^2+w^2)`. |
| part-02/ch-01.md | 1841-1842 | Rayleigh distribution (II-1-129) cases both labeled "for x ≥ 0"; the second line is the cumulative distribution P(x), not a piecewise branch of the density. The | Split into p(x) and P(x); remove the erroneous identical case condition. |
| part-02/ch-01.md | 1873 | The Longuet-Higgins most-probable-max formula uses natural log (ln N), not log; standard form is √(ln N)+0.2886/√(ln N). Using "\log" is ambiguous/likely wrong. | Use `\ln N` (or `\log_e N`). |
| part-02/ch-01.md | 1891 | Bretschneider period density: the prefactor should be in terms of normalized τ (T/T̄), denominator should be T̄⁴ not T̄; as written T³/T̄ is dimensionally wrong | Should be `2.7\frac{T^3}{\bar T^4}\exp[-0.675(T/\bar T)^4]` or fully in τ. |
| part-02/ch-01.md | 1933-1934 | T̄_z = 2π√(m0/m2) conflicts with Eq II-1-152 (line 2090) `T_z = √(m0/m2)` (no 2π) because moments here are in radian vs cyclic frequency; the 2π factor is incon | Note the radian-vs-Hz moment convention, or reconcile the 2π. |
| part-02/ch-01.md | 1980, 1991 | The η(t) Fourier series (II-1-142) is written with A_n,ε_n but the following text (1983) and Eq II-1-143 (1995) define a_n,b_n; the a_n/b_n cosine+sine form of  | Add the a_n cos + b_n sin form of η(t), or reconcile A_n/ε_n with a_n/b_n. |
| part-02/ch-01.md | 2021 | The integrand `\sin^2 2\pi ft` with measure `d(2\pi ft)` over 0..2π is inconsistent with the stated "variance over wave period of 2π" (mixes ωt and 2πft variabl | Make the integration variable consistent (use ωt = 2πft uniformly). |
| part-02/ch-01.md | 2040 | Spectral moment integrand `E(t)` should be `E(f)` (function of frequency, integrated df). | `m_i = \int_0^\infty f^i E(f)\,df`. |

### Formatting (other)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 140 | The Symbol-font bullet glyph was converted to literal `!`; the bulleted assumption list is collapsed into one paragraph. | Replace each `!` with a list bullet and render as a Markdown list. |
| part-02/ch-01.md | 1192 | Same garbled `T %& g & / & d` and unformatted `L2 H/d3`. | $T\sqrt{g/d}$ and $L^2H/d^3$. |

### Glyph substitutions (math)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 928 | Garbled glyph: overbar P (mean power, P̄) rendered as "P6"; recurs at line 929 `P6 = E C_g sin θ`. | Replace "P6" with "P̄" (mean wave power). |
| part-02/ch-01.md | 1166 | Garbled glyph string `T %& g & / & d` (a leaked OCR rendering of T√(g/d)). | Render as $T\sqrt{g/d}$. |
| part-02/ch-01.md | 1449, 1477 | Glyph error: the expansion parameter ε (epsilon) rendered as "0"; recurs line 1477 `0 = kH/2`. | "ε = kH/2 rather than ε = ka". |

### Grammar

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 1062 | Garbled sentence (the "or ... deeper water" clause is wrong/contradictory in shallowing context). | Reword per source; likely "...travel faster because of amplitude dispersion, i.e., higher portions travel faster." |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-01.md | 971-991 | The "Summary of linear (Airy) wave theory" table (Figure II-1-9) lost all its content cells in conversion; it is an empty skeleton. | Mark as image-based figure or restore the table content from the source PDF. |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-02.md | 112 | Two `where`-list entries merged into one line; LaTeX rendered as inline text rather than math; the `c =` definition is merged onto the `f` line | Split into separate list items and wrap math in `$...$`: `f = ` and `c = characteristic velocity` on its own line |
| part-02/ch-02.md | 232 | Equation II-2-4 first equality is dimensionally wrong: `\rho_a U_z^2` should be `\rho_a C_{Dz} U_z^2` only; the bare `\rho_a U_z^2` term is a conversion error ( | Remove spurious first term: `\tau = \rho_a C_{Dz} U_z^2` |
| part-02/ch-02.md | 335 | Equation II-2-10 uses `p_a` (pressure) where it should be `\rho_a` (air density); the geostrophic balance divides by density, not pressure | Correct to `U_g = \frac{1}{\rho_a f}\frac{dp}{dn}` |
| part-02/ch-02.md | 372 | Same `p_a` vs `\rho_a` density error in gradient-wind Equation II-2-11 | Correct to `\frac{1}{\rho_{a}f}` |
| part-02/ch-02.md | 445 | Example II-2-5 math: ambiguous grouping `1/1.236\times10^{-7}` (no parentheses) renders as `(1/1.236)*1e-7` which is wrong; the `(a)` step-label is embedded in  | Parenthesize denominator `1/(1.236\times10^{-7})` and move step labels out of the math fence |
| part-02/ch-02.md | 688 | Equation II-2-26 LaTeX is garbled: `\ b f` is invalid; should be `\hat{f}_p`; exponent `\hat{m}_2` should be `m_2` | Fix to `\hat{f}_p = \lambda_2 \hat{X}^{m_2}` |
| part-02/ch-02.md | 697 | Equation II-2-27: dimensionless time should be `g t / u_*` — consistent with II-2-38 usage `gt/u_*`; OK dimensionally but II-2-23/II-2-22 use `u_*^2`; verify —  | Verify cross-reference "Equations II-2-26 and II-2-27 imply that waves will continue to grow" — these are frequency rela |
| part-02/ch-02.md | 721 | Equation II-2-37 left side `gH_{m_*}/u_*^2` has subscript `m_*` (should be `m0`), a conversion typo | Correct subscript to `H_{m0}` |
| part-02/ch-02.md | 733 | `\propto` (proportional-to symbol) used where `\alpha` (Phillips' constant) is intended (II-2-31); same error at lines 740, 759 with `\infty` for `\alpha` | Replace `\propto`/`\infty` with `\alpha` |
| part-02/ch-02.md | 740, 759 | `\infty` (infinity) used in place of `\alpha`; will mis-render | Replace `\infty` with `\alpha` |
| part-02/ch-02.md | 768 | Text says `\sigma_b` value but writes `f_b = 0.09`; should be `\sigma_b = 0.09` (a sigma parameter, not f) | Correct to `\sigma_b = 0.09` |
| part-02/ch-02.md | 799 | Stray `*` superscript artifact on the coefficient in growth-law equation (II-2-36 group) | Remove `*`: `4.13 \times 10^{-2}` |
| part-02/ch-02.md | 826 | Fully-developed wave-height eq II-2-37: subscript `H_{m_*}` is a typo for `H_{m0}` | Correct subscript |

### Glyph substitutions (math)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-02.md | 513 | Garbled/Private-Use (Sinhala/Tamil) glyphs `ඥ݃݀` where `\sqrt{gd}` (shallow-water long-wave speed) belongs | Replace with `$\sqrt{gd}$` |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-02.md | 123-128 | Table II-2-1 powers-of-ten inconsistent: some are LaTeX (`10^{1}`), some plain (`10-1`, `> 10 6` = "10 6" with a space) | Normalize all exponents to LaTeX, e.g. `$10^{-1}$`, `$>10^{6}$` |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-03.md | 184 | Equation II-3-3 wave phase function is missing the spatial multipliers: should be `k x \cos\theta + k y \sin\theta - \omega t`; `x` and `y` dropped | Restore `k(x\cos\theta + y\sin\theta) - \omega t` |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-03.md | 311 | Depth list is out of order/duplicated (`...20, 10, 16, 14, 12, 10, 8...` — `10` appears twice, `18` missing though Table II-3-1 has 18) | Correct to monotonic list `...20, 18, 16, 14, 12, 10, 8, 6, 4` |
| part-02/ch-03.md | 387-388 | Table II-3-1 caption is replaced by leaked body-paragraph text (the preceding sentence), not the real title "Example Problem Refraction and Shoaling Results" | Restore caption: `Table II-3-1. Example Problem Refraction and Shoaling Results` |
| part-02/ch-03.md | 643 | Table II-3-2 caption replaced by leaked body text; real title is "Guidance for Selection of Wave Transformation Methods" | Restore proper caption |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-04.md | 154 | Equation II-4-11 (modified Miche): `tan h` is broken `\tanh` and `0.1` should be `0.14` per Eq II-4-18 (`H_{max}=0.14L\tanh(kd)`); also `L` not in math | Correct to `H_{mo,b} = 0.14\,L\tanh(kd)` (verify coefficient) and fix `\tanh` |
| part-02/ch-04.md | 188 | Equation has same symbol both sides: should be `H_o' = K_R H_o` (equivalent unrefracted deepwater height); the prime is dropped, making `H_o = K_R H_o` self-con | Restore prime: `H_o' = K_R H_o` |
| part-02/ch-04.md | 393 | Eq II-4-24 application: the `+` between `(3.2+0.14)` and the bracket term should be `×` (multiply h_b by the bracket factor); shown as addition, which does not  | Correct operator to multiplication |
| part-02/ch-04.md | 531, 534 | Equation II-4-33 lists `u_t` (tidal) but the prose calls `u_i` the tidal current and also `u_i` the infragravity flow — `u_i` defined twice, `u_t` undefined | Fix: `u_t` = tidal current; `u_i` = infragravity oscillatory flow (each once) |

### Word merges (context-specific)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-04.md | 610, 616 | Broken cross-reference: `II-4-4037` is a merged/garbled equation number; context (Komar Eq II-4-40 vs Fig caption II-4-37) is inconsistent | Correct to the intended single equation number (II-4-40) |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-05.md | 340 | In the where-list for Eq. II-5-16, the symbol κ (kappa) was OCR'd as the digit "6"; the variable is κ_n | Change to "κ_n = epoch of constituent n" |
| part-02/ch-06.md | 422 | Unbalanced parentheses in the numerator: `(1.30/2 (1.9)(10^7) 3.42` is missing a close paren after 1.30/2 | Correct to `((1.30/2) (1.9) (10^7) (3.42))` |
| part-02/ch-06.md | 661 | Wrong subscript: ebb discharge Q_maxe is computed from U_maxf but uses the ebb velocity value 2.08 (U_maxe); the multiplier should be U_maxe | Change `Q_{maxe} = U_{maxf} A_c` to `Q_{maxe} = U_{maxe} A_c` |

### Duplicated text

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-07.md | 1218 | Duplicated term: form-drag term written as `F_{c,fric}` twice; missing form drag | Correct to `F_{c,tot} = F_{c,form} + F_{c,fric} + F_{c,prop}` |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-07.md | 376 | `#` used for ≤ and `$lgt^{2}$` is garbled ($d_s/gT^2$); will not render correctly | Replace with `0.0157 ≤ d_s/gT^2 ≤ 0.0793` |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-07.md | 423-441 | Caption garbled (body sentence merged into title) and the entire table is duplicated | Restore caption to "Table II-7-1. Wave Reflection Equation Coefficient Values" and delete the duplicate table |
| part-02/ch-07.md | 885-900 | Garbled caption (body text), and OCR typos "Salacted"/"Haights"/"Saransan 1973h" in the duplicated header row | Fix caption to "Table II-7-5. Selected Vessel-Generated Wave Heights (Sorensen 1973b)" and remove garbled duplicate |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-08.md | 708 | Equation number tagged `II-9-6` in Chapter 8 (should be II-8-x); wrong chapter prefix | Renumber tag to the correct II-8-x value |
| part-02/ch-08.md | 811 | Equation number tagged `II-9-7` in Chapter 8; wrong chapter prefix | Renumber tag to correct II-8-x |
| part-02/ch-08.md | 1161-1162 | Malformed/garbled non-dimensional frequency: `(\sqrt{gd}/g)^{1/2}` is dimensionally wrong and lacks an equation tag; intended Ω = (2π/T)(d/g)^(1/2) or (2π/T)√(d | Correct to `\Omega = \frac{2\pi}{T}\sqrt{\frac{d}{g}}` and add proper tag |
| part-02/ch-08.md | 233-237 | Math fully garbled by OCR (`'` for =, `&` for minus, fractions destroyed); these PDF-image equations did not convert to valid LaTeX | Re-typeset the Figure II-8-2 Part-2 distribution PDFs as proper LaTeX |
| part-02/ch-08.md | 272-276 | Plotting-position formulas garbled (`'` for =, `%` for +, `&` for −, `Fˆ` split); will not render | Re-typeset, e.g. `\hat{F}_m = 1 - m/(N+1)` and the Gringorten/Goda/Blom forms |

### Formatting (other)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-08.md | 5 | Frontmatter chapter title truncated ("AND" dangling); should be full title | Set title to "HYDRODYNAMIC ANALYSIS AND DESIGN CONDITIONS" |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-08.md | 24-25 | The `II-8-2. Identifying Meteorological and Hydrodynamic Processes Impacting Design` entry is broken: heading number/text lost, only the tail "Impacting Design" | Restore ToC line "II-8-2. Identifying Meteorological and Hydrodynamic Processes Impacting Design" |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-02/ch-08.md | 929, 1098, 1124 | Table captions are body sentences (caption text lost), and Table II-8-13 is duplicated in full at lines 1100-1148 | Restore proper captions; remove duplicate copy of Table II-8-13 |
| part-02/ch-08.md | 218-227 | Multi-row math cells misaligned/merged so the FT-II mean & SD expressions are orphaned and Weibull "general" row lacks its label | Re-associate distribution-function labels with their math rows |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-01.md | 250 | Malformed LaTeX subscript `M_{\ L_{\Phi}}` (stray backslash-space and bogus nested subscript); should be mean grain size in phi | Render as `M_{\varphi} = \frac{\varphi_{16}+\varphi_{50}+\varphi_{84}}{3}` |
| part-03/ch-01.md | 670 | Garbled LaTeX: `1 \hat{0}^{-7}` (stray hat over 0) should be `10^{-7}` | Render as `C_D = 24/(7.2\times10^{-7}) = 3.3\times10^{7}` |
| part-03/ch-01.md | 675-679 | Two distinct equations crammed in one ```math fence with a bare newline; will not render as intended math | Split into two separate `math` fences (one for W_f, one for Re) |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-01.md | 443 | Author name inconsistent: "Hardin" (List of Figures, line 79) vs "Handin" (text and reference, lines 443, 454, 914). Reference list spells it "Handin" | Correct line 79 List-of-Figures entry to "Handin 1966" |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-01.md | 153 | Body sentence fragment captured as the bold table caption (caption garbled from leaked text) | Replace with the real caption `**Table III-1-2. Sediment Particle Sizes**` |
| part-03/ch-01.md | 433-435 | Table-5 footnotes (lines 435-439) inserted into the middle of a sentence, splitting "...in compression, / which is equivalent to crushing strength" | Move the footnote block out of the sentence so the sentence reads continuously |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-02.md | 111 | Subscript `Q_ℓ` (script-l) consistently OCR'd as `Q_R` with the direction letter (L/R/NET/GROSS) detached; notation badly garbled throughout paragraph | Restore proper subscripts: `Q_{\ell,L}`, `Q_{\ell,R}`, `Q_{\ell,NET}`, `Q_{\ell,GROSS}` |
| part-03/ch-02.md | 625 | Wrong units: transport rate result given as `m^3/s^2`; should be `m^3/s` (volume rate) | Change exponent to `m^3/sec` |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-02.md | 648 | An entire body paragraph captured as the bold table caption; caption begins with a stray "., the associated..." | Replace with a proper caption (e.g. `**Table III-2-2 (cont.). Occurrence of Wave Height and Period ...**`) and keep the  |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-03.md | 470 | Equation III-3-21 is malformed: it has no relational operator. The `- 1` should be `= 1` (the conditions for intersecting/nonintersecting profiles equate to 1). | Change to `\Delta y' + \left(\frac{1}{A'}\right)^{\frac{3}{2}} = 1`. |
| part-03/ch-03.md | 824 | Equation is mangled: the fraction $W_*/(h_*+B)$ is broken into a bad subscript and the result `≈ 0.17 m/yr` was pulled into the denominator. | Rewrite as `\frac{dR_{\infty}}{dt} = \frac{dS}{dt}\,\frac{W_*}{h_*+B} \approx 0.17 \text{ m/yr}`. |
| part-03/ch-03.md | 1064 | The two-relation form (`> or <`) does not render cleanly as a single inequality, and the surrounding text (line 1067) refers to "Equation 3-53" for the transpor | Render as a clearly-labeled criterion and correct the cross-reference so the steepness-direction rule cites Equation 3-5 |

### Glyph substitutions (math)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-03.md | 318 | The overbar symbol on the mean wave height ($\overline{H}$) was OCR'd as a stray `6`; same glyph appears as `H 6` elsewhere. | Change `H 6` to `$\overline{H}$` (annual mean significant wave height). |
| part-03/ch-03.md | 577 | Same corrupted overbar glyph: `H 6` should be the mean significant wave height $\overline{H}$. | Change `H 6` to `$\overline{H}$`. |

### Grammar

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-03.md | 309 | Garbled text: "these award limit" is an OCR corruption of "the seaward limit"; sentence is ungrammatical. | Change to `but rather the seaward limit to which the depositional front has advanced`. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-04.md | 571 | Table III-4-2 caption is garbled: the title "Predictive Capability of Sand Transport Equations (Chapman 1990)" was lost, leaving `).`. | Restore caption: `Table III-4-2. Predictive Capability of Sand Transport Equations (Chapman 1990)`. |
| part-03/ch-04.md | 1607-1654 | Table III-4-16 is badly mis-parsed: the running body text of the example was merged into the table grid and the whole malformed table is duplicated verbatim. | Rebuild Table III-4-16 as the simple (mph, cm/sec) speed table and remove the duplicated/embedded prose. |
| part-03/ch-04.md | 1796, 1856 | Table bold-captions were filled with the body paragraph text instead of the table title (and Table III-4-23 is duplicated, lines 1856 and 1877). | Replace with the proper titles (Table III-4-21 "Calculated Dune Sand Size Distribution"; Table III-4-23 "Corrected Trans |

### Formatting (other)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-05.md | 682 | Citation author name "Pinekin" is wrong; the reference list (line 949-951) and other in-text cites (line 400) use "Pinchin" — broken/incorrect cross-reference. | Correct to "Nairn, Pinchin, and Philpott (1986)". |

### Word merges (context-specific)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-05.md | 1059 | Broken math delimiter: a stray escaped `\$` opens the value instead of `$`, so "1,000kg/m^{3}" will not render correctly; also value is run together with units. | Fix to `fresh water = 1,000 $kg/m^{3}$ or 1.94 $slugs/ft^{3}$`. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-05.md | 672 | Entire paragraph of body text from line 670 is duplicated and mislabeled as a bold "Table III-5-3." caption immediately above the actual table. | Remove the duplicated bold paragraph; replace with the proper table title, e.g. `**Table III-5-3. Erodibility Coefficien |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-06.md | 354 | Garbled OCR of an equation: should read "iteration started by choosing x^(0) = 4√f_w = 0.4"; symbols and subscript "w" are scattered/misplaced. | Reconstruct as `x^{(0)} = 4\sqrt{f_w} = 0.4`. |
| part-03/ch-06.md | 355 | Severely garbled equation fragment: prime/subscript/relational symbols lost and reordered ("'(" for "≈", scattered "z", "u ( wm )" for u_{*wm}). Text is not rea | Reconstruct the intended relation, e.g. `\omega/(\kappa u_{*wm}) \approx (0.12/f_w)(k_n/A_{bm})`; verify against source  |
| part-03/ch-06.md | 461-462 | Iteration value "08.29" is malformed (should be 0.829), and the trailing "= , or the 4 4 f ... w 8 fw" is garbled OCR of "= 4√(4 f_w)". | Fix "08.29" → "0.829" and reconstruct the friction-factor relation `x^{(6)} = 0.686 = 4\sqrt{4 f_w}`. |
| part-03/ch-06.md | 489, 766, 821, 1139, 1213, 1725 | The right-arrow symbol (→ / ⇒) was converted to the literal word "arrow" inside math fences; it will render as text "arrow", not an arrow. | Replace "arrow" with `\rightarrow` (or `\Rightarrow`) in each math expression. |
| part-03/ch-06.md | 400 | Cross-reference error: the rough/smooth turbulent flow criterion is Equation 6-5, not 6-15 (which is the shear-velocity relation). Step 5 (line 401) also refere | Change "Equation 6-15" to "Equation 6-5" in steps 4, 5, and 8 of this procedure. |
| part-03/ch-06.md | 397 | Garbled equation/prose: "= , H ... T = significant s / 2 wave period" is scrambled; the relation H_rms = H_s/√2 and "T = significant wave period" got interleave | Reconstruct: "H = H_rms = H_s/√2; ω = 2π/T with T = significant wave period". |
| part-03/ch-06.md | 1773 | Garbled: should state "height H_rms = H_s/√2 and period T = T_s"; OCR scrambled the symbols ("' hs / 2", "rms"). Also "hs" should be H_s. | Reconstruct as "height H_rms = H_s/√2 and period T = T_s". |

### Formatting (other)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-03/ch-06.md | 891 | Figure III-6-7 caption cites "Raudkivi (1967)" but the body text (line 89, 885) and all other Raudkivi cites use "Raudkivi (1976)" — broken/inconsistent citatio | Correct caption to "Raudkivi (1976)". |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-04/ch-01.md | 793,795 | Reference heading "Komar 1998" is followed by the citation for Komar 1976 (a different work); the 1976 entry is also duplicated under "Komar 1998" while the act | Correct heading/citation pairing; add the real Komar 1998 reference. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-04/ch-01.md | 225,325,368,429,493,525 | Every numbered table has a duplicated caption (one italic, one bold) stacked right before the table. | Keep a single caption per table. |
| part-04/ch-01.md | 493 | Table IV-1-6 caption is garbled: it begins with ")." and then reproduces an entire body paragraph (from line 487) as the table title instead of "Major World Cit | Replace caption with "Table IV-1-6. Major World Cities with Recorded Subsidence". |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-04/ch-02.md | 187,226 | Table IV-2-1's bold caption is a leaked body sentence (from line 185), not the table title "Classification of Coasts"; appears on both halves of the split table | Replace both with "Table IV-2-1. Classification of Coasts". |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-04/ch-02.md | 549,562 | Table IV-2-2 caption garbled (starts ").") and reproduces a full body paragraph as the title; additionally the entire table (caption + 10 data rows) is duplicat | Set caption to "Table IV-2-2. Worldwide Distribution of Barrier Island Coasts" and delete the duplicate copy. |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-04/ch-03.md | 471 | Section number wrong: this is chapter IV-3, so it should be IV-3-5, not "IV-4-5" (TOC at line 71 lists it as part of IV-3). | Change "IV-4-5" to "IV-3-5". |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-01.md | 98 | Closing parenthesis and period pulled inside the `$...$` math span, breaking the math/text boundary. | `5 $ft^{3}/sec$).` |

### Formatting (other)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-02.md | 444 | Broken cross-reference: "V-5-12" should be "V-2-12" (chapter is V-2; the figure is V-2-12, shown at line 448). | `Figures V-2-12 and V-2-13 are photographs...` |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-03.md | 503 | LaTeX fraction contains unescaped multi-word text with spaces; "Wall Trap Volume"/"Active Sediment Volume" will render run-together in italics. | Wrap in `\text{...}`: `WTR = \frac{\text{Wall Trap Volume}}{\text{Active Sediment Volume}}`. |
| part-05/ch-03.md | 747 | Equation garbled: an expression is missing after "involving" and the inline symbols "2 L YL g s" are scrambled LaTeX fragments embedded in prose. | Restore the intended expression (e.g., $Y_s/L_s$ vs $L_g/L_s$) and remove the stray "2 L YL g s" fragment. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-03.md | 619 | Table V-3-4 "title" is an entire body paragraph captured as the bold caption; the real title is "Summary of U.S. Breakwater Projects." | `**Table V-3-4. Summary of U.S. Breakwater Projects (from Chasten et al. 1993)**` |

### Duplicated text

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-04.md | 260 | Equation V-4-4 is malformed: the final term (a sorting/σ expression) does not belong on the right side of the mean-difference ratio; it makes the equality dimen | Restore Eq. V-4-4 to `(M_{φb}-M_{φn})/σ_{φn} = ([·]_b - [·]_n) / σ_{φn}` with the mean expression only. |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-04.md | 425 | Spurious `\nabla` (∇) operator inserted into Equation V-4-6; the equation is simply V = W(B + D_C) (confirmed by Example use `V = 30(2.5 + 6) = 255` at line 476 | `V = W \left( B + D_C \right)` |
| part-05/ch-04.md | 666,674 | Same quantity given two contradictory definitions in adjacent Given blocks: group celerity is `(g h_b)^{1/2}` (line 666) but written as `(g h_b)^2` (line 674);  | Use the shallow-water form consistently: `C_{gb} = (g h_b)^{1/2}` and remove `\dot`. |
| part-05/ch-04.md | 264-267 | Symbol definitions use OCR-mangled tokens "FNb/FNn/MNn/MNb" for what the equations write as σ_{φb}/σ_{φn}/M_{φn}/M_{φb}; the Greek φ/σ glyphs were lost. | Replace with `σφb`, `σφn`, `Mφn`, `Mφb` to match Eqs. V-4-3/V-4-4. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-04.md | 1084 | OCR corruption in Table V-4-1 header: "Years 1 to 31" should be "Years 1 to 3" (Phase I is the first 3 years per body text line 1077; later columns are "Years 1 | `...Project Years 1 to 3` |

### Typos

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-04.md | 164 | OCR corruption: "El NiZo" should be "El Niño" (the ñ glyph became "Z"). | `(e.g., El Niño)` |

### Word merges (context-specific)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-05.md | 1063 | "OceanAugust" merged words; a stray date ("August 7, 2000") is fused to the body text — likely a leaked timestamp/edit artifact. | Separate words and remove/relocate the stray date: "...hindcasts in the Pacific Ocean." |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-06.md | 368 | Symbol garbling: variables s (specific gravity), n (porosity), and h_* (depth of closure) are all rendered as "g". Four different quantities collapsed to "g". | Restore distinct symbols: s (≈2.65), n (≈0.4), h_* (depth of closure), B (berm height). |
| part-05/ch-06.md | 365 | Exponent error: `H_b^{25}` should be `H_b^{2.5}` (cf. line 415 where it is correctly `H_b^{2.5}`). | Change exponent to 2.5. |
| part-05/ch-06.md | 891 | Numerator inconsistency: A_1 was computed as 0.677 m (line 873), then used as 0.0667 m in the numerator and 0.667 m in the denominator — three different values  | Use a consistent A_1 value throughout and recompute H_b. |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-06.md | 446-458 | Table V-6-3 content is replaced by a duplicated, leaked List-of-Tables fragment (page-leader dots), and the block is duplicated. The actual Table V-6-3 (impound | Replace with the correct Table V-6-3 data; remove the duplicated LoT fragment. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-06.md | 675-680 | Table V-6-6 (even-odd data for Example V-6-5) is replaced by a leaked List-of-Tables fragment; the table caption merged with body text. | Restore the actual Table V-6-6 data; remove leaked LoT fragment. |

### Headings / TOC / lists

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-05/ch-07.md | 21-23 | Table of Contents is broken: section V-7-3 entries are mislabeled as bare "Mitigation" (twice) and the V-7-3a/b headings (lines 95, 103) are missing from the TO | Restore the V-7-3 entries (Habitat Trade-offs / Habitat Restoration) and remove the duplicated stray "Mitigation" lines. |
| part-05/ch-07.md | 46-47 | TOC entry for V-7-8 ("Environmental Features of Traditional Coastal Engineering Projects", see line 241) is reduced to a bare "Projects"; section number/title m | Restore the full V-7-8 TOC entry. |
| part-06/ch-04.md | 76-77 | List of Figures entries VI-4-3 and VI-4-4 lost their figure numbers (just "Figure Selective placement") | Restore "Figure VI-4-3. Selective placement" and "Figure VI-4-4. Special placement" |

### Word merges (context-specific)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-04.md | 477 | LaTeX has spaces inserted into every token ("3 3", "E n g l i s h U n i t s"), a malformed subscript `f _ { _ c }` (double underscore), and "EnglishUnits" run t | Rewrite as `E_c = 33\,(w_c)^{3/2}(f_c)^{1/2} \quad \text{(English Units)}` with correct subscript `f_c` |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-04.md | 434-472 | Table VI-4-6 body replaced by LoT rows; Table VI-4-7 caption is a truncated sentence and the data table is duplicated | Provide Table VI-4-6 content; complete the VI-4-7 caption; remove the duplicate |

### Apostrophe glyphs (non-í)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-05.md | 99 | OCR rendered the apostrophe in "d'Angremond" as `=`. Recurs widely (lines 233, 752, 2602, etc.). | Replace `d=Angremond` with `d'Angremond`. |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-05.md | 534 | Subscripted symbols collapsed into stray letters: "2 B s d H", "R d u B 2%", "2 B Hs" are unreadable garbled math from lost subscripts. | Reconstruct as "higher than 2H_s above SWL ... R_u2% if d_B > 2H_s", etc. |
| part-06/ch-05.md | 4446 | Strain-rate symbols rendered as literal `\&` (lost ε̇ glyphs); LaTeX will not render `\&_{...}`. Same `\&`/`\mathbf{v}` corruption in surrounding text (lines 44 | Replace `\&` with the proper dotted-strain symbol (e.g. `\dot{\varepsilon}`). |
| part-06/ch-05.md | 5173-5177 | Explanatory English sentence is trapped inside the ```math fence, so the block will not render as LaTeX. | Move the "if the quantity..." note outside/below the ```math fence. |
| part-06/ch-05.md | 1718 | Equation number `(VI-5-71)` was merged into the math as a stray `- 5 - 71)` term instead of a `\tag`. Same defect at line 1733 (`- 5 - 72)`) and 1779-region. | Replace trailing `- 5 - 71)` with `\tag{VI-5-71}`. |

### Glyph substitutions (math)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-05.md | 250 | Symbol-font registered-trademark glyph decoded as digit `7` (ACCROPODE® / CORE-LOC®). Recurs at 251, 252, 1230, 1600, 1601, 1918, 1944, 1977, 2225. | Replace trailing `7` with `®`. |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-05.md | 488 | Table caption contains body prose, not the table title; the table body below is leaked LoT text. Same defect pattern recurs for Tables 4, 5, 13, 21, 39, 40, 41, | Restore correct title "Surface Roughness Reduction Factor γr ..." and the real table body. |
| part-06/ch-05.md | 571, 584 | Table VI-5-4 (Test Program) title is empty and body is replaced by leaked List-of-Tables rows; the table is duplicated (584 repeats 571). | Restore Test Program table content; remove duplicate/leaked block. |
| part-06/ch-05.md | 4934-4948 | Table VI-5-85 "where" block is heavily garbled OCR: u0 formulas for tides/waves and the A= expression are unreadable; "Ma..c;s density", "Oedometric" label orph | Reconstruct: u0 = ρw g Δ (tides), u0 = ρw g H / [2 cosh(2πd/L)] (waves); A = (π/(kE_oed T))^0.5; "Mass density of water" |
| part-06/ch-05.md | 4101-4103 | Caption is body prose; also "International Standards Organization (IS)" should be "(ISO)". | Restore title "Fractional Limits of Grain Sizes According ISO/CEN" and fix "(IS)" → "(ISO)". |
| part-06/ch-05.md | 4460 | Table VI-5-75 collapsed into a single run-on paragraph; rows/columns merged so values cannot be associated with materials. | Reconstruct as a proper Markdown table with Material / d50 / dmax / φ'crit columns. |

### Typos

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-05.md | 142 | "landwater" should be "landward"; recurs in caption at line 3732. | Change to "landward". |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-06.md | 165 | Missing relational operator; should read g ≤ 0. | "where g ≤ 0". |
| part-06/ch-06.md | 275 | Both the basic and normalized vectors are labeled \overline{Z}; the basic variable vector should be \overline{X}. | "basic variables \overline{X} = (X_1,...) into ... \overline{Z} = (Z_1,...)". |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-06.md | 797 | Wrong/garbled table caption: this is the partial-safety-factor table for Table VI-6-4, not "Table VI-5-22. )". Recurs at lines 864, 884, 904, 1005, 1026, etc. | Remove stray ") " captions / correct to the proper Table VI-6-x caption. |

### Equation correctness (semantic)

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-07.md | 838 | Subscript error: "gH_3^3" should be "gH_s^3" (the 3 is a mis-OCR of subscript s). | "\sqrt{g H_s^3}". |
| part-06/ch-07.md | 846-848 | The literal word "arrow" appears in the LaTeX where an arrow symbol (→/←) was intended. | Replace "arrow" with "\leftarrow" (or →). |
| part-06/ch-07.md | 1223 | Stray "\square" placeholder where a multiplication operator belongs (K_D·cot α). | "(3.5 × 2.0)^{1/3}" (or \cdot). |
| part-06/ch-07.md | 1231 | Stray "\Box" glyph for the multiplication operator inside the cube root. | "(2.0 × 2.0)^{1/3}". |
| part-06/ch-07.md | 1277 | Malformed: the exponent 1/(P+0.5) has been turned into a spurious factor (P/(P+0.5)); inconsistent with the correct form at line 1119: [6.2 P^0.31 (tan α)^0.5]^ | "\left[6.2 P^{0.31}(\tan\alpha)^{0.5}\right]^{1/(P+0.5)}". |
| part-06/ch-07.md | 1301 | Nested fraction "0.5/2π" appears garbled — the numerator should contain 2π·H-related terms, not "0.5"; likely dropped symbols from the surf-similarity substitut | Verify against source; restore the correct radicand (2π/(gT_m²) form). |
| part-06/ch-07.md | 2210 | Garbled middle term "gh_p \cdot 20 ft": stray "gh_p" inserted; should simply be h* + s = 20 + 8.1 = 28.1 ft. | Remove "gh_p"; "h' = h* + s = 20 ft + 8.1 ft = 28.1 ft". |

### Table structure

| File | Line | Issue | Suggested fix |
| --- | --- | --- | --- |
| part-06/ch-08.md | 64 | PDF running-footer (chapter title) leaked onto the end of the List-of-Tables entry for Table VI-8-14. | Remove trailing "Monitoring, Maintenance, and Repair of Coastal Projects". |
| part-06/ch-08.md | 178 | Table caption is a duplicate of the surrounding body paragraph (lines 176-177) merged into the bold caption line, not an actual table title. | Replace with proper caption "Table VI-8-2. General Condition Index Scale". |
| part-06/ch-08.md | 191,200 | Table VI-8-4 has an empty caption and is printed twice (lines 192-198 and 202-208). | Add the caption "Functional and Structural Rating Categories" and remove the duplicate. |
| part-06/ch-08.md | 293 | Table caption is body-paragraph text merged into the caption; the table shown is actually Table VI-8-6 reused as a stand-in for VI-8-7. | Provide the real Table VI-8-7 (Rating Guidance for Armor Loss) with proper caption. |
