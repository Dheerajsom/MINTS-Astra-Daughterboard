import pcbnew as p,os
from pathlib import Path
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('verification/routed-before-finish.kicad_pcb');b.SetFileName(str(Path('ECSense_4CH_I2C.kicad_pcb').resolve()))
ds=b.GetDesignSettings();print([x for x in dir(ds) if 'Hole' in x]);ds.m_TrackMinWidth=p.FromMM(.075);ds.m_MinClearance=p.FromMM(.075)
nc=ds.m_NetSettings.GetDefaultNetclass();nc.SetTrackWidth(p.FromMM(.09));nc.SetClearance(p.FromMM(.075));nc.SetViaDiameter(p.FromMM(.4));nc.SetViaDrill(p.FromMM(.2))
p.ExportSpecctraDSN(b,'verification/retry.dsn')
