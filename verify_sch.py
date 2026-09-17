#!/usr/bin/env python3
"""Structural / electrical sanity check on the generated .kicad_sch."""
import sexpdata, collections, sys, math

S = sexpdata.Symbol
d = sexpdata.loads(open("ECSense_4CH_I2C.kicad_sch").read())

def name(x):
    return str(x[0]) if isinstance(x, list) and x else None

def find(node, tag):
    return [c for c in node if isinstance(c, list) and name(c) == tag]

def get(node, tag):
    r = find(node, tag)
    return r[0] if r else None

# ---------- gather lib symbols
libs = {}
for sym in find(get(d, "lib_symbols"), "symbol"):
    lid = str(sym[1])
    pins = []
    for sub in find(sym, "symbol"):
        for p in find(sub, "pin"):
            at = get(p, "at")
            num = str(get(p, "number")[1])
            pins.append((num, float(at[1]), float(at[2]), float(at[3])))
    libs[lid] = pins

# ---------- placed symbols
refs = collections.Counter()
pin_points = collections.defaultdict(list)   # (x,y) -> [ref.pin]
for sym in d:
    if not (isinstance(sym, list) and name(sym) == "symbol"):
        continue
    lid = str(get(sym, "lib_id")[1])
    at = get(sym, "at")
    x, y, rot = float(at[1]), float(at[2]), float(at[3])
    ref = None
    for p in find(sym, "property"):
        if str(p[1]) == "Reference":
            ref = str(p[2])
    refs[ref] += 1
    for num, px, py, prot in libs[lid]:
        if rot == 90:   px, py = -py, px
        elif rot == 180: px, py = -px, -py
        elif rot == 270: px, py = py, -px
        pin_points[(round(x + px, 3), round(y - py, 3))].append(f"{ref}.{num}")

dups = {r: c for r, c in refs.items() if c > 1}
print("duplicate refdes:", dups if dups else "none")

# ---------- wires (union-find over endpoints)
parent = {}
def froot(a):
    parent.setdefault(a, a)
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
def union(a, b):
    ra, rb = froot(a), froot(b)
    if ra != rb: parent[ra] = rb

wires = []
for w in find(d, "wire"):
    pts = get(w, "pts")
    a = (round(float(pts[1][1]), 3), round(float(pts[1][2]), 3))
    b = (round(float(pts[2][1]), 3), round(float(pts[2][2]), 3))
    wires.append((a, b)); union(a, b)

# ---------- labels
labels = collections.defaultdict(list)
for tag in ("label", "global_label", "hierarchical_label"):
    for l in find(d, tag):
        at = get(l, "at")
        pt = (round(float(at[1]), 3), round(float(at[2]), 3))
        labels[str(l[1])].append(pt)

ncs = set()
for n in find(d, "no_connect"):
    at = get(n, "at")
    ncs.add((round(float(at[1]), 3), round(float(at[2]), 3)))

# nodes = wire endpoints ∪ pin points ∪ label points
allpts = set()
for a, b in wires: allpts.add(a); allpts.add(b)
allpts |= set(pin_points) | {p for v in labels.values() for p in v} | ncs
for p in allpts: froot(p)

# ---------- T-junctions: KiCad connects a point that lies in the INTERIOR of a wire
def on_segment(p, a, b):
    (px, py), (ax, ay), (bx, by) = p, a, b
    if p == a or p == b:
        return False
    cross = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
    if abs(cross) > 1e-6:
        return False
    dot = (px - ax) * (bx - ax) + (py - ay) * (by - ay)
    if dot < 0:
        return False
    return dot <= (bx - ax) ** 2 + (by - ay) ** 2

tee = 0
for a, b in wires:
    for p in allpts:
        if on_segment(p, a, b):
            union(p, a); tee += 1
print(f"T-junctions (point on wire interior): {tee}")

# ---------- build nets
net_of = {}
for p in allpts:
    net_of.setdefault(froot(p), set()).add(p)

# join all points that carry the same label name
for nm, pts in labels.items():
    for p in pts[1:]:
        union(pts[0], p)

net_of = {}
for p in allpts:
    net_of.setdefault(froot(p), set()).add(p)

netname = {}
for nm, pts in labels.items():
    for p in pts:
        netname.setdefault(froot(p), set()).add(nm)

problems = []

# label conflicts (two different names on same electrical node)
for root, names in netname.items():
    if len(names) > 1:
        problems.append(f"NET MERGE: node has labels {sorted(names)}")

# dangling labels (label not on a wire endpoint)
wire_ends = set()
for a, b in wires: wire_ends.add(a); wire_ends.add(b)
for nm, pts in labels.items():
    for p in pts:
        if p not in wire_ends and p not in pin_points:
            problems.append(f"DANGLING LABEL {nm} at {p}")

# pins not connected to a wire, a label, or a no-connect
for p, names in pin_points.items():
    if p in ncs: continue
    if p in wire_ends: continue
    if any(p in v for v in labels.values()): continue
    if len(names) > 1: continue           # pin-to-pin direct
    problems.append(f"UNCONNECTED PIN {names} at {p}")

# wire endpoints that touch nothing
for p in wire_ends:
    if p in pin_points: continue
    if any(p in v for v in labels.values()): continue
    if sum(1 for a, b in wires if a == p or b == p) > 1: continue
    problems.append(f"DANGLING WIRE END at {p}")

# single-pin nets (by label name)
conn_count = collections.Counter()
for p, names in pin_points.items():
    conn_count[froot(p)] += len(names)
for root, names in netname.items():
    if conn_count.get(root, 0) < 2:
        problems.append(f"SINGLE-PIN NET {sorted(names)} ({conn_count.get(root,0)} pin(s))")

# off-grid check (1.27 mm)
for p in allpts:
    for c in p:
        if abs(round(c / 1.27) * 1.27 - c) > 1e-3:
            problems.append(f"OFF-GRID point {p}")
            break

print(f"\nsymbols placed: {sum(refs.values())}   distinct nets: {len(net_of)}")
print(f"named nets: {len(netname)}")
if problems:
    print(f"\n{len(problems)} issue(s):")
    for p in sorted(set(problems))[:80]:
        print("  -", p)
else:
    print("\nno structural issues found.")

# net summary
print("\n--- net pin counts ---")
rows = []
for root, names in netname.items():
    rows.append((sorted(names)[0], conn_count.get(root, 0)))
for nm, c in sorted(rows):
    print(f"  {nm:24s} {c}")
