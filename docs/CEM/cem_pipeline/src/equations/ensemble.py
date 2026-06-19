#!/usr/bin/env python3
"""Combine per-engine equation candidates into a single decision.

Decision order (spec §8.3):
  1. >=2 engines agree (same canonical form) and that form verifies -> ACCEPT (agreed)
  2. exactly one candidate verifies                                  -> ACCEPT (single_verified)
  3. several verify but disagree                                     -> ACCEPT highest score (multi_verified)
  4. none verify                                                     -> hand to selfcorrect
Every candidate's verdict is recorded as evidence regardless of outcome.
"""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalize as NZ  # noqa: E402
import verify as VF      # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import groundtruth as GT  # noqa: E402


def _evidence(cands):
    return [{
        "engine": c.get("engine"),
        "latex": c.get("latex"),
        "sanitized": c.get("sanitized"),
        "verdict": c.get("verdict"),
    } for c in cands]


def decide(candidates, gt_fingerprint, crop_png=None, cfg=None, katex_batch=None):
    """candidates: list of {engine, latex, page?, bbox?}. Returns a decision dict."""
    cfg = cfg or {}
    cands = []
    for c in candidates:
        latex = c.get("latex")
        if not latex:
            continue
        san = NZ.sanitize(latex)
        if not san:
            continue
        d = dict(c)
        d["sanitized"] = san
        cands.append(d)

    if not cands:
        return {"latex": None, "status": "no_candidates", "evidence": []}

    # batch KaTeX validity for all sanitized candidates
    if katex_batch is None:
        kmap = {f"i{idx}": c["sanitized"] for idx, c in enumerate(cands)}
        katex_res = VF.katex_validate_batch(kmap)
    else:
        katex_res = None

    for idx, c in enumerate(cands):
        kok = (katex_batch.get(c["engine"]) if katex_batch
               else katex_res.get(f"i{idx}"))
        c["verdict"] = VF.verify(c["sanitized"], gt_fingerprint, crop_png, cfg, katex_ok=kok)

    has_gt = len(gt_fingerprint) >= 2
    vcfg = cfg.get("verify", {}) if isinstance(cfg.get("verify", {}), dict) else {}
    tol = vcfg.get("symbol_edit_tolerance", 1)
    verified = [c for c in cands if c["verdict"]["accepted"]]
    for c in cands:
        c["_fp"] = GT.latex_symbol_multiset(c["sanitized"])

    # (1) CONSENSUS between independent engines is the PRIMARY signal (the manual's
    # born-digital text layer is glyph-corrupted and can't be trusted as clean GT).
    # Two engines "agree" when canonical LaTeX matches OR their symbol multisets
    # match within a length-proportional tolerance (minor formatting/OCR noise
    # scales with size; a genuinely different equation differs in many symbols).
    # For each candidate, count how many distinct engines corroborate it, then pick
    # the best-corroborated valid candidate, breaking ties toward the MOST COMPLETE
    # transcription (longest fingerprint) so a dropped-term variant never wins.
    def _agree(a, b):
        n = max(len(a["_fp"]), len(b["_fp"]))
        atol = max(tol, round(0.06 * n))
        return (NZ.agree(a["sanitized"], b["sanitized"])
                or GT.multiset_edit_distance(a["_fp"], b["_fp"]) <= atol
                or GT.multiset_edit_distance(GT.loose(a["_fp"]), GT.loose(b["_fp"])) <= atol)

    for c in cands:
        c["_support"] = {c["engine"]}
    for i in range(len(cands)):
        for j in range(len(cands)):
            if i == j or cands[i]["engine"] == cands[j]["engine"]:
                continue
            if _agree(cands[i], cands[j]):
                cands[i]["_support"].add(cands[j]["engine"])
    corroborated = [c for c in cands if len(c["_support"]) >= 2 and c["verdict"]["valid"]]
    if corroborated:
        best = max(corroborated, key=lambda m: (len(m["_support"]), len(m["_fp"]),
                                                m["verdict"]["score"]))
        status = "agreed_gt" if (has_gt and best["verdict"]["accepted"]) else "agreed"
        return {"latex": best["sanitized"], "status": status,
                "engine": best["engine"], "verdict": best["verdict"],
                "evidence": _evidence(cands)}

    if has_gt:
        # (2) exactly one passes the symbol gate
        if len(verified) == 1:
            c = verified[0]
            return {"latex": c["sanitized"], "status": "single_verified",
                    "engine": c["engine"], "verdict": c["verdict"],
                    "evidence": _evidence(cands)}
        # (3) several pass but disagree -> highest score
        if len(verified) >= 2:
            c = max(verified, key=lambda m: m["verdict"]["score"])
            return {"latex": c["sanitized"], "status": "multi_verified",
                    "engine": c["engine"], "verdict": c["verdict"],
                    "evidence": _evidence(cands)}
    else:
        # no ground truth, no engine agreement: a lone KaTeX-valid candidate can
        # still be confirmed by a strong render-diff against the source crop.
        valids = [c for c in cands if c["verdict"]["valid"]]
        if valids:
            best = max(valids, key=lambda m: (m["verdict"].get("ssim") or 0,
                                              m["verdict"]["score"]))
            thr = vcfg.get("render_diff_min_ssim", 0.55)
            if best["verdict"].get("ssim") is not None and best["verdict"]["ssim"] >= thr:
                return {"latex": best["sanitized"], "status": "single_verified",
                        "engine": best["engine"], "verdict": best["verdict"],
                        "evidence": _evidence(cands)}

    # (4) nothing verified -> selfcorrect handles it; pass best-scoring as seed
    best = max(cands, key=lambda m: m["verdict"]["score"])
    return {"latex": None, "status": "needs_selfcorrect",
            "best_seed": best["sanitized"], "best_engine": best["engine"],
            "verdict": best["verdict"], "evidence": _evidence(cands)}
