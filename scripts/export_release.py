"""Export the checked, final KiCad files; does not recreate or reroute the PCB."""
import subprocess, shutil, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PCB='ECSense_4CH_I2C.kicad_pcb';SCH='ECSense_4CH_I2C.kicad_sch'
def run(name,*args):
    r=subprocess.run([CLI,*args],cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (ROOT/'verification'/f'export-{name}.log').write_text(r.stdout)
    if r.returncode:raise RuntimeError(name+': '+r.stdout)
    print(name,'OK',flush=True)
for path in ['manufacturing/gerbers','manufacturing/assembly','output/pdf','tmp/pdfs']:(ROOT/path).mkdir(parents=True,exist_ok=True)
run('gerbers','pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,F.Paste,B.Paste,Edge.Cuts','--output','manufacturing/gerbers/','--precision','6',PCB)
run('drills','pcb','export','drill','--output','manufacturing/gerbers/','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path','manufacturing/drill-report.txt',PCB)
run('bom','sch','export','bom','--fields','Reference,Value,Footprint,QUANTITY,DNP,MPN,Tol,Note','--labels','References,Value,Footprint,Quantity,DNP,Manufacturer_Part,Tolerance,Assembly_Note','--output','manufacturing/assembly/BOM.csv',SCH)
shutil.copy2(ROOT/'manufacturing/assembly/BOM.csv',ROOT/'ECSense_4CH_I2C-bom.csv')
run('positions','pcb','export','pos','--format','csv','--units','mm','--side','both','--exclude-dnp','--output','manufacturing/assembly/Positions-all.csv',PCB)
run('smd-positions','pcb','export','pos','--format','csv','--units','mm','--side','both','--smd-only','--exclude-dnp','--output','manufacturing/assembly/Positions-SMD.csv',PCB)
run('netlist','pcb','export','ipcd356','--output','manufacturing/ECSense_4CH_I2C.d356',PCB)
run('stats','pcb','export','stats','--format','json','--output','verification/board-statistics.json',PCB)
run('mechanical','pcb','export','pdf','--layers','Edge.Cuts,Dwgs.User','--black-and-white','--include-border-title','--mode-single','--output','tmp/pdfs/Mechanical.pdf',PCB)
run('front-assembly','pcb','export','pdf','--layers','F.Fab,F.SilkS,Edge.Cuts','--black-and-white','--include-border-title','--mode-single','--output','tmp/pdfs/Assembly-front.pdf',PCB)
run('back-assembly','pcb','export','pdf','--layers','B.Fab,B.SilkS,Edge.Cuts','--mirror','--black-and-white','--include-border-title','--mode-single','--output','tmp/pdfs/Assembly-back.pdf',PCB)
run('schematic','sch','export','pdf','--output','ECSense_4CH_I2C.pdf',SCH)
run('drc-report','pcb','drc','--schematic-parity','--all-track-errors','--exit-code-violations','--output','verification/final-drc.rpt',PCB)
run('erc-report','sch','erc','--exit-code-violations','--output','verification/final-erc.rpt',SCH)
print('Release exports complete',flush=True)
