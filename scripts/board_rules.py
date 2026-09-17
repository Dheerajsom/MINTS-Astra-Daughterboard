import pcbnew as p

def configure(b):
 d=b.GetDesignSettings();d.m_MinClearance=p.FromMM(.075);d.m_TrackMinWidth=p.FromMM(.075);d.m_ViasMinSize=p.FromMM(.4);d.m_MinThroughDrill=p.FromMM(.2);d.m_ViasMinAnnularWidth=p.FromMM(.1);d.m_HoleClearance=p.FromMM(.15);d.m_HoleToHoleMin=p.FromMM(.2);d.m_MinSilkTextHeight=p.FromMM(.65);d.m_MinSilkTextThickness=p.FromMM(.1)
 n=d.m_NetSettings.GetDefaultNetclass();n.SetClearance(p.FromMM(.075));n.SetTrackWidth(p.FromMM(.09));n.SetViaDiameter(p.FromMM(.4));n.SetViaDrill(p.FromMM(.2))
 for t in b.GetTracks():
  if not isinstance(t,p.PCB_VIA) and t.GetWidth()<p.FromMM(.075):t.SetWidth(p.FromMM(.075))

def save_rules():
 import json
 from pathlib import Path
 f=Path('ECSense_4CH_I2C.kicad_pro');j=json.loads(f.read_text());n=j['net_settings']['classes'][0];n.update(clearance=.075,track_width=.1,via_diameter=.4,via_drill=.2);j['net_settings']['classes']=[n];j['net_settings']['netclass_patterns']=[]
 r=j['board']['design_settings']['rules'];r.update(min_clearance=.075,min_track_width=.075,min_via_diameter=.4,min_through_hole_diameter=.2,min_via_annular_width=.1,min_hole_clearance=.15,min_hole_to_hole=.2,min_copper_edge_clearance=.3,min_silk_clearance=.1,min_text_height=.65,min_text_thickness=.1)
 j['board']['design_settings']['rule_severities'].update(courtyards_overlap='error',silk_over_copper='warning',silk_overlap='warning',missing_courtyard='warning')
 f.write_text(json.dumps(j,indent=2))
if __name__=='__main__':save_rules()
