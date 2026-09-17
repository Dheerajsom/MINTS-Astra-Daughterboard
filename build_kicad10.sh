#!/usr/bin/env bash
# Regenerate the whole KiCad 10 project from gen_sch.py.
#   KICAD_CLI=/path/to/kicad-cli ./build_kicad10.sh
set -euo pipefail
KICAD_CLI="${KICAD_CLI:-kicad-cli}"
OUT="${OUT:-ECSense_4CH_I2C}"

echo "1/5 generating schematic"
python3 gen_sch.py

echo "2/5 checking connectivity"
python3 verify_sch.py > verify.log; head -8 verify.log

echo "3/5 extracting symbol library"
python3 make_symlib.py

echo "4/5 assembling project in ./$OUT"
mkdir -p "$OUT/ECGAS.pretty"
cp ECSense_4CH_I2C.kicad_sch "$OUT/$OUT.kicad_sch"
cp ECSense_4CH_I2C.kicad_pro "$OUT/$OUT.kicad_pro"
cp ECGAS.kicad_sym sym-lib-table fp-lib-table "$OUT/"
cp ECGAS.pretty/README.md "$OUT/ECGAS.pretty/"

echo "5/5 upgrading to the KiCad 10 format and exporting"
"$KICAD_CLI" sch upgrade --force "$OUT/$OUT.kicad_sch"
"$KICAD_CLI" sym upgrade "$OUT/ECGAS.kicad_sym"
"$KICAD_CLI" sch erc --output "$OUT/erc.rpt" --severity-error --severity-warning "$OUT/$OUT.kicad_sch" || true
"$KICAD_CLI" sch export pdf     -o "$OUT/$OUT.pdf"      "$OUT/$OUT.kicad_sch"
"$KICAD_CLI" sch export svg     --output "$OUT"          "$OUT/$OUT.kicad_sch"
"$KICAD_CLI" sch export netlist -o "$OUT/$OUT.net"      "$OUT/$OUT.kicad_sch"
"$KICAD_CLI" sch export bom     -o "$OUT/$OUT-bom.csv"  "$OUT/$OUT.kicad_sch"
echo "done -> $OUT/"
