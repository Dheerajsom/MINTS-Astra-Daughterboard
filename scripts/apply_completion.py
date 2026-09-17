import os,json,re,xml.etree.ElementTree as ET
from pathlib import Path
import pcbnew as p
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb');mm=p.FromMM
v=lambda q:p.VECTOR2I(mm(q[0]),mm(q[1]))
for r in json.load(open('verification/completion-routes.json')):
    net=b.FindNet(r['net'])
    for s in r['sections']:
        for a,z in zip(s['points'],s['points'][1:]):
            if a==z:continue
            t=p.PCB_TRACK(b);t.SetStart(v(a));t.SetEnd(v(z));t.SetLayer(s['layer']);t.SetWidth(mm(s['width']));t.SetNet(net);b.Add(t)
    for q in r['vias']:
        t=p.PCB_VIA(b);t.SetPosition(v(q));t.SetWidth(mm(.4));t.SetDrill(mm(.2));t.SetViaType(p.VIATYPE_THROUGH);t.SetLayerPair(p.F_Cu,p.B_Cu);t.SetNet(net);b.Add(t)
foots={f.GetReference():f for f in b.GetFootprints()}
for c in ET.parse('verification/current-final.xml').findall('.//components/comp'):
    f=foots[c.get('ref')]
    for field in c.findall('fields/field'):
        name=field.get('name')
        if name=='Footprint':continue
        f.SetField(name,field.text or '')
        f.GetField(name).SetVisible(False)
    f.SetExcludedFromBOM(c.find('property[@name="exclude_from_bom"]') is not None)
    f.SetDNP(c.find('property[@name="dnp"]') is not None)
for f in b.GetFootprints():
    for pad in f.Pads():
        n=pad.GetNetname()
        if n.startswith('unconnected-') and '/' in n:
            name=n.replace('/','{slash}');net=b.FindNet(name)
            if not net:net=p.NETINFO_ITEM(b,name);b.Add(net)
            pad.SetNet(net)
for t in b.GetDrawings():
    if isinstance(t,p.PCB_TEXT) and t.GetText()=='REV B / 120 x 80 mm':t.SetPosition(v((153,118)))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):t.SetFrontTentingMode(p.TENTING_MODE_TENTED);t.SetBackTentingMode(p.TENTING_MODE_TENTED)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
