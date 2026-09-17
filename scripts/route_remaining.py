"""Complete local open connections without disturbing the existing routed board.

Routes are checked against all pad/track/via copper and drill clearances. KiCad
DRC remains the final authority; zone copper is refilled after route insertion.
"""
import json, math, heapq, itertools
from pathlib import Path
import numpy as np
from shapely.geometry import Point, LineString, box
from shapely.affinity import rotate, translate
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import intersects_xy

ROOT=Path(__file__).resolve().parent.parent
g=json.loads((ROOT/'verification/geometry.json').read_text())
drc=json.loads((ROOT/'verification/resume-drc.json').read_text())
LAYERS=[0,4,6,2]
items={}; copper=[]; holes=[]
for q in g['pads']:
    x,y=q['xy'];w,h=q['size']
    s=Point(x,y).buffer(w/2,quad_segs=24) if q['shape']=='circle' else translate(rotate(box(-w/2,-h/2,w/2,h/2),-q['angle'],origin=(0,0)),x,y)
    copper.append((q['net'],q['layers'],s))
    items[q['uuid']]={'net':q['net'],'points':[q['xy']],'layers':q['layers']}
    if max(q['drill'])>0:holes.append((q['net'],Point(x,y).buffer(max(q['drill'])/2)))
for q in g['tracks']:
    copper.append((q['net'],[q['layer']],LineString([q['a'],q['z']]).buffer(q['width']/2,quad_segs=24)))
    items[q['uuid']]={'net':q['net'],'points':[q['a'],q['z']],'layers':[q['layer']]}
for q in g['vias']:
    copper.append((q['net'],LAYERS,Point(q['xy']).buffer(q['size']/2,quad_segs=24)))
    holes.append((q['net'],Point(q['xy']).buffer(q['drill']/2)))
    items[q['uuid']]={'net':q['net'],'points':[q['xy']],'layers':LAYERS}

def simplify(points):
    out=[points[0]]
    for i in range(1,len(points)-1):
        a,b,c=out[-1],points[i],points[i+1]
        if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))>1e-10:out.append(b)
    out.append(points[-1]);return out

def route(a,z,width=.075,margin=4):
    net=a['net'];assert net==z['net']
    coords=a['points']+z['points'];step=.025
    x0=math.floor((min(q[0] for q in coords)-margin)/step)*step
    y0=math.floor((min(q[1] for q in coords)-margin)/step)*step
    nx=math.ceil((max(q[0] for q in coords)+margin-x0)/step)+1
    ny=math.ceil((max(q[1] for q in coords)+margin-y0)/step)+1
    local=box(x0-.5,y0-.5,x0+nx*step+.5,y0+ny*step+.5)
    obs={};prs={}
    for layer in LAYERS:
        obs[layer]=unary_union([s.buffer(.075+width/2+.0015,quad_segs=16) for n,ls,s in copper if n!=net and layer in ls and s.intersects(local)])
        prs[layer]=prep(obs[layer])
    vos=unary_union([s.buffer(.2+.075+.002,quad_segs=16) for n,ls,s in copper if n!=net and s.intersects(local)]+[s.buffer(.3+.002,quad_segs=16) for n,s in holes if s.intersects(local)]+[s.buffer(.175+.002,quad_segs=16) for n,ls,s in copper[:len(g['pads'])] if len(ls)==1 and s.intersects(local)])
    vopr=prep(vos)
    xs,ys=np.meshgrid(x0+np.arange(nx)*step,y0+np.arange(ny)*step,indexing='ij')
    blocked={l:intersects_xy(obs[l],xs,ys) for l in LAYERS}
    vb=intersects_xy(vos,xs,ys)
    def xy(ix,iy):return (round(x0+ix*step,7),round(y0+iy*step,7))
    def safe(l,p,q):return not prs[l].intersects(LineString([p,q]))
    goals={}
    for p in z['points']:
        ix,iy=round((p[0]-x0)/step),round((p[1]-y0)/step)
        for dx,dy in itertools.product(range(-2,3),repeat=2):
            for l in z['layers']:
                u,v=ix+dx,iy+dy;q=xy(u,v)
                if not blocked[l][u,v] and safe(l,q,p):goals[(u,v,l)]=p
    def heuristic(q):return min(math.dist(q,t) for t in z['points'])
    queue=[];dist={};prev={};first={};counter=itertools.count()
    for p in a['points']:
        ix,iy=round((p[0]-x0)/step),round((p[1]-y0)/step)
        for dx,dy in itertools.product(range(-2,3),repeat=2):
            for l in a['layers']:
                u,v=ix+dx,iy+dy;q=xy(u,v);key=(u,v,l)
                if not blocked[l][u,v] and safe(l,p,q):
                    c=math.dist(p,q)
                    if c<dist.get(key,1e9):dist[key]=c;prev[key]=None;first[key]=p;heapq.heappush(queue,(c+heuristic(q),next(counter),c,key))
    found=None;iters=0
    directions=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    while queue:
        _,_,cost,key=heapq.heappop(queue)
        if cost>dist[key]+1e-9:continue
        iters+=1;ix,iy,l=key;pt=xy(ix,iy)
        if key in goals:found=key;break
        for dx,dy in directions:
            u,v=ix+dx,iy+dy;k=(u,v,l)
            if not (0<=u<nx and 0<=v<ny) or blocked[l][u,v]:continue
            nc=cost+step*math.hypot(dx,dy)
            if nc>=dist.get(k,1e9)-1e-10:continue
            np_=xy(u,v)
            if not safe(l,pt,np_):continue
            dist[k]=nc;prev[k]=key;heapq.heappush(queue,(nc+heuristic(np_),next(counter),nc,k))
        if not vb[ix,iy]:
            for ll in LAYERS:
                if ll==l or blocked[ll][ix,iy]:continue
                k=(ix,iy,ll);nc=cost+1.5
                if nc<dist.get(k,1e9)-1e-10:
                    dist[k]=nc;prev[k]=key;heapq.heappush(queue,(nc+heuristic(pt),next(counter),nc,k))
    if found is None:print('FAILED',net,width,'visited',iters,'starts',len(first),'goals',len(goals),flush=True);return None
    nodes=[found]
    while prev[nodes[-1]] is not None:nodes.append(prev[nodes[-1]])
    nodes.reverse();sections=[];vias=[];l=nodes[0][2];pts=[first[nodes[0]],xy(*nodes[0][:2])]
    for u,v,ll in nodes[1:]:
        q=xy(u,v)
        if ll!=l:
            sections.append({'layer':l,'points':simplify(pts),'width':width});vias.append(q);pts=[q];l=ll
        else:pts.append(q)
    pts.append(goals[found]);sections.append({'layer':l,'points':simplify(pts),'width':width})
    for sec in sections:
        pts=sec['points'];assert not prs[sec['layer']].intersects(LineString(pts))
        copper.append((net,[sec['layer']],LineString(pts).buffer(width/2,quad_segs=24)))
    for q in vias:
        assert not vopr.intersects(Point(q))
        copper.append((net,LAYERS,Point(q).buffer(.2,quad_segs=24)));holes.append((net,Point(q).buffer(.1)))
    print('ROUTED',net,'length',round(dist[found],3),'vias',len(vias),'visited',iters,flush=True)
    return {'net':net,'sections':sections,'vias':vias}

if __name__=='__main__':
    results=[]
    for i in [5,0,1,2,3,4,6]:
        v=drc['unconnected_items'][i];a,z=[items[x['uuid']] for x in v['items']]
        print('CONNECTION',i,a,z,flush=True)
        r=route(a,z)
        if r:results.append(r)
    (ROOT/'verification/completion-routes.json').write_text(json.dumps(results,indent=2))
    print('COMPLETED',len(results),flush=True)
