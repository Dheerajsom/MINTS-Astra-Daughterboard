import pcbnew as p,json,os
from pathlib import Path
from board_rules import configure
os.chdir(Path(__file__).resolve().parent.parent);b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb');configure(b)
mm=p.FromMM;v=lambda xy:p.VECTOR2I(mm(xy[0]),mm(xy[1]));xy=lambda q:[p.ToMM(q.x),p.ToMM(q.y)]
rem=json.load(open('verification/ripup.json'));removed=0
for t in list(b.GetTracks()):
 if isinstance(t,p.PCB_VIA):continue
 if any(t.GetLayer()==d['layer'] and t.GetNetname()==d['net'] and xy(t.GetStart())==d['a'] and xy(t.GetEnd())==d['z'] for d in rem):b.Remove(t);removed+=1
for q in json.load(open('verification/manual-routes.json')):
 net=b.FindNet(q['net'])
 for pts,layer,width in [(q['front'],p.F_Cu,.075),(q['inner'],p.In1_Cu,.1)]:
  for a,z in zip(pts,pts[1:]):
   if a==z:continue
   t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(net);t.SetLocked(True);b.Add(t)
 via=p.PCB_VIA(b);via.SetPosition(v(q['via']));via.SetWidth(mm(.4));via.SetDrill(mm(.2));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(net);via.SetLocked(True);b.Add(via)
b.BuildConnectivity();p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b);p.SaveBoard('verification/manual-escape.kicad_pcb',b);p.ExportSpecctraDSN(b,'verification/manual-escape.dsn');print('Removed',removed)
