#!/usr/bin/env python3
"""Orchestrate the full CEM -> Markdown conversion, manifest-driven & resumable.
Usage:
  python run_all.py --src <dir-with-Part-PDFs> --out <output-dir> [--jobs N] [--only III-1,III-2]
Steps per chapter: convert_chapter -> ocr_equations(parallel) -> validate_assemble.
Already-finished chapters (final .md present) are skipped unless --force."""
import argparse, os, json, subprocess, sys
HERE=os.path.dirname(os.path.abspath(__file__))

def sh(args): subprocess.run(args,check=True)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--src",required=True); ap.add_argument("--out",required=True)
    ap.add_argument("--jobs",type=int,default=os.cpu_count())
    ap.add_argument("--only",default=""); ap.add_argument("--force",action="store_true")
    a=ap.parse_args()
    os.makedirs(a.out,exist_ok=True)
    man_path=os.path.join(a.out,"manifest.json")
    if not os.path.exists(man_path):
        sh([sys.executable,os.path.join(HERE,"extract.py"),a.src,a.out])
    manifest=json.load(open(man_path))
    only=set(x.strip() for x in a.only.split(",") if x.strip())
    chapters=[m for m in manifest if m["kind"] in ("chapter","glossary")]
    work=os.path.join(a.out,"_work"); os.makedirs(work,exist_ok=True)
    for m in chapters:
        cid=f"{m['part_roman']}-{m['chapter']}" if m['chapter'] else m['part_roman']
        if only and cid not in only: continue
        partdir=f"part-{m['portfolio'].split('-')[-1]}" if m['portfolio'].startswith('Part') else "appendix"
        outdir=os.path.join(a.out,"markdown",partdir); os.makedirs(outdir,exist_ok=True)
        base=f"ch-{m['chapter']:02d}" if m['chapter'] else "glossary"
        final=os.path.join(outdir,base+".md")
        if os.path.exists(final) and not a.force:
            print(f"skip {cid} (done)"); continue
        pdf=os.path.join(a.out,"chapters",m["work_file"])
        assets=os.path.join(outdir,"assets",f"{partdir}-{base}")
        skel=os.path.join(work,f"{cid}.skeleton.md")
        eqjobs=os.path.join(work,f"{cid}.eqjobs.json")
        latex=os.path.join(work,f"{cid}.latex.json")
        review=os.path.join(outdir,base+"_review.md")
        print(f"=== {cid}: {m['orig']} ({m['pages']}pp) ===")
        cfg=json.dumps({"pdf":pdf,"out":skel,"eqjobs":eqjobs,"assets":assets,
                        "part":m["part_roman"],"chapter":m["chapter"] or 0,
                        "title":m.get("title") or base})
        sh([sys.executable,os.path.join(HERE,"convert_chapter.py"),cfg])
        sh([sys.executable,os.path.join(HERE,"ocr_equations.py"),eqjobs,latex,str(a.jobs)])
        rel=os.path.relpath(assets,outdir).replace(os.sep,"/")
        sh([sys.executable,os.path.join(HERE,"validate_assemble.py"),skel,latex,rel,final,review])
        print(f"  -> {final}")
    print("DONE")

if __name__=="__main__":
    main()
