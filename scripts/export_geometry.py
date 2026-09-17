import pcbnew as p,json,os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb')
xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
r={'pads':[],'tracks':[],'vias':[]}
for f in b.GetFootprints():
 for pad in f.Pads():
  r['pads'].append(dict(uuid=pad.m_Uuid.AsString(),ref=f.GetReference(),num=pad.GetNumber(),net=pad.GetNetname(),xy=xy(pad.GetPosition()),size=xy(pad.GetSize()),drill=xy(pad.GetDrillSize()),angle=pad.GetOrientationDegrees(),shape='circle' if pad.GetShape()==p.PAD_SHAPE_CIRCLE else 'rect',layers=[l for l in [0,4,6,2] if pad.IsOnLayer(l)],pth=pad.GetAttribute()!=p.PAD_ATTRIB_SMD))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):r['vias'].append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),xy=xy(t.GetPosition()),size=p.ToMM(t.GetWidth(p.F_Cu)),drill=p.ToMM(t.GetDrill())))
 else:r['tracks'].append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),a=xy(t.GetStart()),z=xy(t.GetEnd()),width=p.ToMM(t.GetWidth()),layer=t.GetLayer()))
json.dump(r,open('verification/geometry.json','w'))
