import json,math,heapq,itertools
from shapely.geometry import Point,LineString,box
from shapely.affinity import rotate,translate
from shapely.ops import unary_union
from shapely.prepared import prep
r=json.load(open('verification/geometry.json'))
allshapes=[];padshapes=[]
for pad in r['pads']:
 x,y=pad['xy'];w,h=pad['size']
 sh=Point(x,y).buffer(w/2) if pad['shape']=='circle' else translate(rotate(box(-w/2,-h/2,w/2,h/2),-pad['angle'],origin=(0,0)),x,y)
 allshapes.append((pad['net'],pad['layers'],sh));padshapes.append((pad,sh))
for t in r['tracks']:
 allshapes.append((t['net'],[t['layer']],LineString([t['a'],t['z']]).buffer(t['width']/2,cap_style=1)))
for via in r['vias']:allshapes.append((via['net'],[0,4,6,2],Point(*via['xy']).buffer(via['size']/2)))

result=[]
def solve(ref,pin,target_ref=None,target_pin=None):
 pad=next(q for q in r['pads'] if q['ref']==ref and q['num']==pin);net=pad['net'];start=pad['xy']
 if target_ref:target=next(q['xy'] for q in r['pads'] if q['ref']==target_ref and q['num']==target_pin)
 else:target=min([t['xy'] for t in r['vias'] if t['net']==net],key=lambda xy:math.dist(xy,start))
 # Restrict obstacles to a local neighborhood to make the fine-pitch escape fast.
 local=box(start[0]-6,start[1]-6,start[0]+6,start[1]+6)
 obstacle=unary_union([sh.buffer(.075+.0375+.001) for n,ls,sh in allshapes if n!=net and 0 in ls and sh.intersects(local) and (len(ls)>1 or any(sh is ps for _,ps in padshapes))])
 ob=prep(obstacle)
 via_obstacle=unary_union([sh.buffer(.2+.075+.003) for n,ls,sh in allshapes if n!=net and sh.intersects(local) and (len(ls)>1 or any(sh is ps for _,ps in padshapes))]+[sh.buffer(.1+.075) for q,sh in padshapes if not q['pth'] and sh.intersects(local)])
 vo=prep(via_obstacle)
 step=.025;queue=[(0,0,0,0)];dist={(0,0):0};prev={};goal=None;iters=0
 while queue:
  _,cost,ix,iy=heapq.heappop(queue)
  if cost>dist[(ix,iy)]+1e-8:continue
  pt=(start[0]+ix*step,start[1]+iy*step);iters+=1
  if cost>.3 and not vo.intersects(Point(pt)):
   goal=(ix,iy);break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nx,ny=ix+dx,iy+dy
   if abs(nx)>220 or abs(ny)>220:continue
   np=(start[0]+nx*step,start[1]+ny*step)
   if ob.intersects(LineString([pt,np])):continue
   nc=cost+step*math.hypot(dx,dy)
   if nc+1e-8<dist.get((nx,ny),1e99):
    dist[nx,ny]=nc;prev[nx,ny]=(ix,iy);h=.1*math.dist(np,target);heapq.heappush(queue,(nc+h,nc,nx,ny))
 assert goal,('No escape',ref,pin,iters)
 nodes=[goal]
 while nodes[-1]!=(0,0):nodes.append(prev[nodes[-1]])
 pts=[[round(start[0]+ix*step,6),round(start[1]+iy*step,6)] for ix,iy in nodes[::-1]]
 def simplify(pts):
  out=[pts[0]]
  for i in range(1,len(pts)-1):
   a,b,c=out[-1],pts[i],pts[i+1]
   if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))>1e-8:out.append(b)
  out.append(pts[-1]);return out
 pts=simplify(pts);vp=pts[-1]
 # Inner layer is available for the local escape and connection to an existing through feature.
 obs=prep(unary_union([sh.buffer(.075+.05+.003) for n,ls,sh in allshapes if n!=net and 4 in ls]))
 st=.05;queue=[(math.dist(vp,target),0,0,0)];dist={(0,0):0};prev={};g=None
 while queue:
  _,cost,ix,iy=heapq.heappop(queue)
  if cost>dist[ix,iy]+1e-8:continue
  pt=(vp[0]+ix*st,vp[1]+iy*st)
  if math.dist(pt,target)<.15 and not obs.intersects(LineString([pt,target])):g=(ix,iy);break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   nx,ny=ix+dx,iy+dy;np=(vp[0]+nx*st,vp[1]+ny*st)
   if not (min(vp[0],target[0])-5<np[0]<max(vp[0],target[0])+5 and min(vp[1],target[1])-5<np[1]<max(vp[1],target[1])+5):continue
   if obs.intersects(LineString([pt,np])):continue
   nc=cost+st*math.hypot(dx,dy)
   if nc+1e-8<dist.get((nx,ny),1e99):dist[nx,ny]=nc;prev[nx,ny]=(ix,iy);heapq.heappush(queue,(nc+math.dist(np,target),nc,nx,ny))
 assert g,('No inner route',ref)
 nodes=[g]
 while nodes[-1]!=(0,0):nodes.append(prev[nodes[-1]])
 inner=simplify([[round(vp[0]+ix*st,6),round(vp[1]+iy*st,6)] for ix,iy in nodes[::-1]]+[target])
 result.append(dict(net=net,front=pts,via=vp,inner=inner));print(ref,pin,net,'escape',pts,'inner points',len(inner),flush=True)
 for a,z in zip(pts,pts[1:]):allshapes.append((net,[0],LineString([a,z]).buffer(.0375)))
 allshapes.append((net,[0,4,6,2],Point(*vp).buffer(.2)))
 for a,z in zip(inner,inner[1:]):allshapes.append((net,[4],LineString([a,z]).buffer(.05)))
solve('U1','F2')
solve('U2','H4','J7','2')
json.dump(result,open('verification/manual-routes.json','w'),indent=2)
