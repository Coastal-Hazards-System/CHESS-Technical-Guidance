import fitz, re
RE_TCAP = re.compile(r'^(Table)\s+([IVX]+-\d+-\d+[a-z]?)\s*\.?\s*$', re.I)

def _lines(page):
    out=[]
    for b in page.get_text("dict")["blocks"]:
        if b.get("type")!=0: continue
        for ln in b["lines"]:
            txt="".join(s["text"] for s in ln["spans"]).strip()
            if txt: out.append((ln["bbox"],txt))
    out.sort(key=lambda x:x[0][1]); return out

def _is_body(bbox,txt,W):
    return (bbox[2]-bbox[0])>W*0.60 and len(txt.split())>=12

def find_table_regions(page):
    W=page.rect.width; lines=_lines(page); regions=[]
    for i,(bb,txt) in enumerate(lines):
        m=RE_TCAP.match(txt)
        if not m: continue
        cap_id=m.group(2); title=lines[i+1][1] if i+1<len(lines) else ""
        bot=bb[3]+300
        for j in range(i+2,len(lines)):
            jbb,jtxt=lines[j]
            if jbb[1]-bb[3]>6 and _is_body(jbb,jtxt,W):
                bot=jbb[1]-2; break
        regions.append((cap_id,title,fitz.Rect(40,bb[3],W-30,bot)))
    return regions

def reconstruct(page,region,title=''):
    tabs=page.find_tables(clip=region,strategy="text").tables
    if not tabs: return None,0.0
    t=max(tabs,key=lambda x:x.row_count*x.col_count)
    cells=[c for c in t.cells if c]
    if not cells: return None,0.0
    lefts=sorted(set(round(c[0]) for c in cells))
    max_right=max(round(c[2]) for c in cells)
    ncol=len(lefts)
    if ncol<2: return None,0.0
    edges=lefts+[max_right+1]
    def col_of(cx):
        for i in range(ncol):
            if edges[i]<=cx<edges[i+1]: return i
        return ncol-1
    words=[w for w in page.get_text("words")
           if region.y0<=(w[1]+w[3])/2<=region.y1 and region.x0<=(w[0]+w[2])/2<=region.x1]
    if not words: return None,0.0
    words.sort(key=lambda w:(round(w[1]),w[0]))
    plines,cur,cy=[],[],None
    for w in words:
        yc=(w[1]+w[3])/2
        if cy is None or abs(yc-cy)<=5:
            cur.append(w); cy=yc if cy is None else (cy+yc)/2
        else:
            plines.append(cur); cur,cy=[w],yc
    if cur: plines.append(cur)
    prows=[]
    for ln in plines:
        row=[""]*ncol
        for w in sorted(ln,key=lambda w:w[0]):
            ci=col_of((w[0]+w[2])/2)
            row[ci]=(row[ci]+" "+w[4]).strip()
        prows.append(row)
    title_words=set(re.findall(r'[A-Za-z]+',title.lower()))
    def is_titlerow(r):
        rw=set(re.findall(r'[A-Za-z]+'," ".join(r).lower()))
        return len(rw & title_words)>=3
    while prows and (sum(1 for c in prows[0] if c)<=1 or is_titlerow(prows[0])):
        prows.pop(0)
    if len(prows)<2: return None,0.0
    merged=[prows[0]]
    for r in prows[1:]:
        if not r[0]:
            for ci in range(ncol):
                if r[ci]: merged[-1][ci]=(merged[-1][ci]+" "+r[ci]).strip()
        else:
            merged.append(r)
    fill=sum(1 for r in merged for c in r if c)/(len(merged)*ncol)
    gfm=["| "+" | ".join(merged[0])+" |","| "+" | ".join("---" for _ in range(ncol))+" |"]
    for r in merged[1:]: gfm.append("| "+" | ".join(r)+" |")
    return gfm,fill

def tables_on_page(page):
    out=[]
    for cap_id,title,region in find_table_regions(page):
        gfm,conf=reconstruct(page,region,title)
        out.append({"id":cap_id,"title":title,"region":region,"gfm":gfm,
                    "confidence":round(conf,2),"ok":bool(gfm and conf>=0.45)})
    return out
