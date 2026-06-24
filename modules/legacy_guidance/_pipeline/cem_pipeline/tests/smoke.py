#!/usr/bin/env python3
"""Smoke tests for the verification core (spec §14 checkpoints 2,4,5).
Run with the main venv python:  python tests/smoke.py
Requires Node+KaTeX (set CEM_NODE if node not on PATH)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "src")
sys.path[:0] = [SRC, os.path.join(SRC, "equations"), os.path.join(SRC, "engines")]

import groundtruth as GT       # noqa: E402
import normalize as NZ          # noqa: E402
import verify as VF             # noqa: E402
import ensemble as ENS          # noqa: E402
import selfcorrect as SC        # noqa: E402

fails = []


def check(name, cond):
    print(("ok  " if cond else "FAIL") + "  " + name)
    if not cond:
        fails.append(name)


# §13.2 groundtruth fingerprint non-empty, contains expected symbols
gt = GT.symbol_multiset("H = ρ g d / 2")
check("fingerprint non-empty", len(gt) > 0)
check("fingerprint has rho", "rho" in gt)

# §13.4 normalize + verify: correct passes, corrupted fails, dropped var caught
check("sanitize fixes {\\bf}", "\\mathbf" in NZ.sanitize(r"{\bf x}"))
v_ok = VF.verify(r"H = \rho g d / 2", gt)
check("correct latex accepted", v_ok["accepted"])
v_bad = VF.verify(r"H = \rho g d / 2 \frac{1}{", gt)
check("corrupted latex rejected (katex)", not v_bad["valid"])
v_drop1 = VF.verify(r"H = \rho g / 2", gt)   # dropped 'd' -> dist 1, within tolerance
check("single drop tolerated (dist<=1)", v_drop1["symbol_match"] and v_drop1["symbol_dist"] == 1)
v_drop2 = VF.verify(r"H = \rho / 2", gt)      # dropped 'g' and 'd' -> dist 2 > tol
check("two dropped vars caught by symbol check", not v_drop2["symbol_match"])

# §13.5 ensemble: cross-engine agreement is the primary signal (born-digital GT
# is glyph-corrupted in this manual, so two engines concurring is authoritative).
gt2 = GT.symbol_multiset("a + b")
d_agree = ENS.decide([{"engine": "marker", "latex": "a+b"},
                      {"engine": "mineru", "latex": "a + b"}], gt2)
check("ensemble agreement (GT confirms) -> agreed_gt", d_agree["status"] == "agreed_gt")
# two engines agree on a form the (clean) GT does not confirm -> still accepted on agreement
d_agree2 = ENS.decide([{"engine": "marker", "latex": "x+y"},
                       {"engine": "mineru", "latex": "x + y"}], gt2)
check("ensemble agreement (no GT confirm) -> agreed", d_agree2["status"] == "agreed")
# a single unconfirmed engine routes to self-correction
d_none = ENS.decide([{"engine": "marker", "latex": "x+y"}], gt2)
check("single unconfirmed -> needs_selfcorrect", d_none["status"] == "needs_selfcorrect")
# self-correct must never leave a valid candidate unfixed: a lone valid candidate
# is resolved (not left flagged); only a candidate with no valid LaTeX flags.
r = SC.correct("e1", None, gt2, [{"engine": "marker", "latex": "x+y"}],
               {"selfcorrect": {"max_passes": 3}}, {})
check("selfcorrect resolves a lone valid candidate", r["status"] == "resolved")
r2 = SC.correct("e2", None, gt2, [{"engine": "marker", "latex": "x+y \\frac{1}{"}],
                {"selfcorrect": {"max_passes": 3}}, {})
check("selfcorrect flags when no valid LaTeX exists", r2["status"] == "flagged")

print()
if fails:
    print(f"{len(fails)} FAILED: {fails}")
    sys.exit(1)
print("all smoke tests passed")
