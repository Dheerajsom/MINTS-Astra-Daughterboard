"""Untangle two local fanout crossings; preserve all remote routing."""
import os
from pathlib import Path
import pcbnew as p
os.chdir(Path(__file__).resolve().parent.parent)
b=p.LoadBoard('ECSense_4CH_I2C.kicad_pcb')
p.SaveBoard('verification/before-fanout-fix.kicad_pcb',b)
remove={
 '3c7f8535-5c16-4d76-9538-9729509e97a2','4483989e-c8b2-4828-87a0-b443b36fd4c2',
 '53caeccd-09bf-4dd1-84af-1a1cdac008ef','2bcc3e17-2c82-4436-ad74-9c28655d58f9',
 '4f065485-a44a-4cd8-8d8a-e6c336644632','77beb6c6-a84e-4a8d-956f-b0aae27e5134',
 'e02d327a-fa5e-46e1-9ccc-70c9690ce39c','e2cff86a-cdfd-4674-ad35-49e2e611a2c3',
 'c9fb41d0-d2b3-4576-85b6-fb116e6415d9',
 '6707af9c-7925-471d-a480-32f1b6785d60',
}
for t in list(b.GetTracks()):
 id=t.m_Uuid.AsString()
 if id in remove:b.Remove(t)
 elif id=='f4ecc370-80b1-4ccb-9a55-5ca6093bfae3':t.SetNet(b.FindNet('/U2_SWDIO'))
 elif id=='3fde5620-babb-45a9-8eb6-5551154e727c':t.SetNet(b.FindNet('/SDA'))
b.BuildConnectivity();p.SaveBoard('ECSense_4CH_I2C.kicad_pcb',b)
