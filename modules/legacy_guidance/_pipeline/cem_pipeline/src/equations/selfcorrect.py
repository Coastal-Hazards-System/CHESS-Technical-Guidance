#!/usr/bin/env python3
"""Multi-pass, unattended self-correction for equations the ensemble could not
verify. Each pass adds candidates from progressively stronger / more targeted
sources, then re-runs the full ensemble decision (agreement / born-digital
symbol match / render-diff) over Marker + MinerU + the new candidates. Accepts
as soon as the ensemble verifies; otherwise -> 'flagged' with the best candidate
and full evidence."""
import os
import sys
import collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ensemble as ENS   # noqa: E402
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import groundtruth as GT  # noqa: E402

ACCEPT = {"agreed", "agreed_gt", "single_verified", "multi_verified"}


def _repair(engines, crop, seed, gt_fingerprint):
    cand_fp = GT.latex_symbol_multiset(seed or "")
    ca, cb = collections.Counter(gt_fingerprint), collections.Counter(cand_fp)
    missing = list((ca - cb).elements())
    extra = list((cb - ca).elements())
    return engines["vlm_repair"](crop, seed or "", missing, extra)


def correct(eqid, crop, gt_fingerprint, prior_candidates, cfg, engines=None):
    """prior_candidates: [{engine, latex}] already tried; engines: optional
    callables pix2tex(crop)->latex, vlm(crop)->latex,
    vlm_repair(crop, latex, missing, extra)->latex. Returns
    {latex, status, verdict, evidence, passes}."""
    cfg = cfg or {}
    engines = engines or {}
    max_passes = cfg.get("selfcorrect", {}).get("max_passes", 3)
    cands = [{"engine": c.get("engine", "prior"), "latex": c.get("latex")}
             for c in (prior_candidates or []) if c.get("latex")]
    evidence = []

    def best_prior_latex():
        dec = ENS.decide(cands, gt_fingerprint, crop, cfg)
        seed = dec.get("latex") or dec.get("best_seed")
        return seed

    # progressively add candidates: a primary VLM read, an independent VLM read
    # (self-consistency vote), a cheap pix2tex vote, then a targeted VLM repair.
    # After each, re-run the ensemble: any two sources (engines or VLM votes)
    # concurring verifies the equation. A clean crop transcribes consistently;
    # a genuinely ambiguous one will not converge and stays flagged.
    passes = [
        [("vlm", lambda: engines["vlm"](crop))] if engines.get("vlm") else [],
        ([("vlm2", lambda: engines["vlm2"](crop))] if engines.get("vlm2") else [])
        + ([("pix2tex", lambda: engines["pix2tex"](crop))] if engines.get("pix2tex") else []),
        [("vlm_repair", lambda: _repair(engines, crop, best_prior_latex(), gt_fingerprint))]
        if engines.get("vlm_repair") else [],
    ]
    for p, batch in enumerate(passes, 1):
        if not batch:
            continue
        for src, fn in batch:
            try:
                latex = fn()
            except Exception as e:
                evidence.append({"pass": p, "error": f"{src}: {e}"})
                continue
            if latex and latex.strip():
                cands.append({"engine": src, "latex": latex})
                evidence.append({"pass": p, "source": src, "latex": latex})
        dec = ENS.decide(cands, gt_fingerprint, crop, cfg)
        if dec.get("status") in ACCEPT:
            return {"latex": dec["latex"], "status": dec["status"],
                    "verdict": dec.get("verdict"), "evidence": evidence, "passes": p,
                    "via": "selfcorrect"}

    # No multi-source consensus emerged. Resolve the equation to the single best
    # transcription rather than leaving it unfixed: prefer a VLM read (it directly
    # transcribes the source crop), then the most complete, highest-scoring valid
    # candidate. Only if NO source produced valid KaTeX at all is it truly flagged.
    dec = ENS.decide(cands, gt_fingerprint, crop, cfg)
    ev = dec.get("evidence") or []
    valid = [e for e in ev if (e.get("verdict") or {}).get("valid")]

    def _rank(e):
        src = str(e.get("engine") or "")
        fp = GT.latex_symbol_multiset(e.get("sanitized") or "")
        return (src.startswith("vlm"), len(fp), (e.get("verdict") or {}).get("score", 0))

    if valid:
        best = max(valid, key=_rank)
        return {"latex": best.get("sanitized"), "status": "resolved",
                "verdict": best.get("verdict"), "evidence": evidence,
                "passes": max_passes, "via": "vlm_resolved"}
    return {"latex": dec.get("latex") or dec.get("best_seed"),
            "status": "flagged", "verdict": dec.get("verdict"),
            "evidence": evidence, "passes": max_passes}
