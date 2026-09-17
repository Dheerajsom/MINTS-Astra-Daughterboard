import os
from pathlib import Path
import pcbnew as p
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb');mm=p.FromMM
positions={'AGND':[(60,60),(100,60),(120,60),(160,60),(60,80),(110,80),(160,80),(65,53),(100,53),(120,53),(155,53)],
           'GND':[(54,95),(54,115),(166,95),(166,115),(65,128),(90,128),(130,128),(155,128),(100,110),(120,100)]}
for net,pts in positions.items():
    for x,y in pts:
        q=p.PCB_VIA(b);q.SetPosition(p.VECTOR2I(mm(x),mm(y)));q.SetWidth(mm(.6));q.SetDrill(mm(.3));q.SetViaType(p.VIATYPE_THROUGH);q.SetLayerPair(p.F_Cu,p.B_Cu);q.SetNet(b.FindNet(net));q.SetFrontTentingMode(p.TENTING_MODE_TENTED);q.SetBackTentingMode(p.TENTING_MODE_TENTED);b.Add(q)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
print('Added',sum(map(len,positions.values())),'ground stitching vias')
