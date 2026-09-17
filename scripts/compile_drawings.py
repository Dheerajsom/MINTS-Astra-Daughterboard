from pathlib import Path
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader,PdfWriter
ROOT=Path(__file__).resolve().parent.parent
W,H=landscape(A4)
cover=ROOT/'tmp/pdfs/Cover.pdf';c=canvas.Canvas(str(cover),pagesize=(W,H))
c.setFillColor(HexColor('#173c39'));c.rect(0,H-108,W,108,fill=1,stroke=0)
c.setFillColor(HexColor('#ffffff'));c.setFont('Helvetica-Bold',24);c.drawString(38,H-49,'EC Sense - four-channel I2C PCB')
c.setFont('Helvetica',12);c.drawString(39,H-77,'Revision B | 120 x 80 mm | Fabrication and assembly | 16 September 2026')
style=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=HexColor('#233835'))
def paragraph(text,x,y,width):
 p=Paragraph(text,style);_,height=p.wrap(width,400);p.drawOn(c,x,y-height);return y-height
c.setFillColor(HexColor('#173c39'));c.setFont('Helvetica-Bold',14);c.drawString(38, H-141,'Fabrication specification')
rows=[('Board','120.00 x 80.00 mm, R3 corners'),('Construction','4 copper layers, 1.6 mm FR-4, ENIG'),('Track / space','0.075 / 0.075 mm minimum'),('Fine vias','0.20 mm finished drill / 0.40 mm pad'),('Stitching vias','0.30 mm finished drill / 0.60 mm pad'),('Mounting','4 x 3.2 mm NPTH; 110 x 70 mm pattern'),('Assembly','Components on both sides; tented vias')]
y=H-166
for label,value in rows:
 c.setStrokeColor(HexColor('#d5dfdd'));c.line(38,y-15,410,y-15)
 c.setFillColor(HexColor('#53615f'));c.setFont('Helvetica',9);c.drawString(38,y,label)
 c.setFillColor(HexColor('#203431'));c.setFont('Helvetica-Bold',9);c.drawString(138,y,value);y-=29
img=ROOT/'output/PCB-top.png'
if img.exists():c.drawImage(str(img),425,H-390,width=385,height=257,preserveAspectRatio=True,mask='auto')
c.setFont('Helvetica',8);c.setFillColor(HexColor('#586b67'));c.drawString(458,H-395,'Illustrative 3D view; land patterns govern assembly.')
y=paragraph('<b>Assembly:</b> Fit all capacitors and R11. Leave JP1-JP4 open. Each sensor socket uses three Mill-Max 0548-0-15-15-21-27-10-0 receptacles. Insert gas sensors after soldering and cleaning.',38,196,365)
paragraph('<b>Checks:</b> Zero DRC violations, unconnected items, schematic mismatches and ERC violations. This is an untested hardware prototype: firmware, gas-specific setup, zero/span calibration and bench validation remain required.',438,196,365)
paragraph('<b>Outputs:</b> Use the Gerbers and separate PTH/NPTH drills for fabrication. Absolute KiCad origin is shared across outputs. Bottom assembly is viewed from below; do not mirror Gerbers. See PCB_README.md for power, connectors and bring-up.',38,118,765)
c.setStrokeColor(HexColor('#d5dfdd'));c.line(38,44,W-38,44)
c.setFont('Helvetica',8);c.setFillColor(HexColor('#53615f'));c.drawString(38,29,'ECSense_4CH_I2C - revision B');c.drawRightString(W-38,29,'Hardware prototype / manufacturing notes');c.save()
writer=PdfWriter();writer.append(str(cover))
parts=[('Mechanical - dimensions in millimeters','tmp/pdfs/Mechanical.pdf'),('Assembly - front','tmp/pdfs/Assembly-front.pdf'),('Assembly - bottom, viewed from below','tmp/pdfs/Assembly-back.pdf'),('Plated drill map','manufacturing/gerbers/ECSense_4CH_I2C-PTH-drl_map.pdf'),('Nonplated drill map','manufacturing/gerbers/ECSense_4CH_I2C-NPTH-drl_map.pdf')]
for title,path in parts:
 reader=PdfReader(str(ROOT/path))
 for page in reader.pages:
  buf=BytesIO();hdr=canvas.Canvas(buf,pagesize=(float(page.mediabox.width),float(page.mediabox.height)))
  hdr.setFont('Helvetica-Bold',13);hdr.setFillColor(HexColor('#173c39'));hdr.drawString(38,float(page.mediabox.height)-44,title);hdr.save();buf.seek(0)
  page.merge_page(PdfReader(buf).pages[0]);writer.add_page(page)
writer.add_metadata({'/Title':'EC Sense revision B - fabrication and assembly','/Author':'EC Sense PCB project'})
out=ROOT/'output/pdf/Fabrication_and_assembly.pdf'
with out.open('wb') as f:writer.write(f)
assert len(PdfReader(str(out)).pages)==6
for _,path in parts[-2:]:
 src=ROOT/path;src.replace(ROOT/'tmp/pdfs'/src.name)
print('Created',out,'with 6 pages')
