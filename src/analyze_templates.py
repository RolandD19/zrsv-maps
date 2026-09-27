#!/usr/bin/env python3
"""
Batch analyzer for ZERO Sievert bin2json output.

Usage:
    python analyze_templates.py jsons.zip
or:
    python analyze_templates.py path/to/json_directory

Writes CSV reports to ./template_analysis/
"""
import json, csv, collections, zipfile, sys, shutil
from pathlib import Path

inp = Path(sys.argv[1] if len(sys.argv) > 1 else "jsons.zip")
out = Path("template_analysis")
if out.exists():
    shutil.rmtree(out)
out.mkdir()

docs = {}
if inp.is_file() and inp.suffix.lower() == ".zip":
    with zipfile.ZipFile(inp) as z:
        for n in z.namelist():
            if n.lower().endswith(".json"):
                with z.open(n) as f:
                    docs[n] = json.load(f)
elif inp.is_dir():
    for p in inp.rglob("*.json"):
        docs[str(p.relative_to(inp))] = json.loads(p.read_text(encoding="utf-8"))
else:
    raise SystemExit("Input must be a ZIP of JSONs or a directory of JSON files.")

object_occ = collections.Counter()
object_templates = collections.defaultdict(set)
chunk_presence = collections.Counter()
chunk_records = collections.Counter()
fence_occ = collections.Counter()
fence_templates = collections.defaultdict(set)
grid_occ = collections.Counter()
grid_values = collections.Counter()
grid_templates = collections.defaultdict(set)
tile_occ = collections.Counter()
tile_templates = collections.defaultdict(set)
decor_occ = collections.Counter()
decor_templates = collections.defaultdict(set)
template_rows = []

def rngish(o):
    return any(t in o.lower() for t in
               ("spawner","spawn","dcm_","generator","random","extraction",
                "quest_","anomaly","prologue"))

for fname, doc in docs.items():
    t_obj=t_fence=t_decor=t_tiles=0
    chunk_names=[]
    for ch in doc.get("chunks", []):
        name=ch.get("name","")
        data=ch.get("data",{})
        items=data.get("items",[])
        chunk_names.append(name)
        chunk_presence[name]+=1
        chunk_records[name]+=len(items)
        if name=="inst":
            for it in items:
                o=it.get("object")
                if o:
                    object_occ[o]+=1; object_templates[o].add(fname); t_obj+=1
        elif name=="fence grid":
            for it in items:
                k=(it.get("fence_id"),it.get("fence_name"))
                fence_occ[k]+=1; fence_templates[k].add(fname); t_fence+=1
        elif name=="decor":
            for it in items:
                k=it.get("decor_id")
                decor_occ[k]+=1; decor_templates[k].add(fname); t_decor+=1
        elif name=="grid":
            g=data.get("grid"); grid_templates[g].add(fname)
            for it in items:
                grid_occ[g]+=1; grid_values[(g,it.get("value"))]+=1
        elif name=="grid + tiles":
            g=data.get("grid"); grid_templates[g].add(fname)
            for it in items:
                grid_occ[g]+=1; grid_values[(g,data.get("grid_value"))]+=1
                k=(f"grid+tiles:{g}",it.get("tile"))
                tile_occ[k]+=1; tile_templates[k].add(fname); t_tiles+=1
        elif name=="tiles":
            layer=data.get("layer")
            for it in items:
                k=(f"tiles:{layer}",it.get("tile"))
                tile_occ[k]+=1; tile_templates[k].add(fname); t_tiles+=1
        elif name in ("water","grid_map"):
            for it in items:
                k=(name,it.get("tile"))
                tile_occ[k]+=1; tile_templates[k].add(fname); t_tiles+=1
    template_rows.append({
        "template":fname, "building_name":doc.get("building_name"),
        "chunks":len(doc.get("chunks",[])), "chunk_types":"|".join(chunk_names),
        "instances":t_obj, "fences":t_fence, "decor":t_decor, "tile_records":t_tiles
    })

def csvout(name, fields, rows):
    with (out/name).open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

csvout("templates.csv", list(template_rows[0]), sorted(template_rows,key=lambda r:r["template"]))
csvout("objects.csv",
       ["object","occurrences","templates","likely_rng_hook","example_templates"],
       [{"object":o,"occurrences":c,"templates":len(object_templates[o]),
         "likely_rng_hook":rngish(o),
         "example_templates":"|".join(sorted(object_templates[o])[:12])}
        for o,c in object_occ.most_common()])
csvout("fence_types.csv",["fence_id","fence_name","occurrences","templates"],
       [{"fence_id":k[0],"fence_name":k[1],"occurrences":c,
         "templates":len(fence_templates[k])} for k,c in fence_occ.most_common()])
csvout("grids.csv",["grid","records","templates"],
       [{"grid":g,"records":c,"templates":len(grid_templates[g])}
        for g,c in grid_occ.most_common()])
csvout("grid_values.csv",["grid","value","occurrences"],
       [{"grid":g,"value":v,"occurrences":c}
        for (g,v),c in sorted(grid_values.items(),key=lambda z:(str(z[0][0]),str(z[0][1])))])
csvout("tile_ids.csv",["source","tile_u32","occurrences","templates"],
       [{"source":s,"tile_u32":t,"occurrences":c,
         "templates":len(tile_templates[(s,t)])}
        for (s,t),c in tile_occ.most_common()])
csvout("decor_ids.csv",["decor_id","occurrences","templates"],
       [{"decor_id":d,"occurrences":c,"templates":len(decor_templates[d])}
        for d,c in decor_occ.most_common()])
csvout("rng_hook_candidates.csv",
       ["object","occurrences","templates","example_templates"],
       [{"object":o,"occurrences":c,"templates":len(object_templates[o]),
         "example_templates":"|".join(sorted(object_templates[o])[:15])}
        for o,c in object_occ.most_common() if rngish(o)])
csvout("chunk_summary.csv",["chunk","templates_with_chunk","records"],
       [{"chunk":c,"templates_with_chunk":chunk_presence[c],"records":chunk_records[c]}
        for c in sorted(chunk_presence)])
print(f"Analyzed {len(docs)} templates -> {out}/")
