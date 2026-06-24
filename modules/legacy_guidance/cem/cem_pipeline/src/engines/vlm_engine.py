#!/usr/bin/env python3
"""Local vision-LLM adapter (spec §7.5) for the self-correction loop.

Talks to a local Ollama server (default) or an OpenAI-compatible vLLM endpoint.
Fully local / open-source; no external API. If the server/model is unavailable
the calls raise, and selfcorrect.py simply skips that pass (graceful degrade).
"""
import os
import base64
import json
import urllib.request

_CFG = {
    "backend": os.environ.get("CEM_VLM_BACKEND", "ollama"),
    "model": os.environ.get("CEM_VLM_MODEL", "qwen2.5vl:7b"),
    "endpoint": os.environ.get("CEM_VLM_ENDPOINT", "http://localhost:11434"),
}

_PROMPT = ("Transcribe this mathematical equation to a single line of KaTeX-"
           "compatible LaTeX math. Output ONLY the math expression itself — no "
           "prose, no $ delimiters, no code fences, no \\documentclass, no "
           "\\begin{document}, no \\begin{equation}, no \\tag. Just the formula.")


def configure(cfg):
    if cfg:
        _CFG.update({k: v for k, v in cfg.items() if v is not None})


def _b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def _post(url, payload, timeout=120):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _clean(latex):
    if not latex:
        return ""
    t = latex.strip()
    t = t.replace("```latex", "").replace("```", "").strip()
    if t.startswith("$$") and t.endswith("$$"):
        t = t[2:-2]
    elif t.startswith("$") and t.endswith("$"):
        t = t[1:-1]
    return t.strip()


def _ollama(prompt, img_path, temperature=0.0):
    payload = {"model": _CFG["model"], "prompt": prompt,
               "images": [_b64(img_path)], "stream": False,
               "options": {"temperature": temperature}}
    res = _post(_CFG["endpoint"].rstrip("/") + "/api/generate", payload)
    return _clean(res.get("response", ""))


def _vllm(prompt, img_path, temperature=0.0):
    # OpenAI-compatible chat/completions with image_url data URI
    data_uri = "data:image/png;base64," + _b64(img_path)
    payload = {"model": _CFG["model"], "temperature": temperature, "messages": [
        {"role": "user", "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": data_uri}}]}]}
    res = _post(_CFG["endpoint"].rstrip("/") + "/v1/chat/completions", payload)
    return _clean(res["choices"][0]["message"]["content"])


def _run(prompt, img_path, temperature=0.0):
    if _CFG["backend"] == "vllm":
        return _vllm(prompt, img_path, temperature)
    return _ollama(prompt, img_path, temperature)


def transcribe(img_path, temperature=0.0):
    return _run(_PROMPT, img_path, temperature)


def repair(img_path, prior_latex, missing, extra):
    miss = " ".join(map(str, missing)) or "(none)"
    ext = " ".join(map(str, extra)) or "(none)"
    prompt = (
        "You are correcting an OCR transcription of the mathematical equation in "
        "this image. A previous attempt produced this LaTeX:\n\n" + (prior_latex or "") +
        "\n\nCompared to the equation's true symbols, that attempt is MISSING: " + miss +
        " and has EXTRA: " + ext + ".\n"
        "Output only the corrected single-line LaTeX (no prose, no $ delimiters).")
    return _run(prompt, img_path)


def available():
    try:
        if _CFG["backend"] == "vllm":
            _post(_CFG["endpoint"].rstrip("/") + "/v1/models", {}, timeout=5)
        else:
            with urllib.request.urlopen(_CFG["endpoint"].rstrip("/") + "/api/tags", timeout=5) as r:
                r.read()
        return True
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    print("available:", available())
    if len(sys.argv) > 1:
        print(repr(transcribe(sys.argv[1])))
