#!/usr/bin/env python3
"""Stage 1 per chapter: clean text + headings, TOC handling, header/footer
stripping, equation detection+crop (full fraction height), faithful table
reconstruction (region-based: GFM or flagged image fallback), figure export.
Writes <out>.md (skeleton with {{EQ:id}}) and <eqjobs>.json"""
import fitz, re, os, sys, json, collections, statistics
from PIL import Image, ImageChops, ImageOps
import tables as TB

RE_RUN=re.compile(r'^\s*EM\s*1110-2-1100'); RE_PART=re.compile(r'^\s*\(Part\s+[IVX]+\)')
RE_DATE=re.compile(r'^\s*(Change\s*\d+\s*)?\(?\d{1,2}\s+\w{3,9}\s+\d{2,4}\)?\s*$')
RE_PAGENO=re.compile(r'^\s*[IVX]+-\d+-\d+\s*$'); RE_CHG=re.compile(r'^\s*Change\s+\d+\b')
RE_SEC=re.compile(r'^([IVX]+)-(\d+)-(\d+)\.\s+(.*)$')
RE_SUB=re.compile(r'^([IVX]+)-(\d+)-(\d+)\.([a-z])\.\s+(.*)$')
RE_EQ=re.compile(r'\(([IVX]+-\d+-\d+[a-z]?)\)\s*$')
RE_FIG=re.compile(r'^(Figure)\s+([IVX]+-\d+-\d+[a-z]?)(?:[\.\s]|$)',re.I)
RE_DOTS=re.compile(r'\s*\.\s*\.\s*\.[\.\s]*')

def is_run(s): return bool(RE_RUN.match(s) or RE_PART.match(s) or RE_DATE.match(s) or RE_PAGENO.match(s) or RE_CHG.match(s))

def crop_eq(page,num_bbox,line_bbox,assets,eqid):
    x=num_bbox[0]; yc=(line_bbox[1]+line_bbox[3])/2; lh=line_bbox[3]-line_bbox[1]
    clip=fitz.Rect(page.rect.x0,yc-lh*1.6,x-2,yc+lh*1.6)
    pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=clip)
    im=Image.frombytes("RGB",[pix.width,pix.height],pix.samples).convert("L")
    bb=ImageChops.difference(im,Image.new("L",im.size,255)).getbbox()
    if bb:
        l,t,r,b=bb; im=im.crop((max(0,l-10),max(0,t-10),min(im.size[0],r+10),min(im.size[1],b+10)))
    im=ImageOps.expand(im,border=14,fill=255)
    rel=f"eq-{eqid}.png"; im.save(os.path.join(assets,rel)); return rel,im.size

def crop_region(page,region,assets,name):
    pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=region)
    rel=f"{name}.png"; pix.save(os.path.join(assets,rel)); return rel

def convert(pdf,out_md,eqjobs_path,assets,part,chapter,title):
    doc=fitz.open(pdf); os.makedirs(assets,exist_ok=True); adir=os.path.basename(assets)
    npages=len(doc)
    edge=collections.Counter()
    for p in doc:
        h=p.rect.height
        for b in p.get_text("dict")["blocks"]:
            if b.get("type")!=0: continue
            for ln in b["lines"]:
                t="".join(s["text"] for s in ln["spans"]).strip()
                if t and (ln["bbox"][1]<h*0.10 or ln["bbox"][1]>h*0.90): edge[t]+=1
    repeated={t for t,c in edge.items() if c>=max(3,npages//4)}
    sizes=collections.Counter()
    for p in doc:
        for b in p.get_text("dict")["blocks"]:
            if b.get("type")!=0: continue
            for ln in b["lines"]:
                for s in ln["spans"]: sizes[round(s["size"])]+=len(s["text"])
    body=sizes.most_common(1)[0][0] if sizes else 10

    # best table per id; keep region+page
    best={}
    for p in doc:
        for tb in TB.tables_on_page(p):
            if tb["id"] not in best or tb["confidence"]>best[tb["id"]]["confidence"]:
                tb["_page"]=p.number; best[tb["id"]]=tb
    # index regions by page (only the winning occurrence)
    regions_by_page=collections.defaultdict(list)
    for tid,tb in best.items():
        regions_by_page[tb["_page"]].append(tb)

    md=["---",'manual: "EM 1110-2-1100 (Coastal Engineering Manual)"',f'part: "{part}"',
        f'chapter: {chapter}',f'title: "{title}"',f'source_pdf: "{os.path.basename(pdf)}"',
        f'pages: {npages}',"---",""]
    eqjobs=[]; counts=collections.Counter(); emitted=set()

    for p in doc:
        h=p.rect.height; d=p.get_text("dict")
        ptxt=p.get_text()
        in_toc=("Table of Contents" in ptxt or "List of Tables" in ptxt or "List of Figures" in ptxt)
        pregions=regions_by_page.get(p.number,[])
        blocks=[b for b in d["blocks"] if b.get("type")==0]
        blocks.sort(key=lambda b:(round(b["bbox"][1]),round(b["bbox"][0])))
        for b in blocks:
            bc=((b["bbox"][0]+b["bbox"][2])/2,(b["bbox"][1]+b["bbox"][3])/2)
            # table region suppression / emission
            hit=None
            for tb in pregions:
                if tb["region"].contains(fitz.Point(bc)) or tb["region"].intersects(fitz.Rect(b["bbox"])):
                    hit=tb; break
            if hit is not None and not in_toc:
                if hit["id"] not in emitted:
                    emitted.add(hit["id"])
                    md+=["",f"**Table {hit['id']}. {hit['title']}**",""]
                    if hit["ok"]:
                        counts["tables_gfm"]+=1; md+=hit["gfm"]+[""]
                    else:
                        counts["tables_img"]+=1
                        rel=crop_region(doc[hit["_page"]],hit["region"],assets,f"table-{hit['id']}")
                        md+=[f"> ⚠️ Table {hit['id']} not auto-gridded; image fallback (review).",
                             f"![Table {hit['id']}](assets/{adir}/{rel})",""]
                continue  # suppress raw text inside table region
            for ln in b["lines"]:
                spans=ln["spans"]; txt="".join(s["text"] for s in spans).rstrip(); s=txt.strip()
                if not s or s in repeated: continue
                y=ln["bbox"][1]
                if (y<h*0.10 or y>h*0.90) and is_run(s): continue
                if in_toc: md.append(f"- {RE_DOTS.sub('  —  ',s)}"); continue
                mf=RE_FIG.match(s)
                if mf: md+=["",f"**{s}**",""]; continue
                me=RE_EQ.search(s)
                if me:
                    eqid=me.group(1); nb=spans[-1]["bbox"]
                    for sp in spans:
                        if RE_EQ.search(sp["text"].strip()): nb=sp["bbox"]; break
                    rel,sz=crop_eq(p,nb,ln["bbox"],assets,eqid)
                    eqjobs.append({"eqid":eqid,"img":os.path.join(assets,rel)})
                    counts["equations"]+=1; md+=["",f"{{{{EQ:{eqid}}}}}",""]; continue
                msub=RE_SUB.match(s); msec=RE_SEC.match(s)
                avg=statistics.mean(sp["size"] for sp in spans); bold=any("Bold" in sp["font"] for sp in spans)
                if msub: md+=["",f"#### {s}",""]
                elif msec: md+=["",f"### {s}",""]
                elif avg>=body+2 and bold and len(s)<90: md+=["",f"## {s}",""]
                else: md.append(txt)
        md.append("")

    for pno,p in enumerate(doc):
        idx=0
        for img in p.get_images(full=True):
            try:
                pix=fitz.Pixmap(doc,img[0])
                if pix.width<60 or pix.height<60: continue
                if pix.n-pix.alpha>=4: pix=fitz.Pixmap(fitz.csRGB,pix)
                idx+=1; counts["figures"]+=1; pix.save(os.path.join(assets,f"img-p{pno+1}-{idx}.png"))
            except: pass

    text=re.sub(r"\n{3,}","\n\n","\n".join(md))
    open(out_md,"w").write(text); json.dump(eqjobs,open(eqjobs_path,"w"),indent=2)
    return dict(pages=npages,**counts,eq_jobs=len(eqjobs))

if __name__=="__main__":
    c=json.loads(sys.argv[1])
    print(json.dumps(convert(c["pdf"],c["out"],c["eqjobs"],c["assets"],c["part"],c["chapter"],c["title"]),indent=2))
