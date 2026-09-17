#!/usr/bin/env python3
"""Extract the schematic's embedded symbols into a standalone ECGAS.kicad_sym library."""
import re, sys

src = open("ECSense_4CH_I2C.kicad_sch").read()

# locate the lib_symbols block
i = src.index("(lib_symbols")
depth, j = 0, i
while j < len(src):
    c = src[j]
    if c == '"':
        j += 1
        while src[j] != '"' or src[j-1] == "\\":
            j += 1
    elif c == "(":
        depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0:
            break
    j += 1
block = src[i:j+1]

# split its direct children (the individual symbols)
inner = block[len("(lib_symbols"):-1]
syms, depth, start = [], 0, None
k = 0
while k < len(inner):
    c = inner[k]
    if c == '"':
        k += 1
        while inner[k] != '"' or inner[k-1] == "\\":
            k += 1
    elif c == "(":
        if depth == 0:
            start = k
        depth += 1
    elif c == ")":
        depth -= 1
        if depth == 0:
            syms.append(inner[start:k+1])
    k += 1

out = ['(kicad_symbol_lib', '  (version 20211014)', '  (generator kicad_symbol_editor)']
for s in syms:
    # inside a library the symbol name carries no "LIB:" prefix
    s = re.sub(r'^\(symbol "ECGAS:', '(symbol "', s, count=1)
    out.append("  " + s.replace("\n", "\n  "))
out.append(")")
open("ECGAS.kicad_sym", "w").write("\n".join(out) + "\n")
print(f"wrote ECGAS.kicad_sym with {len(syms)} symbols")
