#!/usr/bin/env python3
"""pix2tex (LaTeX-OCR) adapter — a cheap extra vote for self-correction only
(known weak; never authoritative). Windows-safe per-call timeout via a thread
(signal.SIGALRM is POSIX-only)."""
import concurrent.futures

_MODEL = None


def _load():
    global _MODEL
    if _MODEL is None:
        from pix2tex.cli import LatexOCR
        _MODEL = LatexOCR()
    return _MODEL


def _infer(img_path):
    from PIL import Image
    m = _load()
    return m(Image.open(img_path))


def transcribe(img_path, timeout=20):
    """Return LaTeX or '' . Best-effort timeout (thread cannot be force-killed,
    but pix2tex hangs are rare and this prevents the common stall)."""
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(_infer, img_path)
            return (fut.result(timeout=timeout) or "").strip()
    except concurrent.futures.TimeoutError:
        return ""
    except Exception:
        return ""


if __name__ == "__main__":
    import sys
    print(repr(transcribe(sys.argv[1])))
