import json
from shapely.geometry import Point,LineString
r=json.load(open('verification/geometry.json'));routes=json.load(open('verification/manual-routes.json'));remove=[]
for t in r['tracks']:
 sh=LineString([t['a'],t['z']]).buffer(t['width']/2)
 for q in routes:
  if t['net']==q['net']:continue
  geoms=[Point(*q['via']).buffer(.276)]
  if t['layer']==0:geoms += [LineString(q['front']).buffer(.1135)]
  if t['layer']==4:geoms += [LineString(q['inner']).buffer(.126)]
  if any(sh.intersects(g) for g in geoms):remove.append(t);break
json.dump(remove,open('verification/ripup.json','w'));print('Reroute',len(remove),'segments on',sorted(set(x['net'] for x in remove)))
