#!/usr/bin/env python3
"""Extract embedded chapter PDFs from the CEM PDF Portfolios + build manifest."""
import sys, os, json, hashlib, re
from pypdf import PdfReader

ROMAN={'01':'I','02':'II','03':'III','04':'IV','05':'V','06':'VI'}

def main(src_dir, out_dir):
    chdir=os.path.join(out_dir,"chapters"); os.makedirs(chdir,exist_ok=True)
    seen={}; recs=[]
    for part in ['01','02','03','04','05','06']:
        f=os.path.join(src_dir,f"EM_1110-2-1100_Part-{part}.pdf")
        if not os.path.exists(f): continue
        for name,content in PdfReader(f).attachments.items():
            data=content[0] if isinstance(content,list) else content
            h=hashlib.md5(data).hexdigest()
            if h in seen: continue
            seen[h]=1; clean=name.replace('<0>','')
            wf=f"P{part}__{clean}"; open(os.path.join(chdir,wf),'wb').write(data)
            try: pc=len(PdfReader(os.path.join(chdir,wf)).pages)
            except: pc=None
            m=re.search(r'Ch_?(\d+)',clean)
            recs.append({"portfolio":f"Part-{part}","orig":clean,"work_file":wf,
                "pages":pc,"part_roman":ROMAN[part],
                "chapter":int(m.group(1)) if m else None,
                "kind":"chapter" if m else "admin"})
    appa=os.path.join(src_dir,"EM_1110-2-1100_App_A.pdf")
    if os.path.exists(appa):
        import shutil; shutil.copy(appa,os.path.join(chdir,"App_A.pdf"))
        recs.append({"portfolio":"App_A","orig":"App_A.pdf","work_file":"App_A.pdf",
                     "pages":95,"part_roman":"App-A","chapter":None,"kind":"glossary"})
    json.dump(recs,open(os.path.join(out_dir,"manifest.json"),"w"),indent=2)
    print(f"Extracted {len(recs)} files -> {chdir}")
    print(f"Manifest -> {os.path.join(out_dir,'manifest.json')}")

if __name__=="__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else ".")
