#!/usr/bin/env python3
"""Compare Nikon's 8Fh SEND with nkscan's, and both 8Eh passes.

compare_tables.py <scsi_trace.bin> <nkscan thumbnail log>
"""
import sys
sys.path.insert(0, __import__("os").path.dirname(__file__))
from common import address, perfs, table, window, log_bytes
from srec import records

trace, nklog = sys.argv[1], sys.argv[2]

# --- Nikon
nik = {}
wins = []
for r in records(trace):
    c = r["cdb"]
    if c[0] == 0x28 and c[2] == 0x8E and r["dlen"] > 6:
        nik.setdefault("8e", []).append((r["seq"], r["data"][6:]))
    if c[0] == 0x2A and c[2] == 0x8F:
        nik.setdefault("8f_send", []).append((r["seq"], r["data"]))
    if c[0] == 0x28 and c[2] == 0x8F:
        nik.setdefault("8f_read", []).append((r["seq"], r["data"][6:]))
    if c[0] == 0x24:
        wins.append((r["seq"], window(r["data"])))

# --- nkscan
lines = open(nklog, encoding="utf-8", errors="replace").read().splitlines()
nk8e = [log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200]
nk8f = [log_bytes(l) for l in lines if "cdb for send 8f" in l]
nk8f_read = [log_bytes(l)[6:] for l in lines if "DEBUG recv [8f" in l and len(l) > 200]

print("Nikon 8Eh reads:", [(s, len(perfs(d))) for s, d in nik["8e"]])
print("nkscan 8Eh reads:", [len(perfs(d)) for d in nk8e])
print("Nikon 8Fh sends:", [(s, len(d)) for s, d in nik["8f_send"]], "reads:", [(s, len(d)) for s, d in nik.get("8f_read", [])])
print("nkscan 8Fh sends:", [len(d) for d in nk8f])

print("\nNikon SET WINDOWs (id, res, y, h):")
for s, w in wins:
    print(f"  {s:6d} id={w['id']} res={w['xres']}/{w['yres']} x={w['x']} y={w['y']} w={w['w']} h={w['h']} bits={w['bits']}")
    if s > 1400:
        break

nt = table(nik["8f_send"][0][1])
kt = table(nk8f[-1])
print(f"\n{'#':>3} | {'Nikon top':>9} {'p':>3} {'d':>4} {'u':>3} {'addr':>6} | {'nkscan top':>10} {'p':>3} {'d':>4} {'u':>3} {'addr':>6} | {'d_addr':>6} {'d_mm':>6}")
for i, (a, b) in enumerate(zip(nt, kt), 1):
    aa, ba = address(*a[1:]), address(*b[1:])
    print(f"{i:3d} | {a[0]:9d} {a[1]:3d} {a[2]:#04x} {a[3]:3d} {aa:6d} | {b[0]:10d} {b[1]:3d} {b[2]:#04x} {b[3]:3d} {ba:6d} | {ba-aa:6d} {(ba-aa)*25.4/4000:6.2f}")
