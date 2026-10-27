"""Shrinks ABS boundary files and adds irrigated area per drainage division.
Usage: python3 scripts/prepare_boundaries.py australia_states.json drainage_divisions.json"""
import json,sys
def simp(r,nd=2):
    o=[]
    for x,y in r:
        q=[round(x,nd),round(y,nd)]
        if not o or o[-1]!=q:o.append(q)
    return o if len(o)>=4 else None
def area(r): return sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(r,r[1:]))/2
def rewind(rings):
    # Vega/d3 wants exterior rings clockwise and holes counter-clockwise (opposite of the GeoJSON standard)
    return [r if (area(r)<0)==(i==0) else r[::-1] for i,r in enumerate(rings)]
def clean(path,keep,skip=lambda p:False,minspan=0.0):
    out=[]
    for f in json.load(open(path))["features"]:
        if not f["geometry"] or skip(f["properties"]):continue
        g=f["geometry"];polys=g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
        np=[]
        for poly in polys:
            rings=[simp(r) for r in poly];rings=[r for r in rings if r]
            if not rings:continue
            xs=[p[0] for p in rings[0]];ys=[p[1] for p in rings[0]]
            if max(xs)-min(xs)<minspan and max(ys)-min(ys)<minspan:continue
            np.append(rewind(rings))
        if np: out.append({"type":"Feature","properties":{k:f["properties"][v] for k,v in keep.items()},"geometry":{"type":"MultiPolygon","coordinates":np}})
    return out
states=clean(sys.argv[1],{"name":"STE_NAME21"},skip=lambda p:p["STE_NAME21"]=="Other Territories",minspan=0.05)
div=clean(sys.argv[2],{"code":"ADD_CODE21","name":"ADD_NAME21"},skip=lambda p:p["ADD_CODE21"] in("D91","D94","D97","DZZ"),minspan=0.05)
def inside(pt,ring):
    x,y=pt;c=False
    for (x1,y1),(x2,y2) in zip(ring,ring[1:]):
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
    return c
tot={f["properties"]["code"]:[0.0,0] for f in div};miss=0
for a in json.load(open("data/irrigation_areas.geojson"))["features"]:
    ring=a["geometry"]["coordinates"][0][0];pt=(sum(p[0] for p in ring)/len(ring),sum(p[1] for p in ring)/len(ring))
    hit=None
    for f in div:
        if any(inside(pt,p[0]) for p in f["geometry"]["coordinates"]):hit=f["properties"]["code"];break
    if hit is None: hit=None;miss+=1;continue
    tot[hit][0]+=a["properties"]["km2"];tot[hit][1]+=1
for f in div:
    k,n=tot[f["properties"]["code"]];f["properties"].update({"irrigated_km2":round(k),"irrigated_ha":round(k*100),"schemes":n})
# state tooltip values: mapped crop area (CLUM) and mapped irrigation area (irrigation districts)
ABBR={"ACT":"Australian Capital Territory","NSW":"New South Wales","NT":"Northern Territory","Qld":"Queensland","SA":"South Australia","Tas":"Tasmania","Vic":"Victoria","WA":"Western Australia"}
crop={}
for r in json.load(open("data/commodity_by_state.json")): crop[ABBR[r["state"]]]=crop.get(ABBR[r["state"]],0)+r["hectares"]
irr={}
for a in json.load(open("data/irrigation_areas.geojson"))["features"]:
    ring=a["geometry"]["coordinates"][0][0];pt=(sum(p[0] for p in ring)/len(ring),sum(p[1] for p in ring)/len(ring))
    for f in states:
        if any(inside(pt,p[0]) for p in f["geometry"]["coordinates"]):
            irr[f["properties"]["name"]]=irr.get(f["properties"]["name"],0)+a["properties"]["km2"]*100;break
for f in states: n=f["properties"]["name"];f["properties"].update({"crop_ha":round(crop.get(n,0)),"irrigated_ha":round(irr.get(n,0))})
json.dump({"type":"FeatureCollection","features":states},open("data/australia_states.json","w"),separators=(",",":"))
json.dump({"type":"FeatureCollection","features":div},open("data/drainage_divisions.json","w"),separators=(",",":"))
print("unmatched schemes:",miss);[print(f["properties"]) for f in div]

# also normalise winding of the irrigation areas used by Map 3
ia=json.load(open("data/irrigation_areas.geojson"))
for f in ia["features"]: f["geometry"]["coordinates"]=[rewind(p) for p in f["geometry"]["coordinates"]]
json.dump(ia,open("data/irrigation_areas.geojson","w"),separators=(",",":"))
