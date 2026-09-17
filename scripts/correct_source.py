from pathlib import Path
p=Path('gen_sch.py');s=p.read_text()
s=s.replace('("A1",  "CE0"','("B1",  "CE0"').replace('("B1",  "RE0"','("A1",  "RE0"')
s=s.replace('name="VSS", number="2"','name="VSS", number="4"').replace('name="SCL", number="4"','name="SCL", number="2"')
s=s.replace('name="IO2", number="3"','name="IO2", number="2"').replace('name="GND", number="2")],\n           [rect(-5.08, 5.08','name="GND", number="3")],\n           [rect(-5.08, 5.08')
s=s.replace('stub("ESD_ARRAY", SX - 45, 195, "3"','stub("ESD_ARRAY", SX - 45, 195, "2"').replace('pin_xy("ESD_ARRAY", SX - 45, 195, "2")','pin_xy("ESD_ARRAY", SX - 45, 195, "3")')
s=s.replace('stub("SHT45", 330, 292, "4"','stub("SHT45", 330, 292, "2"').replace('pin_xy("SHT45", 330, 292, "2")','pin_xy("SHT45", 330, 292, "4")')
s=s.replace('name_to_num["GPIO0/PWM0"], "~{ALERT}"','name_to_num["GPIO1/PWM1"], "~{ALERT}"').replace('name_to_num["GPIO1/PWM1"])','name_to_num["GPIO0/PWM0"])')
s=s.replace('("AVDD_DD", "+3V3A")','("AVDD_DD", "+3V3")')
s=s.replace('value="100n", dnp=True','value="100n", dnp=False').replace('Optional VZERO decoupling - confirm against EVAL-ADUCM355 schematic','Required VZERO decoupling per ADuCM355 Rev C p26')
s=s.replace('dec = [("VREF182", "100n"), ("VREF25", "100n"), ("ADCVBIAS", "100n"),\n       ("AVDD_REG", "1u"), ("DVDD_REG", "1u"), ("DVDD_REG_AD", "1u"),\n       ("VDCDC_CAPOUT", "4u7")]','dec = [("VREF182", "4u7"), ("VREF25", "470n"), ("ADCVBIAS", "470n"),\n       ("AVDD_REG", "470n"), ("DVDD_REG", "470n"), ("DVDD_REG_AD", "470n"),\n       ("VDCDC_CAPOUT", "470n")]')
s=s.replace('place("C", SX + 52, cy, value="4u7")','place("C", SX + 52, cy, value="100n")').replace('place("C", SX + 69, cy, value="4u7")','place("C", SX + 69, cy, value="100n")')
# EEPROM NC pins, per Microchip DS22124.
for name,num in [('A0','1'),('A1','2'),('A2','3'),('WP','7')]:
 s=s.replace(f'name="{name}", number="{num}"',f'name="NC{num}", number="{num}"')
start=s.index('for n in ("1", "2", "3"):')
end=s.index('stub("24AA02E48"',start)
s=s[:start]+'''for n in ("1", "2", "3"):
    nc(*pin_xy("24AA02E48", 335, 360, n))
'''+s[end:]
start=s.index('px, py = pin_xy("24AA02E48", 335, 360, "7")')
end=s.index('px, py = pin_xy("24AA02E48", 335, 360, "8")',start)
s=s[:start]+'''nc(*pin_xy("24AA02E48", 335, 360, "7"))
'''+s[end:]
s=s.replace('VIN 3.3-5.5 V','VIN 4.0-5.5 V; nominal 5 V')
s=s.replace('VERIFY ADuCM355 PINOUT AGAINST OFFICIAL DATASHEET BEFORE LAYOUT','Rev B: datasheet pinout and decoupling corrections; see PCB_README.md')
s=s.replace('(rev "A")','(rev "B")').replace('2026-09-14','2026-09-16')
add='''# Added local supply bypass capacitors; one per supply pin on each AFE.
text("LOCAL SUPPLY BYPASS - PLACE AT EACH IC POWER PIN", 525, 368, 1.8)
for di, dev in enumerate(["U1", "U2"]):
    for i, (pinname, net, gnd) in enumerate([("AVDD", "+3V3A", "AGND"), ("AVDD_DD", "+3V3", "AGND"), ("DVDD", "+3V3", "GND"), ("DVDD_AD", "+3V3", "GND")]):
        cx=528+i*22;cy=384+di*22
        place("C", cx, cy, value="100n", fields={"Note":dev+" "+pinname+" local bypass"})
        p1=pin_xy("C",cx,cy,"1");wire(*p1,p1[0],p1[1]-2.54);rail(net,p1[0],p1[1]-2.54)
        p2=pin_xy("C",cx,cy,"2");wire(*p2,p2[0],p2[1]+2.54);rail(gnd,p2[0],p2[1]+2.54)
place("C", 375, 360, value="100n", fields={"Note":"U5 local bypass"})
p1=pin_xy("C",375,360,"1");wire(*p1,p1[0],p1[1]-2.54);rail("+3V3",p1[0],p1[1]-2.54)
p2=pin_xy("C",375,360,"2");wire(*p2,p2[0],p2[1]+2.54);rail("GND",p2[0],p2[1]+2.54)

'''
s=s.replace('# ---------------------------------------------------------------- file assembly',add+'# ---------------------------------------------------------------- file assembly')
p.write_text(s)
