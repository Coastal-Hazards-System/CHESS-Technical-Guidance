#!/usr/bin/env python3
"""Equation verification: KaTeX validity (hard gate) + symbol cross-check vs
the born-digital ground-truth fingerprint (hard gate) + render-diff SSIM
(soft ranking signal only)."""
import os
import sys
import json
import subprocess
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import groundtruth as GT  # noqa: E402

_HERE = os.path.dirname(os.path.abspath(__file__))
KATEX_JS = os.path.join(os.path.dirname(_HERE), "katex_validate.js")
_NODE = os.environ.get("CEM_NODE", "node")


def katex_validate_batch(latex_map: dict) -> dict:
    """{id: latex} -> {id: bool}. One node process for the whole batch."""
    if not latex_map:
        return {}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(latex_map, f)
        inp = f.name
    try:
        out = subprocess.run([_NODE, KATEX_JS, inp], capture_output=True, text=True, timeout=120)
        if out.returncode != 0:
            sys.stderr.write(f"[verify] katex_validate.js failed: {out.stderr}\n")
            return {k: False for k in latex_map}
        return json.loads(out.stdout)
    except Exception as e:
        sys.stderr.write(f"[verify] katex batch error: {e}\n")
        return {k: False for k in latex_map}
    finally:
        try:
            os.unlink(inp)
        except OSError:
            pass


def katex_valid(latex: str) -> bool:
    return katex_validate_batch({"_": latex}).get("_", False)


# --- render-diff (soft) ----------------------------------------------------
_MPL_OK = None


def _ensure_mpl():
    global _MPL_OK, plt, np, ssim
    if _MPL_OK is not None:
        return _MPL_OK
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _plt
        import numpy as _np
        from skimage.metrics import structural_similarity as _ssim
        plt, np, ssim = _plt, _np, _ssim
        _MPL_OK = True
    except Exception:
        _MPL_OK = False
    return _MPL_OK


def render_diff_ssim(latex: str, source_crop_png: str):
    """SSIM between matplotlib-mathtext render of `latex` and the source crop.
    Returns None when rendering isn't possible (fonts/coverage); soft signal."""
    if not source_crop_png or not os.path.exists(source_crop_png):
        return None
    if not _ensure_mpl():
        return None
    try:
        from PIL import Image
        import io
        fig = plt.figure(figsize=(6, 2), dpi=120)
        fig.text(0.5, 0.5, f"${latex}$", ha='center', va='center', fontsize=18)
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.1)
        plt.close(fig)
        buf.seek(0)
        cand = Image.open(buf).convert("L")
        src = Image.open(source_crop_png).convert("L")
        size = (256, 96)
        cand = cand.resize(size)
        src = src.resize(size)
        a = np.asarray(cand, dtype=float)
        b = np.asarray(src, dtype=float)
        return float(ssim(a, b, data_range=255))
    except Exception:
        return None


def verify(latex, gt_fingerprint, source_crop_png=None, cfg=None,
           katex_ok=None):
    """Return a verdict dict for a single candidate LaTeX.

    {valid, symbol_match, symbol_dist, ssim, score, accepted, reasons}
    `katex_ok` may be supplied from a precomputed batch to avoid re-spawning node.
    """
    cfg = cfg or {}
    vcfg = cfg.get("verify", {}) if isinstance(cfg.get("verify", {}), dict) else {}
    tol = vcfg.get("symbol_edit_tolerance", 1)
    reasons = []

    # ground truth is usable only when the equation has a born-digital text layer.
    # Part II equations are vector graphics (no text) -> no GT -> rely on the
    # ensemble (engine agreement) + render-diff instead of the symbol gate.
    has_gt = len(gt_fingerprint) >= 2

    valid = katex_ok if katex_ok is not None else katex_valid(latex)
    if not valid:
        reasons.append("katex_invalid")

    if has_gt:
        matched, dist = GT.symbol_match(gt_fingerprint, latex, tolerance=tol)
        if not matched:
            reasons.append(f"symbol_mismatch(dist={dist})")
    else:
        matched, dist = None, None
        reasons.append("no_groundtruth")

    want_ssim = bool(source_crop_png) and (vcfg.get("render_diff") or not has_gt)
    ssim_val = render_diff_ssim(latex, source_crop_png) if want_ssim else None

    score = 0.0
    score += 0.5 if valid else 0.0
    if has_gt:
        score += 0.4 if matched else max(0.0, 0.4 - 0.1 * dist)
    if ssim_val is not None:
        score += 0.2 * max(0.0, ssim_val)

    # a single candidate is "accepted" by itself only with born-digital symbol
    # confirmation; without GT, acceptance is decided by the ensemble (agreement).
    accepted = bool(valid and matched) if has_gt else False
    return {
        "valid": bool(valid),
        "has_gt": has_gt,
        "symbol_match": matched,
        "symbol_dist": dist,
        "ssim": ssim_val,
        "score": round(score, 4),
        "accepted": accepted,
        "reasons": reasons,
    }


if __name__ == "__main__":
    gt = GT.symbol_multiset("H = a / b")
    print("node:", _NODE, "katex_js exists:", os.path.exists(KATEX_JS))
    print(verify(r"H = \frac{a}{b}", gt))
    print(verify(r"H = \frac{a}{", gt))   # invalid katex
    print(verify(r"H = \frac{a}{c}", gt))  # symbol mismatch (b vs c)
