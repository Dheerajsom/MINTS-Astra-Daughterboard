import os,math,json,shutil,sys
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent.parent;os.chdir(ROOT)
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb')
if '--keep-routing' not in sys.argv:
 assert p.ImportSpecctraSES(b,'verification/routed.ses')
 p.SaveBoard('verification/routed-before-finish.kicad_pcb',b)
foots={f.GetReference():f for f in b.GetFootprints()};netobjs={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
# Put reference designators where they are readable without colliding with pads.
for ref in ['J5','J6','J7','J8','J9']:
 foots[ref].Reference().SetLayer(p.F_Fab)
for ref,x,y in [('R1',114,112.5),('R2',116.5,112.5),('R3',119,112.5),('R11',112,90),('FB1',104.5,101),('D1',114.5,115)]:
 t=foots[ref].Reference();t.SetPosition(v(x,y));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
foots['JP4'].Reference().SetPosition(v(143.7,77.6))
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT):
  if t.GetText()=='REV B / 120 x 80 mm':t.SetPosition(v(147,116.5))
  if t.GetText()=='ADuCM355 / REQUIRES FIRMWARE + CALIBRATION':t.SetPosition(v(110,118))
# Zone fills are kept off the ambient sensor and high-impedance sensor surface routes.
def polygon_zone(net,layer,pts,priority=0,clear=.2):
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(netobjs[net]);z.SetLocalClearance(mm(clear));z.SetMinThickness(mm(.15));z.SetPadConnection(p.ZONE_CONNECTION_THERMAL);z.SetThermalReliefGap(mm(.2));z.SetThermalReliefSpokeWidth(mm(.25));z.SetAssignedPriority(priority);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
 o=z.Outline();o.NewOutline()
 for x,y in pts:o.Append(mm(x),mm(y))
 b.Add(z);return z
analog=[(50.5,50.5),(105.5,50.5),(105.5,63),(114.5,63),(114.5,50.5),(169.5,50.5),(169.5,85.25),(50.5,85.25)]
digital=[(50.5,85.55),(169.5,85.55),(169.5,129.5),(50.5,129.5)]
polygon_zone('AGND',p.In1_Cu,analog,clear=.15);polygon_zone('GND',p.In1_Cu,digital,clear=.15)
# Surface ground shields with space around sensor electrodes.
for layer in [p.F_Cu,p.B_Cu]:
 polygon_zone('AGND',layer,analog,clear=.35);polygon_zone('GND',layer,digital,clear=.25)
# Distributed power planes on layer 3; routed signals have priority through clearances.
polygon_zone('+3V3A',p.In2_Cu,[(60,76),(104,76),(104,92),(116,92),(116,76),(159,76),(159,97),(60,97)],clear=.2)
polygon_zone('+3V3',p.In2_Cu,[(60,98),(160,98),(160,127),(60,127)],clear=.2)
def keepout(pts,layers):
 z=p.ZONE(b);z.SetIsRuleArea(True);ls=p.LSET()
 for l in layers:ls.AddLayer(l)
 z.SetLayerSet(ls);z.SetDoNotAllowTracks(False);z.SetDoNotAllowVias(False);z.SetDoNotAllowPads(False);z.SetDoNotAllowZoneFills(True)
 o=z.Outline();o.NewOutline()
 for x,y in pts:o.Append(mm(x),mm(y))
 b.Add(z)
for x1,x2 in [(68,97),(123,152)]:keepout([(x1,65),(x2,65),(x2,85),(x1,85)],[p.F_Cu,p.B_Cu])
# Representative 3D bodies, for visualization only; land patterns are authoritative.
Path('models').mkdir(exist_ok=True)
Path('models/ADuCM355.wrl').write_text('''#VRML V2.0 utf8
Transform { translation 0 0 0.216535 children [ Shape { appearance Appearance { material Material { diffuseColor 0.08 0.08 0.085 } } geometry Box { size 2.362205 1.968504 0.354331 } } ] }
''')
# Mill-Max 0548 sleeve envelope. The top surface of the socket is ~0.79 mm above PCB.
parts=['#VRML V2.0 utf8']
for x in [-2.54,0,2.54]:
 parts.append('Transform { translation %s 0 %s rotation 1 0 0 1.570796 children [ Shape { appearance Appearance { material Material { diffuseColor 0.72 0.55 0.2 metallic 0 } } geometry Cylinder { radius %s height %s } } ] }'%(x/2.54,-.95/2.54,.432/2.54,3.5/2.54))
 parts.append('Transform { translation %s 0 %s rotation 1 0 0 1.570796 children [ Shape { appearance Appearance { material Material { diffuseColor 0.72 0.55 0.2 } } geometry Cylinder { radius %s height %s } } ] }'%(x/2.54,.395/2.54,.737/2.54,.79/2.54))
Path('models/ES1_receptacles.wrl').write_text('\n'.join(parts).replace(' metallic 0',''))
for ref,model in [('U1','ADuCM355'),('U2','ADuCM355')]+[(f'J{i}','ES1_receptacles') for i in range(1,5)]:
 m=p.FP_3DMODEL();m.m_Filename='${KIPRJMOD}/models/'+model+'.wrl';m.m_Scale=p.VECTOR3D(1,1,1);foots[ref].Add3DModel(m)
# Dimensions in the fabrication documentation layer.
for a,z,h in [((50,50),(170,50),-6),((170,50),(170,130),-7)]:
 d=p.PCB_DIM_ALIGNED(b);d.SetStart(v(*a));d.SetEnd(v(*z));d.SetHeight(mm(h));d.SetLayer(p.Dwgs_User);d.SetTextSize(v(1.2,1.2));d.SetTextThickness(mm(.15));d.SetLineThickness(mm(.15));d.SetPrecision(0);d.SetSuppressZeroes(True);d.SetUnitsMode(p.DIM_UNITS_MODE_MM);d.SetUnitsFormat(p.DIM_UNITS_FORMAT_BARE_SUFFIX);d.Update();b.Add(d)
# Tented vias protect high impedance areas from contamination.
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA):
  try:t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
  except:pass
b.BuildConnectivity();filler=p.ZONE_FILLER(b);filler.Fill(b.Zones());p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
print('Final copper',len(list(b.GetTracks())),'zones',len(list(b.Zones())))
