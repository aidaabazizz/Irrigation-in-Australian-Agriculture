"""Rebuilds data/ and specs/ for maps from the uploaded CLUM + irrigation-area files (pure Python, no deps).
Usage: python3 scripts/build_from_uploads.py CLUM_Commodities_2023.json irrigation_area.json"""
import json,sys,math,collections
clum,irr=sys.argv[1],sys.argv[2]
G={"cotton":"Cotton","sugar cane":"Sugar cane","grapes":"Grapes","grapes wine":"Grapes","grapes table":"Grapes","grapes dried":"Grapes"}
def grp(p):
    d,b=p["Commod_dsc"],p["Broad_type"]
    if d in G: return G[d]
    if b in("Fruits","Nuts"): return "Fruit & nut"
    if b=="Vegetables and herbs": return "Vegetables & herbs"
    return None
cell=collections.defaultdict(float);state=collections.defaultdict(float);broad=collections.defaultdict(float);land=set()
with open(clum) as f:
    for line in f:
        i=line.find('"properties":')
        if i<0: continue
        p=json.loads(line[i+13:line.rstrip().rstrip(',').rfind('}')])
        g=line[line.find('[[['):line.find('[[[')+200] if False else None
        j=line.find('"coordinates":[[');xy=json.loads('['+line[j+16:].split(']')[0].replace('[','')+']')
        lon,lat=xy[0],xy[1];k=(math.floor(lon)+.5,math.floor(lat)+.5)
        land.add(k);broad[p["Broad_type"]]+=p["Area_ha"]
        g=grp(p)
        if g: cell[(k,g)]+=p["Area_ha"];state[(p["State"],g)]+=p["Area_ha"]
R=lambda x:round(x)
json.dump([{"lon":k[0],"lat":k[1],"commodity":g,"hectares":R(v)} for (k,g),v in cell.items() if v>=50],open("data/commodity_cells.json","w"),separators=(",",":"))
json.dump([{"lon":k[0],"lat":k[1]} for k in land],open("data/land_cells.json","w"),separators=(",",":"))
json.dump([{"state":s,"commodity":g,"hectares":R(v)} for (s,g),v in state.items()],open("data/commodity_by_state.json","w"),indent=1)
json.dump([{"class":k,"hectares":R(v)} for k,v in broad.items()],open("data/landuse_classes.json","w"),indent=1)
# irrigation areas: keep non-void, 2dp coords, per-cell total (km2, equal-area approx)
d=json.load(open(irr));feats=[];ctot=collections.defaultdict(float)
def ring_km2(r):
    a=0;
    for (x1,y1),(x2,y2) in zip(r,r[1:]): a+=x1*y2-x2*y1
    lat=sum(p[1] for p in r)/len(r);return abs(a)/2*111.32*111.32*math.cos(math.radians(lat))
def simp(r):
    o=[];
    for x,y in r:
        q=[round(x,2),round(y,2)]
        if not o or o[-1]!=q:o.append(q)
    return o if len(o)>=4 else None
for ft in d["features"]:
    p=ft["properties"]
    if p["STATUS"].startswith("VOID"):continue
    m={"FLOOD":"Flood (other crops)"}
    t=p["IRRIGATION"];meth="Flood (cotton)" if t.startswith("COTTON") else "Flood (other crops)" if "FLOOD" in t and "SPRAY" not in t else "Spray / mixed" if ("SPRAY" in t) else "Unknown"
    polys=ft["geometry"]["coordinates"] if ft["geometry"]["type"]=="MultiPolygon" else [ft["geometry"]["coordinates"]]
    out=[];km=0
    for poly in polys:
        s=simp(poly[0])
        if s: out.append([s]);km+=ring_km2(poly[0])
    if not out: continue
    c=out[0][0][0];ctot[(math.floor(c[0]),math.floor(c[1]))]+=km
    feats.append({"type":"Feature","properties":{"name":p["NAME"].title(),"method":meth,"status":p["STATUS"].title(),"km2":round(km,1)},"geometry":{"type":"MultiPolygon","coordinates":out}})
json.dump({"type":"FeatureCollection","features":feats},open("data/irrigation_areas.geojson","w"),separators=(",",":"))
sq=lambda x,y:{"type":"Polygon","coordinates":[[[x,y],[x+1,y],[x+1,y+1],[x,y+1],[x,y]]]}
json.dump({"type":"FeatureCollection","features":[{"type":"Feature","properties":{"km2":round(v),"ha":round(v*100)},"geometry":sq(x,y)} for (x,y),v in ctot.items()]},open("data/irrigation_grid.geojson","w"),separators=(",",":"))
json.dump([{"method":m,"km2":round(sum(f["properties"]["km2"] for f in feats if f["properties"]["method"]==m))} for m in {f["properties"]["method"] for f in feats}],open("data/irrigation_methods.json","w"),indent=1)
