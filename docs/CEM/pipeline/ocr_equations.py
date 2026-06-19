#!/usr/bin/env python3
"""Stage 2: OCR equation crops -> LaTeX, parallel across CPU cores.
Each worker loads its own LatexOCR model; a per-equation SIGALRM timeout
prevents the occasional pix2tex infinite loop from stalling the run."""
import sys, json, os, signal
from multiprocessing import Pool

def _init():
    global _M
    from pix2tex.cli import LatexOCR
    _M=LatexOCR()

def _one(job):
    from PIL import Image
    class TO(Exception): pass
    def h(s,f): raise TO()
    signal.signal(signal.SIGALRM,h); signal.alarm(20)
    try: r=_M(Image.open(job["img"]))
    except TO: r="__TIMEOUT__"
    except Exception as e: r=f"__ERR__ {e}"
    finally: signal.alarm(0)
    return job["eqid"], r

def main(eqjobs_path, out_path, jobs=None):
    js=json.load(open(eqjobs_path))
    if not js:
        json.dump({},open(out_path,"w")); print("no equations"); return
    jobs=jobs or os.cpu_count()
    res={}
    with Pool(processes=jobs, initializer=_init) as pool:
        for eqid,latex in pool.imap_unordered(_one, js):
            res[eqid]=latex
    json.dump(res,open(out_path,"w"),indent=2)
    print(f"OCR {len(res)} equations -> {out_path}")

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv)>3 else None)
