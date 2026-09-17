# EC Sense four-channel I2C PCB — revision B

120 × 80 mm outline, R3 corners, four M3 mounting holes on a 110 × 70 mm pattern. Four copper layers, nominal 1.6 mm FR-4. This is a hardware prototype: the ADuCM355 devices require application firmware and each installed gas sensor requires calibration. Design-rule checking is not a substitute for a powered bench test.

Open `ECSense_4CH_I2C.kicad_pro` in KiCad 10. The PCB, corrected schematic, footprint libraries, manufacturing outputs and verification reports are supplied together. The original schematic and generator are preserved in the working folder's `.history/pre-pcb*`, outside the release archive.

## Completed layout and checks

Final KiCad 10.0.5 checks: **0 DRC violations, 0 unconnected items, 0 schematic parity discrepancies, and 0 ERC violations**. No individual DRC exclusions are used. The checked board contains 109 footprints (96 schematic components, 4 mounting holes and 9 test pads), 1,309 track segments and 180 through vias. Check reports are in `verification/final-drc.*` and `verification/final-erc.*`.

The four layers, from top to bottom, are F.Cu (components/signals/ground), In1.Cu (ground with local escape routing), In2.Cu (power pours/signals), and B.Cu (passives/signals/ground). Analog sensor regions have surface copper keepouts; the temperature/humidity sensor is away from the regulator. Analog and digital grounds meet through R11. Ground stitching connects the surface pours to the inner ground layer.

Deliverables:

- `ECSense_4CH_I2C.kicad_pro`, `.kicad_sch`, `.kicad_pcb`: editable project and design.
- `manufacturing/gerbers/`: four copper layers, masks, silkscreens, pastes, board profile, separate plated/nonplated drill files, and Gerber job file.
- `manufacturing/assembly/`: current BOM and placement CSVs. JP1-JP4 are the only DNP items; all capacitors are fitted.
- `output/pdf/Fabrication_and_assembly.pdf`: mechanical, front/back assembly and drill drawings.
- `ECSense_4CH_I2C.pdf`: updated revision B schematic.
- `output/PCB-top.png` and `output/PCB-bottom.png`: views of the completed layout.
- `manufacturing/EC-Sense-120x80-Gerbers.zip`: fabrication files only.
- `EC-Sense-120x80-Project.zip`: editable design, local libraries, outputs and final checks.

The final KiCad files are authoritative. Scripts in the working folder's `scripts/` record construction and routing iterations; running them again can replace completed routing. These iteration scripts are not included in the release archive.

## Electrical corrections made before layout

The original schematic contained errors beyond the missing footprints:

- U1/U2 channel 0: CE0 is B1; RE0 is A1.
- U4 SHT45: SDA=1, SCL=2, VDD=3, GND=4.
- D1 PESD3V3L2BT: signal pins 1/2, common ground pin 3.
- U1/U2 AVDD_DD (G2) now uses the digital 3.3 V rail as required by the pin table.
- Shared ALERT moved from GPIO0 to GPIO1 (H10). GPIO0 drives high after reset and is unsuitable for the original wired connection. Firmware must emulate open drain: assert low, release by selecting input; never drive high.
- Reference/regulator capacitors and DC/DC flying capacitors now follow ADuCM355 Rev C. VZERO capacitors are populated.
- Added one local 100 nF bypass per ADuCM355 supply pin, plus EEPROM bypass.
- 24AA02E48 pins 1/2/3/7 are marked NC, rather than presenting unused pins as address/write-protect controls.
- VIN is specified as 4.0–5.5 V, nominal 5 V, to allow headroom for the 3.3 V LDO.

## Manufacturing and assembly

Order 4 copper layers, nominal 1.6 mm FR-4, ENIG, solder mask and silkscreen on both sides. No controlled-impedance requirement is specified. The fabricator must support **0.075 mm (approximately 3 mil) minimum trace/clearance, 0.20 mm finished via drills with 0.40 mm pads and 0.10 mm annular rings**. Stitching vias use 0.30 mm drills / 0.60 mm pads. Minimum hole-to-hole spacing is 0.20 mm and copper-to-board-edge clearance is 0.30 mm. The 0.5 mm LGA package requires fine tracks near the processors; ordinary 6/6 mil service is insufficient. Use tented signal vias and inspect the LGA joints after reflow. Discuss the 0.25 mm LGA lands and an approximately 80 µm stencil with the assembler. Surface-mounted parts are on both sides. The board uses ordinary through vias, with no blind/buried vias or via-in-pad process.

All manufacturing and placement outputs use the same absolute KiCad origin. The outline centerline extends from (50, 50) to (170, 130) mm; the line width is a drawing stroke, not extra board material. The four 3.2 mm nonplated mounting holes are at (55,55), (165,55), (55,125), and (165,125) mm. The outer dimensions are exactly 120 x 80 mm, with 3 mm corner radii. Drill and placement outputs follow their file-format axis conventions. The assembly PDF shows the bottom side mirrored for viewing from below; do not mirror the Gerbers.

J1–J4 each accept **three Mill-Max 0548-0-15-15-21-27-10-0 receptacles**. Their #21 contact accepts 0.381–0.559 mm pins; the ES1 pins are 0.40 ±0.01 mm. Footprint holes are 1.00 mm finished plated diameter (manufacturer minimum 0.9144 mm), with 1.8 mm pads and 2.54 mm pitch. C/S/R is mirrored from the sensor's bottom-view drawing into the PCB top view. **The earlier suggestions of Mill-Max 0350 and 0305 are unsuitable for these small sensor pins.**

The sensor drawing does not dimension the pin-row offset within the body. A conservative 14 × 24 mm component courtyard reserves the full possible body envelope around the pin row; no guessed offset is needed for PCB fit. The 3D socket representation is illustrative, not a mating-part inspection model. Insert the gas sensors after soldering and cleaning. Do not expose the sensor apertures or SHT45 to solvents or conformal coating.

C1–C3, C9–C11, C17–C19 and C25–C27: C0G/NP0. Other small capacitors: X7R, preferably 10 V or higher; check effective capacitance under DC bias. R9/R10: 200 Ω, 0.1%, ≤10 ppm/°C. Fit all capacitors. Leave JP1–JP4 open during operation; they are only storage/transport shorts. R11 is the sole AGND–GND connection and must be populated.

## Connectors and bring-up

| Connector | Pin order |
|---|---|
| J5, JST PH 6-pin host | 1 VIN, 2 GND, 3 SDA, 4 SCL, 5 ALERT, 6 RESET |
| J6/J7, 1.27 mm SWD | 1 3V3 reference, 2 SWDIO, 3 SWCLK, 4 GND, 5 RESET |
| J8/J9, 2.54 mm UART | 1 3V3 reference, 2 MCU TX, 3 MCU RX, 4 GND |

All bus/debug signals are **3.3 V logic**. Supply through J5; the 3V3 debug pins are voltage references, not an additional power input. Program U1 and U2 independently using SWD. Their default addresses 0x30 and 0x31 are a firmware convention selected by the P2.4 straps, not fixed hardware addresses. U4 uses 0x44; U5 uses 0x50. BOOT test pads allow recovery by holding the corresponding BM pin low during reset.

Power up initially with a current-limited 5 V supply and no gas sensors. Check 3V3/3V3A and internal regulated/reference voltages, debug access, I2C, and the ALERT release state. Configure the potentiostats and gas-specific bias before insertion. Verify current measurement with a precision current source, then perform clean-air zero and certified-gas span calibration. Firmware, calibrated ppm conversion, environmental qualification and physical bench testing are not included in this PCB deliverable.

## Source drawings

- [Analog Devices ADuCM355 Rev C, pinout and recommended components](https://www.analog.com/media/en/technical-documentation/data-sheets/ADuCM355.pdf), pp. 20–23 and 26–28.
- [Sensirion SHT4x data sheet](https://sensirion.com/resource/datasheet/sht4x).
- [Nexperia PESD3V3L2BT](https://assets.nexperia.com/documents/data-sheet/PESD3V3L2BT.pdf).
- [Microchip 24AA02E48](https://ww1.microchip.com/downloads/en/DeviceDoc/22124C.pdf).
- [EC Sense ES1 mechanical drawing](https://ecsense.com/wp-content/uploads/2021/01/ES1-AG1-200-01-All-Gas-Sensor_Datasheet_V1.4_20250306.pdf).
- [Mill-Max receptacle catalog, p. 157](https://www.mill-max.com/sites/default/files/external/catalog/2020-03/153-201_0.pdf).

The earlier working-folder `DESIGN.md` is historical architecture context, outside the release archive. This file and the revision B schematic supersede conflicting pinout, capacitor, socket, power, and ALERT details in it.

Standard footprints and available 3D models are copied from the installed KiCad 10 libraries; see `libraries/LICENSE.md` and `models/kicad/LICENSE.md`. Local 3D model paths replace installation-specific paths. The custom ADuCM355 and socket bodies are illustrative; the SHT45 land pattern is supplied even though its installed KiCad 3D model is unavailable. Land patterns and manufacturer drawings govern assembly, not the rendering.
