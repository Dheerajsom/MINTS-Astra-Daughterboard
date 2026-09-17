> **Revision B PCB update:** Read [PCB_README.md](PCB_README.md) for corrected pinouts, component values, socket selection, power range and bring-up requirements. Several assumptions in this original architecture note were incorrect. The corrected schematic and PCB are authoritative.

# 4-Channel EC Sense Gas Sensor Board with a Single I²C Bus

Design note + KiCad schematic for a custom carrier that takes four **bare ES1 3-pin
electrochemical sensors** and presents all their data on one I²C bus.

Source datasheets (in this folder):
`ES1-AG1-200-01 All Gas Sensor_Datasheet_V1.4_20250306.pdf`,
`TB600B&C-IAQ_Datasheet_V3.0_20250904.pdf`,
`EC Sense Product List_V1.9_20250409.pdf`.

---

## 1. What the datasheets actually give you

### 1.1 Bare sensor — ES1 series (the 3-pin part)

From the ES1-AG1-200-01 datasheet:

| Parameter | Value | Design consequence |
|---|---|---|
| Operating principle | Amperometric, **3-electrode** | Needs a potentiostat, not just an ADC |
| Pins (bottom view) | **C, S, R** in line — Counter, Sense (working), Reference | 3 pins, 2.54 mm pitch, Ø0.4 mm, body ~11.5 × 11.5 × 5.6 mm |
| Bias voltage | **0 mV** | V_BIAS = V_ZERO for this part; other gases may differ |
| Recommended load resistor | **100 Ω** | Set the AFE's R_LOAD to 100 Ω |
| Sensitivity | **40 nA/ppm ± 10** (CO cal), 55 nA/ppm ± 15 (isobutene cal) | 200 ppm FS → **8 µA**; 1000 ppm overload → 40 µA |
| Zero current | **± 100 nA** | = ±2.5 ppm equivalent. Zeroing in clean air is mandatory, not optional |
| Resolution | 0.1 ppm quoted "16-bit ADC" | 0.1 ppm ≈ 4 nA — well inside a decent TIA+ADC |
| Response | T50 < 10 s, T90 < 30 s | 1–4 Hz output rate is plenty; use the rest for averaging |
| Warm-up | < 60 s | |
| Temperature curve | ≈ **4 nA/ppm at −40 °C → ≈ 51 nA/ppm at +50 °C** | ~12× swing. **On-board temperature measurement and compensation is compulsory** |
| Long-term drift | < 5 %/year, life > 3 years | Recalibration/cartridge-swap plan needed |
| Storage | 0–20 °C (optimum 4–6 °C), 12 months | Keep spares refrigerated; ship with the electrode shorting clip fitted |

Two things worth flagging before you commit to a BOM:

- **AG1 "All Gas" is deliberately non-selective.** The cross-sensitivity table shows
  CO reads 105 ppm for a 100 ppm test, H₂ reads 625 ppm for 2000 ppm, AsH₃ reads 4 ppm
  for a 1 ppm calculated concentration, and NO₂/O₃ read *negative*. Four AG1 sensors will
  not give you four gases — populate the four sockets with gas-specific ES1 parts
  (CO, H₂S, NO₂, SO₂, NH₃, O₃, HCHO, …) from the product list.
- **O₂ (`01-ES1-O2-25%-01`) is electrically different** from the amperometric parts.
  If you need O₂, treat it as a separate channel variant, not a drop-in.

### 1.2 Ready-made module — TB600B/C (the "breakout board")

The TB600B&C is EC Sense's own breakout: the ES1 sensor + a microcontroller + a
temperature/humidity sensor + a flash chip holding the factory calibration, on a
23 × 25.5 × 9.5 mm board with a 4-pin cable.

| Parameter | Value |
|---|---|
| Output | UART TTL 3.3 V **or** I²C 3.3 V (separate part numbers, `…-I2C-01`) |
| I²C pinout | VCC = red, GND = black, **SDA = yellow, SCL = green** |
| **I²C clock** | **≤ 20 kHz** |
| Supply | 3.3–5.5 V, 5 V recommended; ~3.4–6.2 mA (I²C, LED off / peak) |
| Sleep | 0.9 mA @ 5 V |
| On-board T/RH | ±0.2 °C, ±2 % RH |
| Protocol | Q&A mode by default, switchable to active-upload |

**Why this pushes you toward your own board.** The datasheet publishes no address-select
pin and no address-configuration command, and the bus is limited to 20 kHz. Multiple
TB600-I2C modules on one bus will therefore collide. Your options with the stock modules
are a **TCA9548A I²C mux** (one module per channel) or an **LTC4316 address translator**
per module — both of which mean you are still paying for four microcontrollers, four
T/RH sensors and ~100 mm² each, to end up with a 20 kHz bus.

> **Plan B, if you want something working next week:** 4 × `04-TB600x-<gas>-<range>-I2C-01`
> behind a TCA9548A, 5 V rail, host talks to 0x70 then to the module. Zero analog design
> risk. Take this path for the first prototype if the science matters more than the board.

The rest of this document is **Plan A**: your own carrier around the bare ES1.

---

## 2. What the front end has to do

Per channel:

1. Hold the **reference electrode** at a programmed potential relative to the working
   electrode (0 mV for most EC Sense parts) — i.e. a potentiostat with a control
   amplifier driving the counter electrode.
2. Convert the working-electrode current to voltage with a **transimpedance amplifier**,
   with a settable R_LOAD of 100 Ω in series with the working electrode.
3. Digitise it with enough resolution that the **LSB is well under the sensor noise**.

Numbers, using 40 nA/ppm:

| Sensor | FS current | R_TIA | TIA FS | ADC LSB (16-bit over ±0.9 V) | ppm/LSB |
|---|---|---|---|---|---|
| ES1-AG1-**200** | 8.0 µA | 100 kΩ | 0.80 V | 27.5 µV → 0.275 nA | **0.0069 ppm** |
| ES1-AG1-**10** | 400 nA | 512 kΩ | 0.205 V | 27.5 µV → 0.054 nA | **0.0013 ppm** |
| ES1-CO-**1000** | 40 µA | 20 kΩ | 0.80 V | 27.5 µV → 1.4 nA | 0.034 ppm |

So a 16-bit ADC behind a programmable TIA comfortably beats the datasheet's own
0.01 ppm / 0.1 ppm resolution figures. **The limit is not the LSB — it is the ±100 nA
zero current, the 5 %/year drift and the 12× temperature coefficient.** Budget your
effort accordingly: the analog design is the easy part, the calibration is not.

Since R_TIA is switchable at runtime on the chosen part, implement **autoranging**:
drop to a low gain when a channel saturates (the ES1 overload range is 5× full scale)
and report the range in the status register.

---

## 3. IC options

| Role | Part | Key numbers | Verdict |
|---|---|---|---|
| **Potentiostat + ADC + MCU, 2 ch** | **ADuCM355** (ADI) | 2 potentiostats, LPTIA R_TIA 1 k–512 kΩ, R_LOAD 10/30/50/100/1.5k/3k/3.5k Ω, 16-bit 400 kSPS ADC, dual 12-bit bias DACs 0.2–2.4 V, EIS 0.016 Hz–200 kHz, Cortex-M3 26 MHz / 128 kB flash, UART+I²C+SPI, 72-LGA 6×5 mm, 2.8–3.6 V, 4.75–5.2 mA active / 3 µA hibernate | **Chosen.** One part does the whole channel, each device is its own I²C target, and EIS gives you sensor-health diagnostics for free |
| Potentiostat AFE, **4 ch**, no MCU | MAX30134 (ADI/Maxim) | 4 DC channels + 1 EIS channel, 4 × 16-bit current ADCs, 4 × 12-bit DACs, 3.5 µA bias current, 25-bump WLP 2.93 × 2.93 mm, ~$5.45/1k, **SPI only** | Strongest alternative — one chip for all four channels, half the cost. Costs you an external MCU and 0.4 mm-pitch WLP assembly |
| Same analog core, AFE only | AD5941 / AD5940 | SPI, pair with STM32G0/L4/RP2350 | Use if you already have an MCU you like and want ADI's analog core |
| Cheap single-channel potentiostat | TI **LMP91000** / LMP91002 | R_TIA 2.75 k–350 kΩ, internal bias 1–24 % of V_REF, I²C **for configuration only**, analog V_OUT, fixed address 0x48 with an **MENB** pin so several can share a bus | The classic budget option; needs an external ADC and 4 chip-selects |
| Precision I²C ADC (if using LMP91000) | TI ADS122C04 (24-bit, 2 diff ch, PGA), TI ADS1115 (16-bit, 4 ch, 4 addr), Microchip MCP3424 (18-bit, 4 ch, 8 addr) | | ADS122C04 if you care about noise, ADS1115 if you care about price |
| Discrete potentiostat | MCP6V51 (5 µV offset), LTC6078, ADA4505-2, LMP7721 (3 fA I_B), ADA4530-1 (fA) | | Only if you want full control of the loop and low-leakage input |
| I²C mux (address collisions) | TCA9548A / PCA9548A | 8 channels, 0x70–0x77 | Required for the TB600-I2C route |
| I²C address translator | LTC4316 | remaps a fixed-address target | Alternative to a mux |
| Level translation | PCA9306, TXS0102 | | If the host is 1.8 V |
| Bus extension | LTC4311 (active pull-up), PCA9515A | | If the sensor head is on a cable |
| T / RH | **SHT45-AD1B** (0x44), SHT40, or TMP117 | ±0.1 °C / ±1.0 % RH | Mandatory for compensation |
| ID + cal store | **24AA02E48** (0x50, EUI-48 at 0xFA) | | Board serial + per-sensor cal blob |
| Analog LDO | **ADP151AUJZ-3.3** | 9 µV_rms, 200 mA | Clean rail for the AFE |
| ESD | PESD3V3L2BT, TPD2E007 | | On SDA/SCL |
| Sensor socket | Mill-Max **0350 / 0305** series press-fit receptacles, or a 3-way SIP strip (Mill-Max 801/851 series, Preci-Dip 801-87-003) | accept 0.30–0.51 mm pins | Confirm against the Ø0.4 mm ES1 pin |

### Why ADuCM355 over MAX30134 here

You asked for a smart node per sensor, which the ADuCM355 gives you directly: firmware,
calibration and linearisation live next to the analog, the host sees clean ppm numbers,
and each device is an independent I²C target so a channel failure does not take the bus
down. It is also a hand-solderable LGA rather than a 0.4 mm WLP. The trade is cost
(~2 × ADuCM355 vs 1 × MAX30134) and firmware effort — you are writing an I²C target
driver, not just reading registers.

---

## 4. Chosen architecture

```
   ES1 socket J1 ──C/S/R──┐
                          ├── ADuCM355 U1  (pot 0, pot 1)  ──┐
   ES1 socket J2 ──C/S/R──┘        I²C target 0x30           │
                                                             ├── SDA / SCL ── host (J5)
   ES1 socket J3 ──C/S/R──┐                                  │      + /ALERT, /RESET
                          ├── ADuCM355 U2  (pot 0, pot 1)  ──┤
   ES1 socket J4 ──C/S/R──┘        I²C target 0x31           │
                                                             │
                     SHT45 (0x44) ───────────────────────────┤
                     24AA02E48 (0x50) ───────────────────────┘
```

- Both ADuCM355 run **the same firmware image**; each reads a strap resistor on **P2.4**
  at boot (U1 → 0 Ω to GND → 0x30, U2 → 10 kΩ to +3V3 → 0x31).
- One shared open-drain **/ALERT** (GPIO0 on both devices) for threshold alarms, so the
  host does not have to poll.
- **/RESET** is bussed to both devices and brought out to the host connector.
- Programming: SWD per device (J6, J7); **BM/P1.1** pulled up with a test point —
  pulling it low during reset drops the part into a loop so a bad image can be erased
  over SWD. UART on J8/J9 for logging and the serial bootloader.
- Analog rail **+3V3A** is ferrite-isolated from the digital +3V3; **AGND** and **GND**
  meet at a single 0 Ω (R11) under U1.
- **RCAL = 200 Ω, 0.1 %, ≤10 ppm/°C** per device (between RCAL0 and RCAL1) — this is the
  reference the EIS engine calibrates against.

### Per-channel passives (all four channels identical)

| Part | Value | Function |
|---|---|---|
| C_CE | 100 nF | CE ↔ CAP_POT, potentiostat loop compensation |
| C_RC | 100 nF | between RCx_0 and RCx_1, LPTIA filter |
| C_LPF | 4.7 µF | on AIN4_LPF0 / AIN7_LPF1 |
| C_VBIAS | 100 nF | VBIAS decoupling |
| C_VZERO | 100 nF (DNP) | optional, fit per ADI reference design |
| 3 × 22 pF C0G | — | CE / SE / RE to AGND, at the socket, EMC |
| JP (DNP) | — | SE–RE shorting jumper for storage/transport only |

---

## 5. Firmware: suggested I²C register map

8-bit register address, auto-increment, MSB-first, repeated-start for reads.

| Addr | R/W | Bytes | Contents |
|---|---|---|---|
| 0x00 | R | 1 | `WHO_AM_I` = 0xEC |
| 0x01 | R | 1 | `STATUS`: bit0 ch0 ready, bit1 ch1 ready, bit2 ch0 overrange, bit3 ch1 overrange, bit4 warm-up, bit7 fault |
| 0x02 | RW | 1 | `CTRL`: bit0 ch0 enable, bit1 ch1 enable, bit2 start EIS, bit6 sleep, bit7 soft reset |
| 0x03 | RW | 1 | `ODR` (0 = 1 Hz, 1 = 2 Hz, 2 = 4 Hz) |
| 0x10 | R | 4 | CH0 electrode current, int32, **pA** |
| 0x14 | R | 4 | CH0 concentration, int32, **ppb** (temperature-compensated) |
| 0x18 | R | 4 | CH1 electrode current, int32, pA |
| 0x1C | R | 4 | CH1 concentration, int32, ppb |
| 0x20 | R | 2 | Die temperature, int16, 0.01 °C |
| 0x22 | RW | 2 | Ambient temperature written by host (or read from SHT45), int16, 0.01 °C |
| 0x24 | RW | 2 | Ambient RH, uint16, 0.01 %RH |
| 0x30 | RW | 1 | CH0 R_TIA index (0 = auto) |
| 0x31 | RW | 1 | CH1 R_TIA index |
| 0x32 | RW | 2 | CH0 V_BIAS, uint16, DAC code |
| 0x34 | RW | 2 | CH1 V_BIAS |
| 0x40 | RW | 16 | CH0 sensor ID string |
| 0x50 | RW | 4 | CH0 sensitivity, nA/ppm × 1000 |
| 0x54 | RW | 4 | CH0 zero current, pA |
| 0x58 | RW | 4 | CH0 temperature-compensation polynomial coefficients |
| 0x70 | R | 8 | Last EIS result: R_s, C_dl (sensor-health indicator) |
| 0x7E | RW | 1 | `SAVE_CAL` — write 0xA5 to commit cal to flash |

Temperature compensation: store the ES1 curve as a 3rd-order polynomial in T normalised
to 25 °C, `S(T) = S₂₅ · (a₀ + a₁·ΔT + a₂·ΔT² + a₃·ΔT³)`, fitted to the curve on page 3 of
the ES1 datasheet, then refined against your own chamber data. Do **not** use a single
%/°C coefficient — the curve is strongly non-linear below 0 °C.

---

## 6. Layout rules that actually matter

The working-electrode node carries hundreds of picoamps to a few microamps. Leakage,
not noise, is what will ruin it.

1. **Guard ring** around every SE net and its via/pad, driven at V_ZERO (not AGND), on
   both the top layer and the layer directly beneath.
2. Keep SE traces **short (< 15 mm), on one layer, no vias**. Route CE and RE beside
   them, never crossing a digital net.
3. **No solder-mask opening** under the sockets other than the pads. Assemble with
   no-clean flux and clean anyway; ionic residue between SE and AGND at 10¹¹ Ω is a
   0.03 ppm offset.
4. 4-layer stack: L1 AFE + signal, L2 solid GND, L3 +3V3 / +3V3A (split, not overlapping
   the AFE), L4 digital.
5. Do **not** route I²C, SWD or the DC-DC flying-cap nets under the AFE section of U1/U2.
6. AGND and DGND join at **one** point (R11) under the device; AGND pour covers only the
   AFE corner.
7. Put the **SHT45 in the middle of the four sockets**, thermally coupled to them, with a
   routed slot isolating it from the LDO and the MCU dies. It is measuring *the sensors'*
   temperature, not the board's.
8. Keep the LDO and any heat source at the opposite end of the board. A 1 °C gradient
   across the sensor cluster is a ~2.5 % reading error at room temperature.
9. Conformal-coat the board **except** the socket area and the sensor apertures. Never
   let alcohol, acetone or strong solvent near the sensors (explicit datasheet warning).

---

## 7. BOM (4 channels)

| Qty | Ref | Part | Description |
|---|---|---|---|
| 2 | U1, U2 | ADUCM355BCCZ | Dual potentiostat + 16-bit ADC + Cortex-M3, 72-LGA |
| 1 | U3 | ADP151AUJZ-3.3 | 3.3 V 200 mA ultra-low-noise LDO, TSOT-23-5 |
| 1 | U4 | SHT45-AD1B | T/RH sensor, I²C 0x44 |
| 1 | U5 | 24AA02E48T-I/SN | 2 kbit EEPROM with EUI-48, I²C 0x50 |
| 4 | J1–J4 | 3 × Mill-Max 0350-series receptacle (or 1 × 3-way SIP socket) | EC Sense ES1 socket, 2.54 mm, Ø0.4 mm pin |
| 1 | J5 | JST PH B6B-PH-K | Host: VIN, GND, SDA, SCL, /ALERT, /RESET |
| 2 | J6, J7 | 1×5 1.27 mm header | SWD |
| 2 | J8, J9 | 1×4 2.54 mm header | UART / serial bootloader |
| 1 | D1 | PESD3V3L2BT | ESD array on SDA/SCL |
| 1 | FB1 | 600 Ω @ 100 MHz, 0805 | +3V3 → +3V3A |
| 2 | R (RCAL) | 200 Ω, 0.1 %, ≤10 ppm/°C | EIS calibration |
| 2 | R | 2.2 kΩ | I²C pull-ups |
| 3 | R | 10 kΩ | /ALERT, /RESET, U2 address strap |
| 2 | R | 10 kΩ | BM pull-ups |
| 1 | R | 0 Ω | U1 address strap (→ 0x30) |
| 1 | R11 | 0 Ω | AGND–GND single-point tie |
| 12 | C | 22 pF C0G | Electrode EMC filters (3 per channel) |
| 8 | C | 100 nF X7R | C_CE, C_VBIAS (2 per channel) |
| 4 | C | 100 nF X7R | C_RC (1 per channel) |
| 4 | C | 4.7 µF X7R | C_LPF (1 per channel) |
| 4 | C | 100 nF (DNP) | C_VZERO |
| ~20 | C | 100 nF / 1 µF / 4.7 µF | Supply, regulator and DC-DC decoupling — **values per ADuCM355 datasheet Applications Information** |
| 4 | JP1–JP4 | Solder jumper (DNP) | SE–RE storage short |

---

## 8. KiCad 10 project

Everything is written in the **native KiCad 10 format** — not a KiCad 7 file that
KiCad 10 upgrades on open. The schematic is `version 20260306`
(`generator_version "10.0"`), the symbol library is `version 20251024`, and the project
file uses `meta.version 3` / `net_settings.meta.version 5`. All of it was produced and
checked with KiCad **10.0.6**.

### `ECSense_4CH_I2C/`

| File | What it is |
|---|---|
| `ECSense_4CH_I2C.kicad_pro` | Project file, `Default` / `SENSOR` / `POWER` net classes pre-created |
| `ECSense_4CH_I2C.kicad_sch` | A1 schematic, 198 symbols |
| `ECGAS.kicad_sym` | The 19 custom symbols as a real, editable library |
| `sym-lib-table` | Registers `ECGAS` against `${KIPRJMOD}/ECGAS.kicad_sym` |
| `fp-lib-table` | Registers `ECGAS.pretty` for the two custom footprints |
| `ECGAS.pretty/README.md` | Dimensions and guidance for the two footprints you still have to draw |
| `ECSense_4CH_I2C.pdf` / `.svg` | Schematic plots, exported by KiCad |
| `ECSense_4CH_I2C.net` | KiCad netlist |
| `ECSense_4CH_I2C-bom.csv` | BOM, exported by KiCad |
| `erc.rpt` | The ERC report as it stands |

Build scripts, at the top level:

| File | What it is |
|---|---|
| `gen_sch.py` | Generates the schematic — edit the constants at the top to change channel count, spacing or net names |
| `verify_sch.py` | Connectivity checker: duplicate refdes, dangling labels/wires, single-pin nets, off-grid points, **and T-junctions** |
| `make_symlib.py` | Extracts the embedded symbols into `ECGAS.kicad_sym` |
| `build_kicad10.sh` | Runs the whole chain: generate → check → extract library → upgrade to KiCad 10 → ERC + PDF + SVG + netlist + BOM |

Rebuild with:

```sh
KICAD_CLI=/path/to/kicad-cli ./build_kicad10.sh
```

`gen_sch.py` writes the older s-expression dialect and `build_kicad10.sh` calls
`kicad-cli sch upgrade` / `sym upgrade` to convert — so the format conversion is always
done by KiCad itself rather than by hand.

### Two real shorts that KiCad 10's ERC caught

Running proper ERC found bugs that a syntax check would never have shown. Both were the
same mistake: **a wire routed straight through another wire's endpoint**, which KiCad
treats as a connection.

1. **The entire I²C bus was shorted to GND.** At J5, the GND pin's drop wire ran down
   past the SDA and SCL stubs at exactly the x they ended on. SDA, SCL and GND became
   one net — the board would have been dead on arrival with no obvious cause.
2. **AGND was shorted to GND at both ADuCM355s.** The AGND rail dropped onto the DGND
   rail's horizontal run, merging the analog and digital grounds and making the R11
   single-point tie meaningless — which would have quietly undone the grounding scheme
   in section 6.
3. A third instance at the EEPROM: the `WP` pull-down ran through the SDA and SCL stubs.

`verify_sch.py` now models T-junctions (a point lying in the *interior* of a wire, not
just at its endpoints), so this class of error is caught before KiCad ever sees the file.

### Validation actually performed (KiCad 10.0.6)

```
kicad-cli sch upgrade          -> version 20260306, generator_version 10.0
kicad-cli sym upgrade          -> version 20251024, generator_version 10.0
kicad-cli sch erc              -> 6 violations, ALL of them the two footprints
                                  still to be drawn (4 x ES1 socket, 2 x ADuCM355 LGA).
                                  Zero pin_to_pin, zero multiple_net_names,
                                  zero power_pin_not_driven, zero dangling.
kicad-cli sch export netlist   -> 83 nets, every one with >= 2 nodes
kicad-cli sch export pdf/svg   -> OK
kicad-cli sch export bom       -> OK
verify_sch.py                  -> no duplicate refdes, no dangling labels or wires,
                                  no single-pin nets, 0 T-junctions, all on 1.27 mm grid
```

Netlist spot-check, confirming the buses are separate and the sensor wiring is right:

```
SDA       7  D1.1  J5.3  R1.2  U1.H5  U2.H5  U4.1  U5.5
SCL       7  D1.3  J5.4  R2.2  U1.J5  U2.J5  U4.4  U5.6
GND      29   (separate from AGND)
AGND     41   (separate from GND, tied only through R11)
+3V3A     7  C36.1 C37.1 FB1.2 U1.F11 U1.G2 U2.F11 U2.G2
~{ALERT}  4  J5.5  R3.2  U1.G10 U2.G10
/CH1_CE   4  C1.1  C4.1  J1.1(C)  U1.A1(CE0)
/CH4_SE   4  C26.1 J4.2(S) JP4.1  U2.A9(SE1)
```

## 9. Verify before you fabricate

1. **ADuCM355 pinout.** The pin numbers in the schematic were transcribed from the
   Rev. C datasheet pin table. Two assignments (B1 = RE0, B2 = VZERO0) were reconstructed
   from the symmetry of the channel-1 pins, not read directly. **Check all 72 pins against
   the official PDF and the EVAL-ADUCM355QSPZ reference schematic.**
2. **DC-DC and regulator capacitors.** VDCDC_CAP1P/1N/2P/2N/CAPOUT, AVDD_REG, DVDD_REG,
   DVDD_REG_AD values in the schematic are placeholders. Take them from the datasheet.
3. **ES1 socket.** Confirm the Ø0.4 mm pin diameter and 2.54 mm pitch against the
   mechanical drawing of *your* part numbers, and against the socket's pin-acceptance range.
   Then draw `ECGAS:EC_Sense_ES1_3pin_2.54mm` and `ECGAS:ADuCM355_LGA-72_6x5mm` — these are
   the only two footprints not resolved by the standard KiCad 10 libraries, and the only
   two ERC violations left in `erc.rpt`. See `ECGAS.pretty/README.md`.
4. **Bias per gas.** The ES1-AG1 is 0 mV. Confirm with EC Sense for each gas variant you
   intend to use before fixing the V_BIAS default in firmware.
5. **I²C target mode.** Confirm the ADuCM355 I²C peripheral supports clock stretching in
   target mode at the speed your host runs, and that your host tolerates it.
6. **Bench check the TIA before trusting it.** Drive a known current into a socket
   (a precision voltage source through a 1 GΩ resistor gives clean nanoamps) and verify
   gain and linearity at each R_TIA setting. Then zero in clean air / N₂ and span with
   certified gas.

---

## Sources

- [ADuCM355 product page, Analog Devices](https://www.analog.com/en/products/aducm355.html)
- [ADuCM355 datasheet (Rev. C)](https://www.analog.com/media/en/technical-documentation/data-sheets/aducm355.pdf)
- [ADuCM355 Hardware Reference Manual UG-1262](https://www.analog.com/media/en/technical-documentation/user-guides/aducm355-hardware-reference-manual-ug-1262.pdf)
- [MAX30131/MAX30132/MAX30134 electrochemical sensor AFEs](https://www.analog.com/en/products/max30134.html)
- [MAX30131/32/34 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/max30131-max30132-max30134.pdf)
- [AD5941 analog front end](https://www.analog.com/en/products/ad5941.html)
- [AD5940 analog front end](https://www.analog.com/en/products/ad5940.html)
- [AN-2058: ADuCM355 User Bootloader](https://www.analog.com/en/resources/app-notes/an-2058.html)
- EC Sense `ES1-AG1-200-01 All Gas Sensor_Datasheet_V1.4_20250306.pdf` (local)
- EC Sense `TB600B&C-IAQ_Datasheet_V3.0_20250904.pdf` (local)
- EC Sense `EC Sense Product List_V1.9_20250409.pdf` (local)
