#!/usr/bin/env python3
"""
Generate a KiCad 9 schematic for a 4-channel EC Sense ES1 electrochemical
gas-sensor front end with a single I2C output bus.

Topology: 2 x ADuCM355 (dual potentiostat each) -> 4 sensor channels.
Both ADuCM355 act as I2C targets on one shared bus (addresses strapped on P2.4).

Connections are made by NET LABELS (no long wires) so the sheet stays readable.
"""
import uuid as _uuid

def U():
    return str(_uuid.uuid4())

PAPER = "A1"          # 841 x 594 mm
LIB = "ECGAS"

# ---------------------------------------------------------------- primitives
def esc(s):
    # KiCad's s-expression parser rejects raw newlines inside quoted strings
    return (s.replace('\\', '\\\\')
             .replace('"', '\\"')
             .replace('\r\n', '\\n')
             .replace('\n', '\\n'))

def prop(name, value, x, y, rot=0, hide=False, size=1.27, justify=None):
    e = f'(font (size {size} {size}))'
    if justify:
        e = f'(font (size {size} {size})) (justify {justify})'
    h = " hide" if hide else ""
    return (f'(property "{esc(name)}" "{esc(value)}" (at {x} {y} {rot}) '
            f'(effects {e}{h}))')

def pin(etype, shape, x, y, rot, length, name, number, nsize=1.0, numsize=1.0):
    return (f'(pin {etype} {shape} (at {x} {y} {rot}) (length {length})\n'
            f'  (name "{esc(name)}" (effects (font (size {nsize} {nsize}))))\n'
            f'  (number "{esc(number)}" (effects (font (size {numsize} {numsize}))))\n'
            f')')

def rect(x1, y1, x2, y2, fill="background"):
    return (f'(rectangle (start {x1} {y1}) (end {x2} {y2}) '
            f'(stroke (width 0.254) (type default)) (fill (type {fill})))')

# ---------------------------------------------------------------- symbol defs
SYMBOLS = {}

def add_symbol(name, ref, value, pins, body, extra_props=None, ref_at=(0,0),
               val_at=(0,-2.54), power=False, hide_pin_names=False,
               pin_name_offset=1.016):
    """pins: list of dicts with etype, shape, x, y, rot, length, name, number"""
    SYMBOLS[name] = dict(ref=ref, value=value, pins=pins, body=body,
                         extra=extra_props or {}, ref_at=ref_at, val_at=val_at,
                         power=power, hide_names=hide_pin_names,
                         offset=pin_name_offset)

def sym_text(name):
    s = SYMBOLS[name]
    out = [f'(symbol "{LIB}:{name}"']
    out.append(f'  (pin_names (offset {s["offset"]})' + (' hide' if s["hide_names"] else '') + ')')
    out.append('  (in_bom yes) (on_board yes)')
    if s["power"]:
        out.append('  (power)')
    out.append('  ' + prop("Reference", s["ref"], s["ref_at"][0], s["ref_at"][1],
                           hide=s["power"], justify="left"))
    out.append('  ' + prop("Value", s["value"], s["val_at"][0], s["val_at"][1], justify="left"))
    out.append('  ' + prop("Footprint", s["extra"].get("Footprint", ""), 0, 0, hide=True))
    out.append('  ' + prop("Datasheet", s["extra"].get("Datasheet", ""), 0, 0, hide=True))
    out.append('  ' + prop("Description", s["extra"].get("Description", ""), 0, 0, hide=True))
    for k, v in s["extra"].items():
        if k in ("Footprint", "Datasheet", "Description"):
            continue
        out.append('  ' + prop(k, v, 0, 0, hide=True))
    out.append(f'  (symbol "{name}_0_1"')
    for b in s["body"]:
        out.append('    ' + b)
    out.append('  )')
    out.append(f'  (symbol "{name}_1_1"')
    for p in s["pins"]:
        out.append('    ' + pin(**p).replace('\n', '\n    '))
    out.append('  )')
    out.append(')')
    return '\n'.join(out)

# ------------------------------------------------- ADuCM355 (72-lead LGA)
# NOTE: pinout reconstructed from the ADuCM355 Rev. C datasheet pin table.
# VERIFY every pin against the official PDF before layout.
ADUC_LEFT = [
    # (number, name, etype)
    ("B1",  "CE0",              "passive"),
    ("A1",  "RE0",              "passive"),
    ("A3",  "SE0",              "passive"),
    ("A2",  "DE0",              "passive"),
    ("C1",  "CAP_POT0",         "passive"),
    ("D1",  "RC0_0",            "passive"),
    ("D2",  "RC0_1",            "passive"),
    ("A4",  "AIN4_LPF0",        "passive"),
    ("C2",  "VBIAS0",           "output"),
    ("B2",  "VZERO0",           "output"),
    ("A7",  "RCAL0",            "passive"),
    ("",    "",                 "spacer"),
    ("B11", "CE1",              "passive"),
    ("A11", "RE1",              "passive"),
    ("A9",  "SE1",              "passive"),
    ("A10", "DE1",              "passive"),
    ("C11", "CAP_POT1",         "passive"),
    ("D11", "RC1_0",            "passive"),
    ("D10", "RC1_1",            "passive"),
    ("A8",  "AIN7_LPF1",        "passive"),
    ("C10", "VBIAS1",           "output"),
    ("B10", "VZERO1",           "output"),
    ("A6",  "RCAL1",            "passive"),
    ("",    "",                 "spacer"),
    ("B9",  "AIN0",             "input"),
    ("B8",  "AIN1",             "input"),
    ("B6",  "AIN2",             "input"),
    ("B7",  "AIN3/BUF_VREF1V8", "input"),
    ("B4",  "AIN5",             "input"),
    ("B3",  "AIN6",             "input"),
    ("",    "",                 "spacer"),
    ("A5",  "VREF_1.82V",       "passive"),
    ("E2",  "VREF_2.5V",        "passive"),
    ("E11", "ADCVBIAS_CAP",     "passive"),
    ("B5",  "AGND_REF",         "passive"),
    ("H1",  "XTALI",            "input"),
    ("J1",  "XTALO",            "output"),
    ("E5",  "DNC_E5",           "no_connect"),
    ("E10", "DNC_E10",          "no_connect"),
]
ADUC_RIGHT = [
    ("J5",  "P0.4/I2C_SCL",     "bidirectional"),
    ("H5",  "P0.5/I2C_SDA",     "bidirectional"),
    ("J3",  "P0.10/UART_SOUT",  "output"),
    ("J2",  "P0.11/UART_SIN",   "input"),
    ("",    "",                 "spacer"),
    ("H9",  "P0.0/SPI0_CLK",    "bidirectional"),
    ("H8",  "P0.1/SPI0_MOSI",   "bidirectional"),
    ("H7",  "P0.2/SPI0_MISO",   "bidirectional"),
    ("H6",  "P0.3/SPI0_CS",     "bidirectional"),
    ("F5",  "P1.0/SYS_WAKE",    "bidirectional"),
    ("D5",  "BM/P1.1",          "input"),
    ("E7",  "P1.2/SPI1_CLK",    "bidirectional"),
    ("D7",  "P1.3/SPI1_MOSI",   "bidirectional"),
    ("F6",  "P1.4/SPI1_MISO",   "bidirectional"),
    ("D6",  "P1.5/SPI1_CS",     "bidirectional"),
    ("J4",  "P2.4",             "bidirectional"),
    ("G10", "GPIO0/PWM0",       "bidirectional"),
    ("H10", "GPIO1/PWM1",       "bidirectional"),
    ("",    "",                 "spacer"),
    ("H3",  "SWCLK",            "input"),
    ("H4",  "SWDIO",            "bidirectional"),
    ("J10", "~{RESET}",         "input"),
    ("",    "",                 "spacer"),
    ("F11", "AVDD",             "power_in"),
    ("G2",  "AVDD_DD",          "power_in"),
    ("J6",  "DVDD",             "power_in"),
    ("F1",  "DVDD_AD",          "power_in"),
    ("E1",  "AVDD_REG",         "passive"),
    ("J7",  "DVDD_REG",         "passive"),
    ("G1",  "DVDD_REG_AD",      "passive"),
    ("J9",  "VDCDC_CAP1P",      "passive"),
    ("J8",  "VDCDC_CAP1N",      "passive"),
    ("G11", "VDCDC_CAP2P",      "passive"),
    ("H11", "VDCDC_CAP2N",      "passive"),
    ("J11", "VDCDC_CAPOUT",     "passive"),
    ("",    "",                 "spacer"),
    ("F10", "AGND",             "power_in"),
    ("H2",  "AGND_DD",          "power_in"),
    ("F7",  "DGND",             "power_in"),
    ("F2",  "DGND_AD",          "power_in"),
]

PITCH = 2.54
HW = 30.48          # half width of ADuCM355 body


def build_aducm355():
    nl = len(ADUC_LEFT)
    nr = len(ADUC_RIGHT)
    n = max(nl, nr)
    half = (n - 1) * PITCH / 2.0
    half = round(half / 1.27) * 1.27
    top = half + PITCH
    bot = -half - PITCH
    pins = []
    aduc_pinmap = {}
    for i, (num, name, et) in enumerate(ADUC_LEFT):
        if et == "spacer":
            continue
        y = half - i * PITCH
        pins.append(dict(etype=et, shape="line", x=-(HW + 5.08), y=y, rot=0,
                         length=5.08, name=name, number=num))
        aduc_pinmap[num] = (-(HW + 5.08), y, "L")
    for i, (num, name, et) in enumerate(ADUC_RIGHT):
        if et == "spacer":
            continue
        y = half - i * PITCH
        pins.append(dict(etype=et, shape="line", x=(HW + 5.08), y=y, rot=180,
                         length=5.08, name=name, number=num))
        aduc_pinmap[num] = ((HW + 5.08), y, "R")
    body = [rect(-HW, top, HW, bot)]
    add_symbol("ADuCM355", "U", "ADuCM355", pins, body,
               extra_props={"Footprint": "ECGAS:ADuCM355_LGA-72_6x5mm",
                            "Datasheet": "https://www.analog.com/media/en/technical-documentation/data-sheets/aducm355.pdf",
                            "Description": "Dual potentiostat + 16-bit ADC + Cortex-M3, electrochemical AFE",
                            "MPN": "ADUCM355BCCZ"},
               ref_at=(-HW, top + 2.54), val_at=(-HW, top + 5.08))
    return aduc_pinmap, top, bot

ADUC_PINS, ADUC_TOP, ADUC_BOT = build_aducm355()

# ------------------------------------------------- generic small symbols
def two_pin(name, ref, value, body, vertical=True, etype="passive",
            p1="1", p2="2", fp=""):
    if vertical:
        pins = [dict(etype=etype, shape="line", x=0, y=3.81, rot=270, length=1.27,
                     name="~", number=p1),
                dict(etype=etype, shape="line", x=0, y=-3.81, rot=90, length=1.27,
                     name="~", number=p2)]
    else:
        pins = [dict(etype=etype, shape="line", x=-3.81, y=0, rot=0, length=1.27,
                     name="~", number=p1),
                dict(etype=etype, shape="line", x=3.81, y=0, rot=180, length=1.27,
                     name="~", number=p2)]
    add_symbol(name, ref, value, pins, body, extra_props={"Footprint": fp},
               ref_at=(2.54, 1.27), val_at=(2.54, -1.27), hide_pin_names=True)

two_pin("R", "R", "R", [rect(-1.016, 2.54, 1.016, -2.54, fill="none")],
        vertical=True, fp="Resistor_SMD:R_0603_1608Metric")
two_pin("C", "C", "C",
        ['(polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))',
         '(polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))'],
        vertical=True, fp="Capacitor_SMD:C_0603_1608Metric")
two_pin("L_Ferrite", "FB", "Ferrite",
        [rect(-1.016, 2.54, 1.016, -2.54, fill="none")],
        vertical=True, fp="Inductor_SMD:L_0805_2012Metric")

# power symbols
def power_sym(name, label, up=True):
    y = 0
    pins = [dict(etype="power_in", shape="line", x=0, y=0, rot=(90 if up else 270),
                 length=0, name=label, number="1")]
    if up:
        body = ['(polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))',
                '(polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))']
    else:
        body = ['(polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))',
                '(polyline (pts (xy -0.762 -1.905) (xy 0.762 -1.905)) (stroke (width 0.254) (type default)) (fill (type none)))',
                '(polyline (pts (xy -0.254 -2.54) (xy 0.254 -2.54)) (stroke (width 0.254) (type default)) (fill (type none)))',
                '(polyline (pts (xy 0 0) (xy 0 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))']
    add_symbol(name, "#PWR", label, pins, body, power=True, hide_pin_names=True,
               ref_at=(0, -3.81), val_at=(0, 3.81 if up else -5.08))

power_sym("+3V3", "+3V3", True)
power_sym("+3V3A", "+3V3A", True)
power_sym("VIN", "VIN", True)
power_sym("GND", "GND", False)
power_sym("AGND", "AGND", False)

add_symbol("PWR_FLAG", "#FLG", "PWR_FLAG",
           [dict(etype="power_out", shape="line", x=0, y=0, rot=90, length=0,
                 name="pwr", number="1")],
           ['(polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) '
            '(xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0.254) (type default)) '
            '(fill (type none)))'],
           power=True, hide_pin_names=True, ref_at=(0, -1.27), val_at=(0, 3.81))

# EC Sense ES1 3-pin sensor socket
add_symbol("EC_SENSOR_ES1", "J", "ES1 socket",
           [dict(etype="passive", shape="line", x=7.62, y=2.54, rot=180, length=2.54,
                 name="C", number="1"),
            dict(etype="passive", shape="line", x=7.62, y=0, rot=180, length=2.54,
                 name="S", number="2"),
            dict(etype="passive", shape="line", x=7.62, y=-2.54, rot=180, length=2.54,
                 name="R", number="3")],
           [rect(-5.08, 5.08, 5.08, -5.08),
            '(circle (center 0 0) (radius 2.54) (stroke (width 0.254) (type default)) (fill (type none)))'],
           extra_props={"Footprint": "ECGAS:EC_Sense_ES1_3pin_2.54mm",
                        "Description": "3-pin socket for EC Sense ES1 bare electrochemical sensor (C/S/R)"},
           ref_at=(-5.08, 6.35), val_at=(-5.08, 8.89))

# ADP151 LDO (TSOT-23-5)
add_symbol("ADP151", "U", "ADP151AUJZ-3.3",
           [dict(etype="power_in", shape="line", x=-10.16, y=2.54, rot=0, length=2.54, name="VIN", number="1"),
            dict(etype="input",    shape="line", x=-10.16, y=-2.54, rot=0, length=2.54, name="EN", number="3"),
            dict(etype="power_out",shape="line", x=10.16, y=2.54, rot=180, length=2.54, name="VOUT", number="5"),
            dict(etype="passive",  shape="line", x=10.16, y=-2.54, rot=180, length=2.54, name="NC", number="4"),
            dict(etype="power_in", shape="line", x=0, y=-10.16, rot=90, length=2.54, name="GND", number="2")],
           [rect(-7.62, 6.35, 7.62, -7.62)],
           extra_props={"Footprint": "Package_TO_SOT_SMD:TSOT-23-5",
                        "Description": "3.3V 200mA ultra-low-noise LDO"},
           ref_at=(-7.62, 7.62), val_at=(-7.62, 10.16))

# SHT45 (DFN-4)
add_symbol("SHT45", "U", "SHT45-AD1B",
           [dict(etype="bidirectional", shape="line", x=-10.16, y=2.54, rot=0, length=2.54, name="SDA", number="1"),
            dict(etype="power_in",      shape="line", x=0, y=-10.16, rot=90, length=2.54, name="VSS", number="4"),
            dict(etype="power_in",      shape="line", x=0, y=10.16, rot=270, length=2.54, name="VDD", number="3"),
            dict(etype="input",         shape="line", x=-10.16, y=-2.54, rot=0, length=2.54, name="SCL", number="2")],
           [rect(-7.62, 7.62, 7.62, -7.62)],
           extra_props={"Footprint": "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
                        "Description": "I2C temperature + RH sensor, addr 0x44"},
           ref_at=(-7.62, 9.0), val_at=(-7.62, 11.5))

# 24AA02E48 EEPROM (SOIC-8)
add_symbol("24AA02E48", "U", "24AA02E48T-I/SN",
           [dict(etype="input",   shape="line", x=-12.7, y=5.08, rot=0, length=2.54, name="NC1", number="1"),
            dict(etype="input",   shape="line", x=-12.7, y=2.54, rot=0, length=2.54, name="NC2", number="2"),
            dict(etype="input",   shape="line", x=-12.7, y=0, rot=0, length=2.54, name="NC3", number="3"),
            dict(etype="power_in",shape="line", x=0, y=-12.7, rot=90, length=2.54, name="VSS", number="4"),
            dict(etype="bidirectional", shape="line", x=12.7, y=0, rot=180, length=2.54, name="SDA", number="5"),
            dict(etype="input",   shape="line", x=12.7, y=2.54, rot=180, length=2.54, name="SCL", number="6"),
            dict(etype="input",   shape="line", x=12.7, y=5.08, rot=180, length=2.54, name="NC7", number="7"),
            dict(etype="power_in",shape="line", x=0, y=12.7, rot=270, length=2.54, name="VCC", number="8")],
           [rect(-10.16, 10.16, 10.16, -10.16)],
           extra_props={"Footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                        "Description": "2 kbit I2C EEPROM with EUI-48 node ID, addr 0x50"},
           ref_at=(-10.16, 11.5), val_at=(-10.16, 14.0))

# Host connector 6 pin
def conn(name, ref, value, npins, fp, labels):
    pins = []
    h = (npins - 1) * PITCH / 2
    body = [rect(-2.54, h + 2.54, 2.54, -h - 2.54)]
    for i in range(npins):
        y = h - i * PITCH
        pins.append(dict(etype="passive", shape="line", x=-7.62, y=y, rot=0,
                         length=5.08, name=labels[i], number=str(i + 1)))
    add_symbol(name, ref, value, pins, body, extra_props={"Footprint": fp},
               ref_at=(-2.54, h + 3.81), val_at=(-2.54, h + 6.35))

conn("CONN_HOST", "J", "Host I2C", 6, "Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical",
     ["VIN", "GND", "SDA", "SCL", "~{ALERT}", "~{RESET}"])
conn("CONN_SWD", "J", "SWD", 5, "Connector_PinHeader_1.27mm:PinHeader_1x05_P1.27mm_Vertical",
     ["VTREF", "SWDIO", "SWCLK", "GND", "~{RESET}"])
conn("CONN_UART", "J", "UART/BSL", 4, "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
     ["3V3", "RX", "TX", "GND"])

# jumper / solder bridge
add_symbol("JUMPER", "JP", "Solder jumper",
           [dict(etype="passive", shape="line", x=-5.08, y=0, rot=0, length=2.54, name="A", number="1"),
            dict(etype="passive", shape="line", x=5.08, y=0, rot=180, length=2.54, name="B", number="2")],
           [rect(-2.54, 1.905, 2.54, -1.905)],
           extra_props={"Footprint": "Jumper:SolderJumper-2_P1.3mm_Open_Pad1.0x1.5mm"},
           ref_at=(-2.54, 2.8), val_at=(-2.54, -5.0), hide_pin_names=True)

# TVS / ESD array
add_symbol("ESD_ARRAY", "D", "PESD3V3L2BT",
           [dict(etype="passive", shape="line", x=-7.62, y=2.54, rot=0, length=2.54, name="IO1", number="1"),
            dict(etype="passive", shape="line", x=-7.62, y=-2.54, rot=0, length=2.54, name="IO2", number="2"),
            dict(etype="passive", shape="line", x=0, y=-10.16, rot=90, length=2.54, name="GND", number="3")],
           [rect(-5.08, 5.08, 5.08, -7.62)],
           extra_props={"Footprint": "Package_TO_SOT_SMD:SOT-23"},
           ref_at=(-5.08, 6.35), val_at=(-5.08, 8.89))

# ---------------------------------------------------------------- sheet items
ITEMS = []          # rendered s-expressions
INSTANCES = []      # for sheet instance paths
ROOT_UUID = U()
PROJECT = "ECSense_4CH_I2C"


GRID = 1.27
def sn(v):
    return round(round(float(v) / GRID) * GRID, 4)

REFCOUNT = {}
def next_ref(prefix):
    REFCOUNT[prefix] = REFCOUNT.get(prefix, 0) + 1
    return f"{prefix}{REFCOUNT[prefix]}"

def place(symname, x, y, ref=None, value=None, rot=0, mirror=None, fields=None,
          dnp=False):
    x, y = sn(x), sn(y)
    s = SYMBOLS[symname]
    ref = ref or next_ref(s["ref"])
    value = value if value is not None else s["value"]
    u = U()
    m = f" (mirror {mirror})" if mirror else ""
    lines = [f'(symbol (lib_id "{LIB}:{symname}") (at {x} {y} {rot}){m}',
             f'  (unit 1) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"})',
             f'  (uuid {u})']
    rx, ry = s["ref_at"]; vx, vy = s["val_at"]
    hide_ref = s["power"]
    lines.append('  ' + prop("Reference", ref, x + rx, y - ry, hide=hide_ref, justify="left"))
    lines.append('  ' + prop("Value", value, x + vx, y - vy, justify="left"))
    lines.append('  ' + prop("Footprint", s["extra"].get("Footprint", ""), x, y, hide=True))
    lines.append('  ' + prop("Datasheet", s["extra"].get("Datasheet", ""), x, y, hide=True))
    lines.append('  ' + prop("Description", s["extra"].get("Description", ""), x, y, hide=True))
    for k, v in (fields or {}).items():
        lines.append('  ' + prop(k, v, x, y, hide=True))
    for p in s["pins"]:
        lines.append(f'  (pin "{esc(p["number"])}" (uuid {U()}))')
    lines.append(f'  (instances (project "{PROJECT}" (path "/{ROOT_UUID}" '
                 f'(reference "{ref}") (unit 1))))')
    lines.append(')')
    ITEMS.append('\n'.join(lines))
    return ref

def pin_xy(symname, x, y, number, rot=0, mirror=None):
    """schematic coords of a pin connection point for a placed symbol"""
    x, y = sn(x), sn(y)
    for p in SYMBOLS[symname]["pins"]:
        if p["number"] == number:
            px, py = p["x"], p["y"]
            if mirror == "y":
                px = -px
            if mirror == "x":
                py = -py
            if rot == 90:
                px, py = -py, px
            elif rot == 180:
                px, py = -px, -py
            elif rot == 270:
                px, py = py, -px
            return (round(x + px, 4), round(y - py, 4))
    raise KeyError(number)

def wire(x1, y1, x2, y2):
    x1, y1, x2, y2 = sn(x1), sn(y1), sn(x2), sn(y2)
    ITEMS.append(f'(wire (pts (xy {x1} {y1}) (xy {x2} {y2})) '
                 f'(stroke (width 0) (type default)) (uuid {U()}))')

def label(name, x, y, rot=0, justify="left bottom"):
    x, y = sn(x), sn(y)
    ITEMS.append(f'(label "{esc(name)}" (at {x} {y} {rot}) (fields_autoplaced)\n'
                 f'  (effects (font (size 1.27 1.27)) (justify {justify})) (uuid {U()}))')

def glabel(name, x, y, rot=0, shape="bidirectional"):
    ITEMS.append(f'(global_label "{esc(name)}" (shape {shape}) (at {x} {y} {rot}) '
                 f'(fields_autoplaced)\n  (effects (font (size 1.27 1.27)) '
                 f'(justify left)) (uuid {U()}))')

def nc(x, y):
    x, y = sn(x), sn(y)
    ITEMS.append(f'(no_connect (at {x} {y}) (uuid {U()}))')

def text(txt, x, y, size=1.6):
    ITEMS.append(f'(text "{esc(txt)}" (at {x} {y} 0) '
                 f'(effects (font (size {size} {size})) (justify left)) (uuid {U()}))')

def textbox(txt, x, y, w, h, size=1.5):
    ITEMS.append(f'(text_box "{esc(txt)}" (at {x} {y} 0) (size {w} {h})\n'
                 f'  (stroke (width 0.2) (type solid)) (fill (type none))\n'
                 f'  (effects (font (size {size} {size})) (justify left top)) (uuid {U()}))')

# helper: stub a pin out to a net label
def stub(sym, sx, sy, number, net, dirn="L", length=5.08, rot=0, mirror=None):
    px, py = pin_xy(sym, sx, sy, number, rot, mirror)
    if dirn == "L":
        ex, ey = px - length, py
        wire(px, py, ex, ey)
        label(net, ex, ey, 180, "right bottom")
    elif dirn == "R":
        ex, ey = px + length, py
        wire(px, py, ex, ey)
        label(net, ex, ey, 0, "left bottom")
    elif dirn == "U":
        ex, ey = px, py - length
        wire(px, py, ex, ey)
        label(net, ex, ey, 90, "left bottom")
    else:
        ex, ey = px, py + length
        wire(px, py, ex, ey)
        label(net, ex, ey, 270, "left bottom")
    return ex, ey

def rail(symname, x, y, rot=0):
    place(symname, x, y, rot=rot)

# =================================================================== SHEET
text("4-CHANNEL EC SENSE ES1 ELECTROCHEMICAL GAS SENSOR FRONT END  -  SINGLE I2C BUS OUTPUT", 20, 14, 3.0)
text("2 x ADuCM355 dual potentiostat, each an I2C target (U1=0x30, U2=0x31). Programmable bias per channel.", 20, 20, 2.0)

textbox("!! VERIFY BEFORE LAYOUT !!\n"
        "1. ADuCM355 pin numbers here were transcribed from the Rev. C datasheet pin table.\n"
        "   Check EVERY pin against the official PDF and the EVAL-ADUCM355QSPZ reference design.\n"
        "2. VDCDC_CAPx and the AVDD_REG / DVDD_REG / DVDD_REG_AD decoupling values must be taken\n"
        "   from the datasheet Applications Information section - placeholders are used here.\n"
        "3. EC Sense ES1 pin order is C-S-R (counter / sense=working / reference), 2.54 mm pitch,\n"
        "   0.4 mm pin diameter. Confirm against the mechanical drawing of YOUR part number.\n"
        "4. Sensitivity is strongly temperature dependent (approx. 4 nA/ppm at -40 C to 51 nA/ppm\n"
        "   at +50 C for AG1). Temperature compensation in firmware is mandatory, not optional.",
        20, 26, 250, 34, 1.6)

# ---------------------------------------------------------------- channels
CH_X = 55
CH_Y0 = 78
CH_DY = 62

chan_map = [  # (channel, device, potentiostat index)
    (1, "U1", 0), (2, "U1", 1), (3, "U2", 0), (4, "U2", 1),
]

for idx, (ch, dev, pot) in enumerate(chan_map):
    y = CH_Y0 + idx * CH_DY
    text(f"CHANNEL {ch}   ({dev} potentiostat {pot})", CH_X - 25, y - 16, 2.0)
    jref = place("EC_SENSOR_ES1", CH_X, y, ref=f"J{ch}",
                 value=f"ES1 CH{ch}",
                 fields={"MPN": "3x Mill-Max 0350 series receptacle (0.30-0.51 mm pin)",
                         "Note": "EC Sense ES1 bare sensor, C/S/R, 2.54 mm pitch"})
    # nets
    n_ce, n_se, n_re = f"CH{ch}_CE", f"CH{ch}_SE", f"CH{ch}_RE"
    stub("EC_SENSOR_ES1", CH_X, y, "1", n_ce, "R", 10.16)
    stub("EC_SENSOR_ES1", CH_X, y, "2", n_se, "R", 10.16)
    stub("EC_SENSOR_ES1", CH_X, y, "3", n_re, "R", 10.16)

    # 22pF EMC caps to AGND on each electrode
    for k, (net, dx) in enumerate([(n_ce, 0), (n_se, 12.7), (n_re, 25.4)]):
        cx = CH_X + 30.48 + dx
        cy = y + 12.7
        place("C", cx, cy, value="22p", fields={"Tol": "C0G 5%",
                                                "Note": "EMC filter, keep at socket"})
        px, py = pin_xy("C", cx, cy, "1")
        wire(px, py, px, py - 2.54)
        label(net, px, py - 2.54, 90, "left bottom")
        gx, gy = pin_xy("C", cx, cy, "2")
        wire(gx, gy, gx, gy + 2.54)
        rail("AGND", gx, gy + 2.54)

    # DNP storage-short jumper across SE / RE
    jx = CH_X + 30.48
    jy = y - 12.7
    place("JUMPER", jx, jy, value="SE-RE short", dnp=True,
          fields={"Note": "Fit only for storage/transport. Remove before measurement."})
    ax, ay = pin_xy("JUMPER", jx, jy, "1")
    wire(ax, ay, ax - 5.08, ay); label(n_se, ax - 5.08, ay, 180, "right bottom")
    bx, by = pin_xy("JUMPER", jx, jy, "2")
    wire(bx, by, bx + 5.08, by); label(n_re, bx + 5.08, by, 0, "left bottom")

    # potentiostat loop passives
    base = CH_X + 92
    # C_CE : CE <-> CAP_POT
    place("C", base, y - 12.7, value="100n",
          fields={"Note": "Potentiostat loop compensation, CE to CAP_POT"})
    p1 = pin_xy("C", base, y - 12.7, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(n_ce, p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", base, y - 12.7, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(f"CH{ch}_CAPPOT", p2[0], p2[1] + 5.08, 270, "left bottom")

    # C_RC : RC_0 <-> RC_1
    place("C", base + 17.78, y - 12.7, value="100n",
          fields={"Note": "LPTIA RC filter between RCx_0 and RCx_1"})
    p1 = pin_xy("C", base + 17.78, y - 12.7, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"CH{ch}_RC0", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", base + 17.78, y - 12.7, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(f"CH{ch}_RC1", p2[0], p2[1] + 5.08, 270, "left bottom")

    # C_LPF : AIN_LPF to AGND
    place("C", base, y + 12.7, value="4u7",
          fields={"Note": "LPTIA output low-pass, X7R 10V"})
    p1 = pin_xy("C", base, y + 12.7, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"CH{ch}_LPF", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", base, y + 12.7, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("AGND", p2[0], p2[1] + 2.54)

    # C_VZERO (optional - fit per ADI reference design)
    place("C", base + 35.56, y + 12.7, value="100n", dnp=False,
          fields={"Note": "Required VZERO decoupling per ADuCM355 Rev C p26"})
    p1 = pin_xy("C", base + 35.56, y + 12.7, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"CH{ch}_VZERO", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", base + 35.56, y + 12.7, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("AGND", p2[0], p2[1] + 2.54)

    # C_VBIAS
    place("C", base + 17.78, y + 12.7, value="100n",
          fields={"Note": "VBIAS decoupling"})
    p1 = pin_xy("C", base + 17.78, y + 12.7, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"CH{ch}_VBIAS", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", base + 17.78, y + 12.7, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("AGND", p2[0], p2[1] + 2.54)

# ---------------------------------------------------------------- ADuCM355 x2
DEV_X = {"U1": 297.18, "U2": 431.80}
DEV_Y = 189.23

pot_net = {("U1", 0): 1, ("U1", 1): 2, ("U2", 0): 3, ("U2", 1): 4}

analog_map = {
    0: {"CE0": "CE", "RE0": "RE", "SE0": "SE", "CAP_POT0": "CAPPOT",
        "RC0_0": "RC0", "RC0_1": "RC1", "AIN4_LPF0": "LPF",
        "VBIAS0": "VBIAS", "VZERO0": "VZERO"},
    1: {"CE1": "CE", "RE1": "RE", "SE1": "SE", "CAP_POT1": "CAPPOT",
        "RC1_0": "RC0", "RC1_1": "RC1", "AIN7_LPF1": "LPF",
        "VBIAS1": "VBIAS", "VZERO1": "VZERO"},
}
name_to_num = {}
for num, nm, et in ADUC_LEFT + ADUC_RIGHT:
    if et != "spacer":
        name_to_num[nm] = num

for dev, dx in DEV_X.items():
    addr = "0x30" if dev == "U1" else "0x31"
    place("ADuCM355", dx, DEV_Y, ref=dev,
          value="ADuCM355",
          fields={"MPN": "ADUCM355BCCZ", "I2C_ADDR": addr})
    text(f"{dev}  I2C target {addr}", dx - 30.48, DEV_Y + ADUC_TOP + 14, 2.0)

    for pot in (0, 1):
        ch = pot_net[(dev, pot)]
        for pinname, suffix in analog_map[pot].items():
            num = name_to_num[pinname]
            if suffix == "VZERO":
                netname = f"CH{ch}_VZERO"
            else:
                netname = f"CH{ch}_{suffix}"
            stub("ADuCM355", dx, DEV_Y, num, netname, "L", 7.62)

    # RCAL resistor between RCAL0 and RCAL1
    stub("ADuCM355", dx, DEV_Y, name_to_num["RCAL0"], f"{dev}_RCAL0", "L", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["RCAL1"], f"{dev}_RCAL1", "L", 7.62)

    # analog references
    for pname, net in [("VREF_1.82V", f"{dev}_VREF182"),
                       ("VREF_2.5V", f"{dev}_VREF25"),
                       ("ADCVBIAS_CAP", f"{dev}_ADCVBIAS")]:
        stub("ADuCM355", dx, DEV_Y, name_to_num[pname], net, "L", 7.62)

    # AGND_REF -> AGND
    px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num["AGND_REF"])
    wire(px, py, px - 7.62, py); wire(px - 7.62, py, px - 7.62, py + 5.08)
    rail("AGND", px - 7.62, py + 5.08)

    # unused analog inputs / DNC / XTAL
    for pname in ["AIN0", "AIN1", "AIN2", "AIN3/BUF_VREF1V8", "AIN5", "AIN6",
                  "DNC_E5", "DNC_E10", "XTALI", "XTALO", "DE0", "DE1"]:
        px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num[pname])
        nc(px, py)

    # ---- right side: digital
    stub("ADuCM355", dx, DEV_Y, name_to_num["P0.4/I2C_SCL"], "SCL", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["P0.5/I2C_SDA"], "SDA", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["P0.10/UART_SOUT"], f"{dev}_TX", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["P0.11/UART_SIN"], f"{dev}_RX", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["SWCLK"], f"{dev}_SWCLK", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["SWDIO"], f"{dev}_SWDIO", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["~{RESET}"], "~{RESET}", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["BM/P1.1"], f"{dev}_BM", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["P2.4"], f"{dev}_ADDR", "R", 7.62)
    stub("ADuCM355", dx, DEV_Y, name_to_num["GPIO1/PWM1"], "~{ALERT}", "R", 7.62)
    px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num["GPIO0/PWM0"])
    nc(px, py)

    for pname in ["P0.0/SPI0_CLK", "P0.1/SPI0_MOSI", "P0.2/SPI0_MISO",
                  "P0.3/SPI0_CS", "P1.0/SYS_WAKE", "P1.2/SPI1_CLK",
                  "P1.3/SPI1_MOSI", "P1.4/SPI1_MISO", "P1.5/SPI1_CS"]:
        px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num[pname])
        nc(px, py)

    # supplies
    # supply rails: stagger the horizontal run so the power symbols do not collide
    for i, (pname, net) in enumerate([("AVDD", "+3V3A"), ("AVDD_DD", "+3V3"),
                                      ("DVDD", "+3V3"), ("DVDD_AD", "+3V3")]):
        px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num[pname])
        run = 20.32 + i * 6.35          # clear of the net-label column
        wire(px, py, px + run, py); wire(px + run, py, px + run, py - 7.62)
        rail(net, px + run, py - 7.62)
    for i, pname in enumerate(["AGND", "AGND_DD"]):
        px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num[pname])
        # must run PAST the DGND columns (20.32 / 26.67) or the AGND drop lands on
        # the DGND wire and shorts the analog and digital grounds together
        run = 33.02 + i * 6.35
        wire(px, py, px + run, py); wire(px + run, py, px + run, py + 7.62)
        rail("AGND", px + run, py + 7.62)
    for i, pname in enumerate(["DGND", "DGND_AD"]):
        px, py = pin_xy("ADuCM355", dx, DEV_Y, name_to_num[pname])
        run = 20.32 + i * 6.35
        wire(px, py, px + run, py); wire(px + run, py, px + run, py + 7.62)
        rail("GND", px + run, py + 7.62)
    for pname in ["AVDD_REG", "DVDD_REG", "DVDD_REG_AD",
                  "VDCDC_CAP1P", "VDCDC_CAP1N", "VDCDC_CAP2P",
                  "VDCDC_CAP2N", "VDCDC_CAPOUT"]:
        stub("ADuCM355", dx, DEV_Y, name_to_num[pname], f"{dev}_{pname}", "R", 7.62)

# ---------------------------------------------------------------- support blocks
SX = 600.71

text("POWER", SX - 20, 46, 2.2)
jpwr = place("CONN_HOST", SX, 70, ref="J5", value="Host I2C + power",
             fields={"Note": "VIN 4.0-5.5 V; nominal 5 V"})
px, py = pin_xy("CONN_HOST", SX, 70, "1"); wire(px, py, px - 5.08, py)
wire(px - 5.08, py, px - 5.08, py - 5.08); rail("VIN", px - 5.08, py - 5.08)
# GND must clear the SDA/SCL/ALERT/RESET stubs below it, which end at px-5.08.
# Routing the drop at px-5.08 would run straight through them and short the bus.
px, py = pin_xy("CONN_HOST", SX, 70, "2"); wire(px, py, px - 12.7, py)
wire(px - 12.7, py, px - 12.7, py + 12.7); rail("GND", px - 12.7, py + 12.7)
stub("CONN_HOST", SX, 70, "3", "SDA", "L", 5.08)
stub("CONN_HOST", SX, 70, "4", "SCL", "L", 5.08)
stub("CONN_HOST", SX, 70, "5", "~{ALERT}", "L", 5.08)
stub("CONN_HOST", SX, 70, "6", "~{RESET}", "L", 5.08)

ldo = place("ADP151", SX - 60, 110, ref="U3")
px, py = pin_xy("ADP151", SX - 60, 110, "1"); wire(px, py, px, py - 5.08)
rail("VIN", px, py - 5.08)
px, py = pin_xy("ADP151", SX - 60, 110, "3"); wire(px, py, px - 5.08, py)
wire(px - 5.08, py, px - 5.08, py - 12.7); rail("VIN", px - 5.08, py - 12.7)
px, py = pin_xy("ADP151", SX - 60, 110, "5"); wire(px, py, px, py - 5.08)
rail("+3V3", px, py - 5.08)
px, py = pin_xy("ADP151", SX - 60, 110, "4"); nc(px, py)
px, py = pin_xy("ADP151", SX - 60, 110, "2"); wire(px, py, px, py + 2.54)
rail("GND", px, py + 2.54)

for i, (cx, val, net) in enumerate([(SX - 80, "10u", "VIN"), (SX - 40, "10u", "+3V3"),
                                    (SX - 28, "1u", "+3V3")]):
    place("C", cx, 112, value=val)
    p1 = pin_xy("C", cx, 112, "1"); wire(*p1, p1[0], p1[1] - 2.54)
    rail(net, p1[0], p1[1] - 2.54)
    p2 = pin_xy("C", cx, 112, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("GND", p2[0], p2[1] + 2.54)

text("Analog rail: ferrite-isolated from +3V3", SX - 80, 130, 1.6)
fb = place("L_Ferrite", SX - 60, 142, ref="FB1", value="600R@100MHz")
p1 = pin_xy("L_Ferrite", SX - 60, 142, "1"); wire(*p1, p1[0], p1[1] - 2.54)
rail("+3V3", p1[0], p1[1] - 2.54)
p2 = pin_xy("L_Ferrite", SX - 60, 142, "2"); wire(*p2, p2[0], p2[1] + 2.54)
rail("+3V3A", p2[0], p2[1] + 2.54)
for cx, val in [(SX - 45, "10u"), (SX - 33, "100n")]:
    place("C", cx, 144, value=val)
    p1 = pin_xy("C", cx, 144, "1"); wire(*p1, p1[0], p1[1] - 2.54)
    rail("+3V3A", p1[0], p1[1] - 2.54)
    p2 = pin_xy("C", cx, 144, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("AGND", p2[0], p2[1] + 2.54)

# I2C pull-ups and ESD
text("I2C BUS", SX - 20, 166, 2.2)
for i, (net, cx) in enumerate([("SDA", SX - 10), ("SCL", SX + 10)]):
    r = place("R", cx, 182, value="2k2")
    p1 = pin_xy("R", cx, 182, "1"); wire(*p1, p1[0], p1[1] - 2.54)
    rail("+3V3", p1[0], p1[1] - 2.54)
    p2 = pin_xy("R", cx, 182, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(net, p2[0], p2[1] + 5.08, 270, "left bottom")
r = place("R", SX + 30, 182, value="10k")
p1 = pin_xy("R", SX + 30, 182, "1"); wire(*p1, p1[0], p1[1] - 2.54)
rail("+3V3", p1[0], p1[1] - 2.54)
p2 = pin_xy("R", SX + 30, 182, "2"); wire(*p2, p2[0], p2[1] + 5.08)
label("~{ALERT}", p2[0], p2[1] + 5.08, 270, "left bottom")
r = place("R", SX + 50, 182, value="10k")
p1 = pin_xy("R", SX + 50, 182, "1"); wire(*p1, p1[0], p1[1] - 2.54)
rail("+3V3", p1[0], p1[1] - 2.54)
p2 = pin_xy("R", SX + 50, 182, "2"); wire(*p2, p2[0], p2[1] + 5.08)
label("~{RESET}", p2[0], p2[1] + 5.08, 270, "left bottom")

esd = place("ESD_ARRAY", SX - 45, 195, ref="D1")
stub("ESD_ARRAY", SX - 45, 195, "1", "SDA", "L", 5.08)
stub("ESD_ARRAY", SX - 45, 195, "2", "SCL", "L", 5.08)
px, py = pin_xy("ESD_ARRAY", SX - 45, 195, "3"); wire(px, py, px, py + 2.54)
rail("GND", px, py + 2.54)

# address straps
text("I2C ADDRESS STRAPS (read on P2.4 at boot)", SX - 80, 214, 1.8)
for dev, cx, val, rail_name in [("U1", SX - 60, "0R", "GND"), ("U2", SX - 20, "10k", "+3V3")]:
    r = place("R", cx, 228, value=val)
    p1 = pin_xy("R", cx, 228, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"{dev}_ADDR", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("R", cx, 228, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail(rail_name, p2[0], p2[1] + 2.54)
    text(f"{dev} -> {'0x30' if dev=='U1' else '0x31'}", cx - 6, 240, 1.4)

# BM straps
for dev, cx in [("U1", SX + 20), ("U2", SX + 45)]:
    r = place("R", cx, 228, value="10k")
    p1 = pin_xy("R", cx, 228, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"{dev}_BM", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("R", cx, 228, "2"); wire(*p2, p2[0], p2[1] + 2.54)
    rail("+3V3", p2[0], p2[1] + 2.54)
text("BM pull-ups: pull low + reset = flash-erase recovery", SX + 8, 240, 1.4)

# RCAL resistors
text("EIS CALIBRATION RESISTORS", SX - 80, 254, 1.8)
for dev, cx in [("U1", SX - 60), ("U2", SX - 20)]:
    r = place("R", cx, 268, value="200R 0.1% 10ppm",
              fields={"Note": "RCAL between RCAL0 and RCAL1, low tempco"})
    p1 = pin_xy("R", cx, 268, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"{dev}_RCAL0", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("R", cx, 268, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(f"{dev}_RCAL1", p2[0], p2[1] + 5.08, 270, "left bottom")

# reference decoupling
text("REFERENCE / REGULATOR DECOUPLING  (values: see datasheet App Info)", SX - 80, 286, 1.8)
dec = [("VREF182", "4u7"), ("VREF25", "470n"), ("ADCVBIAS", "470n"),
       ("AVDD_REG", "470n"), ("DVDD_REG", "470n"), ("DVDD_REG_AD", "470n"),
       ("VDCDC_CAPOUT", "470n")]
for di, dev in enumerate(["U1", "U2"]):
    for i, (netsuf, val) in enumerate(dec):
        cx = SX - 72 + i * 17
        cy = 302 + di * 26
        place("C", cx, cy, value=val)
        p1 = pin_xy("C", cx, cy, "1"); wire(*p1, p1[0], p1[1] - 5.08)
        label(f"{dev}_{netsuf}", p1[0], p1[1] - 5.08, 90, "left bottom")
        p2 = pin_xy("C", cx, cy, "2"); wire(*p2, p2[0], p2[1] + 2.54)
        rail("AGND" if "VREF" in netsuf or "ADCV" in netsuf or "AVDD" in netsuf else "GND",
             p2[0], p2[1] + 2.54)

# DC-DC flying caps
for di, dev in enumerate(["U1", "U2"]):
    cy = 302 + di * 26
    place("C", SX + 52, cy, value="100n")
    p1 = pin_xy("C", SX + 52, cy, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"{dev}_VDCDC_CAP1P", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", SX + 52, cy, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(f"{dev}_VDCDC_CAP1N", p2[0], p2[1] + 5.08, 270, "left bottom")
    place("C", SX + 69, cy, value="100n")
    p1 = pin_xy("C", SX + 69, cy, "1"); wire(*p1, p1[0], p1[1] - 5.08)
    label(f"{dev}_VDCDC_CAP2P", p1[0], p1[1] - 5.08, 90, "left bottom")
    p2 = pin_xy("C", SX + 69, cy, "2"); wire(*p2, p2[0], p2[1] + 5.08)
    label(f"{dev}_VDCDC_CAP2N", p2[0], p2[1] + 5.08, 270, "left bottom")

# ---------------------------------------------------------------- T/RH + EEPROM
text("AMBIENT T / RH  (mandatory for compensation)", 300, 268, 2.0)
sht = place("SHT45", 330, 292, ref="U4")
stub("SHT45", 330, 292, "1", "SDA", "L", 5.08)
stub("SHT45", 330, 292, "2", "SCL", "L", 5.08)
px, py = pin_xy("SHT45", 330, 292, "3"); wire(px, py, px, py - 2.54)
rail("+3V3", px, py - 2.54)
px, py = pin_xy("SHT45", 330, 292, "4"); wire(px, py, px, py + 2.54)
rail("GND", px, py + 2.54)
place("C", 352, 292, value="100n")
p1 = pin_xy("C", 352, 292, "1"); wire(*p1, p1[0], p1[1] - 2.54); rail("+3V3", p1[0], p1[1] - 2.54)
p2 = pin_xy("C", 352, 292, "2"); wire(*p2, p2[0], p2[1] + 2.54); rail("GND", p2[0], p2[1] + 2.54)
text("addr 0x44", 320, 306, 1.4)

text("BOARD ID / CAL STORE", 300, 330, 2.0)
ee = place("24AA02E48", 335, 360, ref="U5")
for n in ("1", "2", "3"):
    nc(*pin_xy("24AA02E48", 335, 360, n))
stub("24AA02E48", 335, 360, "5", "SDA", "R", 5.08)
stub("24AA02E48", 335, 360, "6", "SCL", "R", 5.08)
nc(*pin_xy("24AA02E48", 335, 360, "7"))
px, py = pin_xy("24AA02E48", 335, 360, "8"); wire(px, py, px, py - 2.54)
rail("+3V3", px, py - 2.54)
px, py = pin_xy("24AA02E48", 335, 360, "4"); wire(px, py, px, py + 2.54)
rail("GND", px, py + 2.54)
text("addr 0x50, EUI-48 at 0xFA", 315, 378, 1.4)

# ---------------------------------------------------------------- debug headers
text("DEBUG / PROGRAMMING", 130, 424, 2.0)
for i, dev in enumerate(["U1", "U2"]):
    x = 150 + i * 60
    j = place("CONN_SWD", x, 448, ref=f"J{6+i}", value=f"SWD {dev}")
    px, py = pin_xy("CONN_SWD", x, 448, "1"); wire(px, py, px - 2.54, py)
    wire(px - 2.54, py, px - 2.54, py - 5.08); rail("+3V3", px - 2.54, py - 5.08)
    stub("CONN_SWD", x, 448, "2", f"{dev}_SWDIO", "L", 5.08)
    stub("CONN_SWD", x, 448, "3", f"{dev}_SWCLK", "L", 5.08)
    px, py = pin_xy("CONN_SWD", x, 448, "4"); wire(px, py, px - 2.54, py)
    wire(px - 2.54, py, px - 2.54, py + 5.08); rail("GND", px - 2.54, py + 5.08)
    stub("CONN_SWD", x, 448, "5", "~{RESET}", "L", 5.08)

juart = place("CONN_UART", 300, 448, ref="J8", value="UART U1")
px, py = pin_xy("CONN_UART", 300, 448, "1"); wire(px, py, px - 2.54, py)
wire(px - 2.54, py, px - 2.54, py - 5.08); rail("+3V3", px - 2.54, py - 5.08)
stub("CONN_UART", 300, 448, "2", "U1_TX", "L", 5.08)
stub("CONN_UART", 300, 448, "3", "U1_RX", "L", 5.08)
px, py = pin_xy("CONN_UART", 300, 448, "4"); wire(px, py, px - 2.54, py)
wire(px - 2.54, py, px - 2.54, py + 5.08); rail("GND", px - 2.54, py + 5.08)
juart2 = place("CONN_UART", 370, 448, ref="J9", value="UART U2")
px, py = pin_xy("CONN_UART", 370, 448, "1"); wire(px, py, px - 2.54, py)
wire(px - 2.54, py, px - 2.54, py - 5.08); rail("+3V3", px - 2.54, py - 5.08)
stub("CONN_UART", 370, 448, "2", "U2_TX", "L", 5.08)
stub("CONN_UART", 370, 448, "3", "U2_RX", "L", 5.08)
px, py = pin_xy("CONN_UART", 370, 448, "4"); wire(px, py, px - 2.54, py)
wire(px - 2.54, py, px - 2.54, py + 5.08); rail("GND", px - 2.54, py + 5.08)

# AGND / GND single-point tie + power flags
text("AGND-GND TIE + POWER FLAGS", 440, 424, 1.8)
rt = place("R", 450, 448, value="0R", fields={"Note": "Single-point analog/digital ground tie, place under U1"})
p1 = pin_xy("R", 450, 448, "1"); wire(*p1, p1[0], p1[1] - 2.54); rail("AGND", p1[0], p1[1] - 2.54, rot=180)
p2 = pin_xy("R", 450, 448, "2"); wire(*p2, p2[0], p2[1] + 2.54); rail("GND", p2[0], p2[1] + 2.54)
for i, (pn, rl) in enumerate([("VIN", "VIN"), ("+3V3A", "+3V3A"), ("GND", "GND"), ("AGND", "AGND")]):
    fx = 475 + i * 18
    place("PWR_FLAG", fx, 448, ref=f"#FLG{i+1}")
    wire(fx, 448, fx, 452)
    rail(rl, fx, 452, rot=(180 if rl in ("VIN", "+3V3A") else 0))

textbox("DESIGN NOTES\n"
        "RTIA selection (ADuCM355 LPTIA, programmable 1k...512k):\n"
        "  ES1-AG1-200 : 40 nA/ppm, 200 ppm FS -> 8 uA FS. RTIA = 100k -> 0.80 V FS.\n"
        "                16-bit ADC over ~+/-0.9 V -> ~27 uV LSB -> 0.27 nA -> ~0.007 ppm/LSB.\n"
        "  ES1-AG1-10  : 40 nA/ppm, 10 ppm FS -> 400 nA FS. RTIA = 512k -> 0.205 V FS -> ~0.0013 ppm/LSB.\n"
        "  Keep RLOAD = 100 R (EC Sense recommended load resistor for the ES1 series).\n"
        "Bias: VBIAS/VZERO 12-bit LPDACs, 0.2...2.4 V. 0 mV bias -> VBIAS = VZERO (typ. 1.1 V).\n"
        "      For biased gases set VBIAS = VZERO + Vbias_target.\n"
        "I2C: each ADuCM355 runs as an I2C target. Firmware reads its strap on P2.4 at boot and\n"
        "     selects 0x30 or 0x31, so one binary serves both devices.\n"
        "Layout: guard ring at VZERO potential around every SE net; no soldermask opening under\n"
        "     the sensor sockets; clean with no-clean flux only; keep SE traces < 15 mm; AGND and\n"
        "     DGND joined at one point under U1/U2; do not route I2C or SWD under the AFE section.",
        30, 312, 250, 88, 1.5)

# Added local supply bypass capacitors; one per supply pin on each AFE.
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

# ---------------------------------------------------------------- file assembly
lib_block = "\n".join(sym_text(n) for n in SYMBOLS)

out = []
out.append('(kicad_sch')
out.append('  (version 20230121)')
out.append('  (generator eeschema)')
out.append(f'  (uuid {ROOT_UUID})')
out.append(f'  (paper "{PAPER}")')
out.append('  (title_block')
out.append('    (title "4-Channel EC Sense ES1 Gas Sensor Front End - I2C")')
out.append('    (date "2026-09-16")')
out.append('    (rev "B")')
out.append('    (company "")')
out.append('    (comment 1 "2 x ADuCM355 dual potentiostat, 4 channels, single I2C bus")')
out.append('    (comment 2 "Sensor: EC Sense ES1 series, 3-pin C/S/R, 2.54 mm pitch")')
out.append('    (comment 3 "Rev B: datasheet pinout and decoupling corrections; see PCB_README.md")')
out.append('  )')
out.append('  (lib_symbols')
for line in lib_block.split('\n'):
    out.append('    ' + line)
out.append('  )')
for it in ITEMS:
    for line in it.split('\n'):
        out.append('  ' + line)
out.append('  (sheet_instances')
out.append('    (path "/" (page "1"))')
out.append('  )')
out.append(')')

with open("ECSense_4CH_I2C.kicad_sch", "w") as f:
    f.write("\n".join(out) + "\n")

print("components placed:", sum(1 for i in ITEMS if i.startswith('(symbol (lib_id')))
print("refs:", REFCOUNT)
print("wrote ECSense_4CH_I2C.kicad_sch")
