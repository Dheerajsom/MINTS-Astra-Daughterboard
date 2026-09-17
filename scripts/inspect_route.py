import pcbnew as p,os,json
from pathlib import Path
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('verification/placed.kicad_pcb');b.SetFileName(str(Path('ECSense_4CH_I2C.kicad_pcb').resolve()));p.ImportSpecctraSES(b,'verification/retry.ses')
ds=b.GetDesignSettings();ds.m_TrackMinWidth=p.FromMM(.075);ds.m_HoleClearance=p.FromMM(.15);ds.m_MinSilkTextHeight=p.FromMM(.65)
p.SaveBoard('verification/retry-board.kicad_pcb',b)
p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
p.ExportSpecctraDSN(b,'verification/retry4.dsn')
