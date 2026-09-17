import pcbnew as p,os
from pathlib import Path
from board_rules import configure
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb');configure(b);p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b);p.ExportSpecctraDSN(b,'verification/retry4.dsn')
