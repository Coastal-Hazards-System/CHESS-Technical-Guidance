# CEM Web Conversion — Errata (corrections to the original manual)

_Places where the converted web text intentionally **differs from the printed Coastal
Engineering Manual** because the printed manual itself contains an error. These are distinct
from conversion fixes (font-glyph corruption, OCR artifacts), where the web text restores
what the manual already meant. Each item below changes the manual's printed content and
should be reviewed by a subject-matter expert as a formal erratum. Identified by the
corpus-wide equation audit (vision-LLM re-read of the source crops). Generated 2026-06-25._

| Equation | Printed manual | Web text (corrected) | Rationale |
| --- | --- | --- | --- |
| II-1-133 | `H_{max} = [\sqrt{\log N} + 0.2886/\sqrt{\log N} - …] H_{rms}` | `\ln N` in place of `\log N` | The Longuet-Higgins most-probable-maximum-height relation uses the natural logarithm; the source prints `\log`, which is ambiguous/incorrect for this formula. |
| II-1-148 | `m_i = \int_0^\infty f^i\, E(t)\, df` | `E(f)` in place of `E(t)` | A spectral moment integrates the energy density over frequency, so the integrand must be `E(f)`. The printed `E(t)` is a typographical error. |
| II-3-3 | `\Omega(x,y,t) = (k\cos\theta + k\sin\theta - \omega t)` | `k(x\cos\theta + y\sin\theta) - \omega t` | The wave phase function requires the spatial coordinates `x` and `y`; they are dropped in the printed equation, leaving a dimensionally and physically incomplete expression. |

**Status:** the corrected forms are in the published Markdown. This list records the
divergence from the print edition so the corrections are transparent and auditable, pending
expert sign-off. If strict fidelity to the print edition is later preferred, these three are
the equations to revert (and would then be flagged as suspected original-manual errors).
