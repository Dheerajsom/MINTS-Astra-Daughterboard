from route_remaining import *
def pad(ref,pin):
 return items[next(q['uuid'] for q in g['pads'] if q['ref']==ref and q['num']==pin)]
def endpoint(net,xy,layers):return {'net':net,'points':[xy],'layers':layers}
requests=[
 (pad('U2','H4'),items['f4ecc370-80b1-4ccb-9a55-5ca6093bfae3']),
 (pad('U2','H5'),items['3fde5620-babb-45a9-8eb6-5551154e727c']),
 (endpoint('/U2_SWDIO',[137.525,90.025],[4]),items['f4ecc370-80b1-4ccb-9a55-5ca6093bfae3']),
 (endpoint('/SDA',[136.714,85.744],[6]),items['3fde5620-babb-45a9-8eb6-5551154e727c']),
 (pad('U1','H2'),items['c6ab5d87-c933-4442-b7b2-790056e38c8f']),
 (pad('U1','H4'),endpoint('/U1_SWDIO',[78.6452,86.7501],[0])),
]
results=[]
for i,(a,z) in enumerate(requests):
 print('REQUEST',i,a,z,flush=True)
 r=route(a,z,margin=5)
 if r:results.append(r)
(ROOT/'verification/completion-routes.json').write_text(json.dumps(results,indent=2))
print('COMPLETED',len(results),'of',len(requests),flush=True)
