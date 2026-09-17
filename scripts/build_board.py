import os, math, shutil, json, xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parent.parent;os.chdir(ROOT)
STD=Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints')
mm=p.FromMM
v=lambda x,y:p.VECTOR2I(mm(x),mm(y))
# CC-72-2: top-view grid, 11 columns x 9 rows (I omitted), 0.5 mm pitch.
rows={'A':list(range(1,12)),'B':list(range(1,12)),'C':[1,2,10,11], 'D':[1,2,5,6,7,10,11],'E':[1,2,5,7,10,11],'F':[1,2,5,6,7,10,11],'G':[1,2,10,11],'H':list(range(1,12)),'J':list(range(1,12))}
assert sum(map(len,rows.values()))==72
head='''(footprint "ADuCM355_LGA-72_6x5mm" (version 20241229) (generator pcbnew) (layer "F.Cu")
(descr "Analog Devices CC-72-2, 6x5 mm, 72 lands on 0.5 mm grid. Datasheet Rev C Fig 7/20. 0.25 mm NSMD copper lands.") (tags "ADuCM355 CC-72-2") (attr smd)
(fp_text reference "REF**" (at 0 -3.7) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))
(fp_text value "ADuCM355" (at 0 3.7) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))
(fp_rect (start -3 -2.5) (end 3 2.5) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))
(fp_rect (start -3.25 -2.75) (end 3.25 2.75) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
(fp_rect (start -3.12 -2.62) (end 3.12 2.62) (stroke (width 0.12) (type default)) (fill none) (layer "F.SilkS"))
(fp_circle (center -3.55 -2.8) (end -3.4 -2.8) (stroke (width 0.12) (type default)) (fill solid) (layer "F.SilkS"))
'''
for ri,(row,cols) in enumerate(rows.items()):
 for col in cols:
  head+=f'(pad "{row}{col}" smd roundrect (at {(col-6)*.5} {(ri-4)*.5}) (size 0.25 0.25) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.1) (solder_mask_margin 0.025))\n'
head+=')\n';Path('ECGAS.pretty/ADuCM355_LGA-72_6x5mm.kicad_mod').write_text(head)
s='''(footprint "EC_Sense_ES1_3pin_2.54mm" (version 20241229) (generator pcbnew) (layer "F.Cu")
(descr "EC Sense ES1 socket, 3x Mill-Max 0548-0-15-15-21-27-10-0, 1.00 mm finished PTH, 2.54 mm pitch. C/S/R shown in TOP view. Conservative 14x24 mm sensor body envelope about pin row.") (attr through_hole)
(fp_text reference "REF**" (at 0 13.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
(fp_text value "ES1 SENSOR" (at 0 -13.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
(fp_rect (start -7 -12) (end 7 12) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
(fp_rect (start -6.4 -11.6) (end 6.4 11.6) (stroke (width 0.1) (type dash)) (fill none) (layer "F.Fab"))
'''
for num,x,label in [(1,2.54,'C'),(2,0,'S'),(3,-2.54,'R')]:
 s+=f'(pad "{num}" thru_hole {"rect" if num==1 else "circle"} (at {x} 0) (size 1.8 1.8) (drill 1.0) (layers "*.Cu" "*.Mask"))\n'
 s+=f'(fp_text user "{label}" (at {x} 2) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))\n'
s+=')\n';Path('ECGAS.pretty/EC_Sense_ES1_3pin_2.54mm.kicad_mod').write_text(s)
# Preserve standard footprints locally so the project is self-contained.
tree=ET.parse('verification/current.xml'); comps=tree.findall('.//components/comp'); nets=tree.findall('.//nets/net')
libs={'ECGAS':'${KIPRJMOD}/ECGAS.pretty'}
for c in comps:
 fp=c.findtext('footprint');lib,name=fp.split(':');
 if lib=='ECGAS':continue
 dest=Path('libraries')/(lib+'.pretty');dest.mkdir(parents=True,exist_ok=True)
 shutil.copy2(STD/(lib+'.pretty')/(name+'.kicad_mod'),dest/(name+'.kicad_mod'))
 libs[lib]='${KIPRJMOD}/'+str(dest)
for lib,name in [('MountingHole','MountingHole_3.2mm_M3'),('TestPoint','TestPoint_Pad_D1.0mm')]:
 dest=Path('libraries')/(lib+'.pretty');dest.mkdir(parents=True,exist_ok=True);shutil.copy2(STD/(lib+'.pretty')/(name+'.kicad_mod'),dest/(name+'.kicad_mod'));libs[lib]='${KIPRJMOD}/'+str(dest)
Path('fp-lib-table').write_text('(fp_lib_table (version 7)\n'+''.join(f'(lib (name "{k}")(type "KiCad")(uri "{val}")(options "")(descr "Project-local verified footprint"))\n' for k,val in libs.items())+')\n')
# Board and project constraints for the 0.5 mm LGA. Short neck-downs need 3 mil clearance.
pr=json.load(open('ECSense_4CH_I2C.kicad_pro'))
cls=pr['net_settings']['classes'][0]
cls.update(clearance=.075,track_width=.1,via_diameter=.4,via_drill=.2)
pr['net_settings']['classes']=[cls]
pr['net_settings']['netclass_patterns']=[]
rules=pr['board']['design_settings']['rules'];rules.update(min_clearance=.075,min_track_width=.1,min_via_diameter=.4,min_through_hole_diameter=.2,min_via_annular_width=.1,min_via_annulus=.1,min_hole_to_hole=.2,min_copper_edge_clearance=.3,min_hole_clearance=.15,min_silk_clearance=.1,min_text_height=.65,min_text_thickness=.1)
sev=pr['board']['design_settings']['rule_severities'];sev.update(courtyards_overlap='error',silk_over_copper='warning',silk_overlap='warning',missing_courtyard='warning')
json.dump(pr,open('ECSense_4CH_I2C.kicad_pro','w'),indent=2)
b=p.BOARD(); b.SetFileName(str(ROOT/'ECSense_4CH_I2C.kicad_pcb'));b.SetCopperLayerCount(4)
ds=b.GetDesignSettings();ds.m_MinClearance=mm(.075);ds.m_TrackMinWidth=mm(.1);ds.m_ViasMinSize=mm(.4);ds.m_MinThroughDrill=mm(.2);ds.m_ViasMinAnnularWidth=mm(.1);ds.m_HoleToHoleMin=mm(.2);ds.m_MinSilkTextHeight=mm(.65);ds.m_MinSilkTextThickness=mm(.1)
try:
 nc=ds.m_NetSettings.GetDefaultNetclass();nc.SetClearance(mm(.075));nc.SetTrackWidth(mm(.1));nc.SetViaDiameter(mm(.4));nc.SetViaDrill(mm(.2))
except Exception as e: print('netclass',e)
netobjs={};pin_nets={}
for n in nets:
 name=n.get('name');net=p.NETINFO_ITEM(b,name);b.Add(net);netobjs[name]=net
 for node in n.findall('node'):pin_nets[(node.get('ref'),node.get('pin'))]=name
foot={}
# Exact coordinates are in mm. Board outline (50,50)-(170,130).
pos={'U1':(82,85,0),'U2':(138,85,0),'J1':(75,69,0),'J2':(90,69,0),'J3':(130,69,0),'J4':(145,69,0),
'J5':(105,123,0),'J6':(80,113,90),'J7':(135,113,90),'J8':(71,123,90),'J9':(141,123,90),
'U3':(108,107,0),'U4':(110,57,0),'U5':(125,108,0),'D1':(112,116,0),
'FB1':(107,101,90),'R11':(110,90,90),'R1':(114,110,90),'R2':(116.5,110,90),'R3':(119,110,90),'R4':(121.5,116,0),
'C33':(104,107,90),'C34':(112,106,90),'C35':(112,103,90),'C36':(107,97.5,90),'C37':(110,97.5,90),'C56':(113,57,90),'C65':(131,106,90),
'R5':(81,101,0),'R6':(137,101,0),'R7':(85,101,0),'R8':(141,101,0),
'R9':(82,77,0),'R10':(138,77,0)}
# Repeated low-leakage analog networks and EMC capacitors on the back.
back=set(['R9','R10'])
for ch,jx in enumerate([75,90,130,145],1):
 n=(ch-1)*8
 for k,dx in [(1,2.54),(2,0),(3,-2.54)]:pos[f'C{n+k}']=(jx+dx,71.7,90);back.add(f'C{n+k}')
 pos[f'JP{ch}']=(jx-1.3,75.5,0);back.add(f'JP{ch}')
# Local parts directly around their associated silicon pins (back side).
for dev,cx,base,refbase in [(1,82,0,38),(2,138,16,45)]:
 analog={4:(-5.3,-1.5,90),5:(-4.5,1.5,0),6:(-3,-5,90),7:(-2.3,-2.3,0),8:(-2.2,-.5,0),12:(5.3,-1.5,90),13:(4.5,1.5,0),14:(3,-5,90),15:(2.3,-2.3,0),16:(2.2,-.5,0)}
 for idx,(dx,dy,rot) in analog.items():pos[f'C{base+idx}']=(cx+dx,85+dy,rot);back.add(f'C{base+idx}')
 local=[(-1,-5,90),(-5.3,4,90),(5.3,4,90),(0,2,0),(1.5,5,90),(-2.2,4.5,0),(8,7.7,90)]
 for j,(dx,dy,rot) in enumerate(local):pos[f'C{refbase+j}']=(cx+dx,85+dy,rot);back.add(f'C{refbase+j}')
 for idx,dx,dy,rot in [(52 if dev==1 else 54,3.5,8.5,0),(53 if dev==1 else 55,7.5,4,90), (57 if dev==1 else 61,7.5,.5,90),(58 if dev==1 else 62,-4.5,7,0),(59 if dev==1 else 63,0,8.5,90),(60 if dev==1 else 64,-7.5,2,90)]:
  pos[f'C{idx}']=(cx+dx,85+dy,rot);back.add(f'C{idx}')
rootid=ET.parse('verification/current.xml').find('.//design/sheet').get('tstamps','') if ET.parse('verification/current.xml').find('.//design/sheet') is not None else ''
for c in comps:
 ref=c.get('ref');lib,name=c.findtext('footprint').split(':');path=ROOT/('ECGAS.pretty' if lib=='ECGAS' else 'libraries/'+lib+'.pretty')
 f=p.FootprintLoad(str(path),name);assert f,ref
 f.SetReference(ref);f.SetValue(c.findtext('value'));f.SetFPID(p.LIB_ID(lib,name));b.Add(f)
 assert ref in pos,ref
 x,y,rot=pos[ref];f.SetPosition(v(x,y));f.SetOrientationDegrees(rot)
 if ref in back:f.Flip(v(x,y),False)
 sp=c.find('sheetpath').get('tstamps','/')
 uuid=c.findtext('tstamps').split()[0]
 f.SetPath(p.KIID_PATH(sp.rstrip('/')+'/'+uuid))
 f.SetDNP(c.find('property[@name="dnp"]') is not None or ref.startswith('JP'))
 for pad in f.Pads():
  net=pin_nets.get((ref,pad.GetNumber()))
  if net:pad.SetNet(netobjs[net])
 f.Value().SetVisible(False)
 f.Reference().SetTextSize(v(.7,.7));f.Reference().SetTextThickness(mm(.1));f.Reference().SetKeepUpright(True)
 # Put dense passive references on assembly layer; section labels remain on silkscreen.
 if ref.startswith('C') or ref in ['R9','R10']:
  f.Reference().SetLayer(p.B_Fab if ref in back else p.F_Fab)
 else:
  f.Reference().SetPosition(v(x,y+(3.6 if ref.startswith('U') else 1.6)))
 if ref.startswith('J') and not ref.startswith('JP'):f.Reference().SetPosition(v(x,y+13 if ref in ['J1','J2','J3','J4'] else y-3))
 foot[ref]=f
# Mechanical mounting holes.
for i,(x,y) in enumerate([(55,55),(165,55),(55,125),(165,125)],1):
 f=p.FootprintLoad(str(ROOT/'libraries/MountingHole.pretty'),'MountingHole_3.2mm_M3');b.Add(f);f.SetReference('H'+str(i));f.SetValue('M3');f.SetPosition(v(x,y));f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);f.Reference().SetVisible(False);f.Value().SetVisible(False)
# Test pads - independent of schematic, same-net copper access.
for i,(name,x,y,label) in enumerate([('VIN',101,118,'VIN'),('+3V3',105,111,'3V3'),('+3V3A',105,94,'3V3A'),('GND',117,118,'GND'),('AGND',110,87,'AGND'),('/U1_BM',87,105,'BOOT1'),('/U2_BM',143,105,'BOOT2'),('/SDA',123,120,'SDA'),('/SCL',127,120,'SCL')],1):
 f=p.FootprintLoad(str(ROOT/'libraries/TestPoint.pretty'),'TestPoint_Pad_D1.0mm');b.Add(f);f.SetReference('TP'+str(i));f.SetValue(label);f.SetPosition(v(x,y));f.SetAttributes(f.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES);f.Reference().SetVisible(False);f.Value().SetVisible(False)
 for pad in f.Pads():pad.SetNet(netobjs[name])
# Outline with 3 mm corner radii, exact outside dimensions 120 x 80 mm.
def line(a,z,layer,width=.1):
 q=p.PCB_SHAPE();q.SetShape(p.SHAPE_T_SEGMENT);q.SetStart(v(*a));q.SetEnd(v(*z));q.SetLayer(layer);q.SetWidth(mm(width));b.Add(q)
def arc(a,m,z):
 q=p.PCB_SHAPE();q.SetShape(p.SHAPE_T_ARC);q.SetArcGeometry(v(*a),v(*m),v(*z));q.SetLayer(p.Edge_Cuts);q.SetWidth(mm(.05));b.Add(q)
for a,z in [((53,50),(167,50)),((170,53),(170,127)),((167,130),(53,130)),((50,127),(50,53))]:line(a,z,p.Edge_Cuts,.05)
c=.878679656
for a,m,z in [((167,50),(170-c,50+c),(170,53)),((170,127),(170-c,130-c),(167,130)),((53,130),(50+c,130-c),(50,127)),((50,53),(50+c,50+c),(53,50))]:arc(a,m,z)
def text(txt,x,y,size=1,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(v(x,y));t.SetTextSize(v(size,size));t.SetTextThickness(mm(.15 if size>=1 else .12));t.SetLayer(layer);t.SetMirrored(layer==p.B_SilkS);b.Add(t)
text('EC SENSE / 4 CHANNEL',83,54.5,1.4);text('I2C SENSOR INTERFACE',141,54.5,1.1)
for ch,x in enumerate([75,90,130,145],1):text('CH'+str(ch),x,59,1.2)
text('AIR / T+RH',110,53,0.8)
text('AFE 1 / 0x30',82,96.5,1);text('AFE 2 / 0x31',138,96.5,1)
text('SWD1',82.5,110,1);text('SWD2',137.5,110,1)
text('UART1',74.8,127,1);text('UART2',144.8,127,1)
text('5V  GND SDA SCL ALRT RST',110,128.2,.85)
text('REV B / 120 x 80 mm',145,119,0.8)
text('ES1: C=COUNTER  S=SENSE  R=REFERENCE',110,78,.75,p.B_SilkS)
text('JP1-JP4: OPEN FOR OPERATION',110,102,1,p.B_SilkS)
text('3.3V LOGIC / VIN 4.0-5.5V',110,126,1,p.B_SilkS)
text('ADuCM355 / REQUIRES FIRMWARE + CALIBRATION',110,122,1,p.B_SilkS)
# Mark connector pin 1 and test pads with concise labels.
for txt,x,y in [('VIN',101,116.5),('3V3',103,111),('3V3A',105,92.5),('GND',117,116.5),('AGND',110,85.5),('BOOT1',87,107),('BOOT2',143,107),('SDA',123,118.5),('SCL',127,118.5)]:text(txt,x,y,.75)
for cx in [82,138]:
 text('3V3 DIO CLK GND RST',cx+0.5,116,.65)
for cx in [74.8,144.8]:text('3V3 TX RX GND',cx,120,.65)
b.GetTitleBlock().SetTitle('EC Sense 4-channel I2C sensor interface');b.GetTitleBlock().SetRevision('B');b.GetTitleBlock().SetDate('2026-09-16')
b.BuildConnectivity();p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
print('Footprints',len(list(b.GetFootprints())),'nets',len(netobjs),'outline',p.ToMM(b.GetBoardEdgesBoundingBox().GetWidth()),p.ToMM(b.GetBoardEdgesBoundingBox().GetHeight()))
print('DSN export',p.ExportSpecctraDSN(b,'verification/layout.dsn'))
