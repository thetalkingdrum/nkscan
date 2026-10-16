#!/usr/bin/env python3
"""Check one nkscan thumbnail pass: do the 8Eh records line up with the image lines?

pass_check.py <nkscan log> <thumbnail.tiff nkscan wrote>

Prints the 8Eh record count, the filled image lines (the TIFF width), their difference,
and the perforation phase of the first line after each inter-frame gap. On a good pass
(Nikon Scan's) the difference is 0 and the phase stays within ~100 addresses down the roll.
"""
import os, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import address, perfs, log_bytes

log, tif = sys.argv[1], sys.argv[2]
f = open(tif, "rb").read()
ifd = struct.unpack("<I", f[4:8])[0]
tags = {}
for i in range(struct.unpack("<H", f[ifd:ifd + 2])[0]):
    t, ty, c, v = struct.unpack("<HHII", f[ifd + 2 + 12 * i: ifd + 14 + 12 * i])
    tags[t] = (ty, c, v)
w, h = tags[256][2], tags[257][2]
n = tags[273][1]
rd = lambda tag: struct.unpack(f"<{n}I", f[tags[tag][2]:tags[tag][2] + 4 * n]) if n > 1 else (tags[tag][2],)
raw = b"".join(f[o:o + c] for o, c in zip(rd(273), rd(279)))
img = np.frombuffer(raw, dtype="<u2").reshape(h, w, 3).astype(float)
prof = img[10:-10].mean(axis=(0, 2))

lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
rec = perfs([log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200][-1])
print(f"8Eh records {len(rec)}, filled image lines {w}, records - lines = {len(rec) - w:+d}")

thr = 0.5 * (np.median(prof) + np.percentile(prof, 99.5))
b, ends, i = prof > thr, [], 0
while i < len(b):
    if b[i]:
        j = i
        while j + 1 < len(b) and b[j + 1]:
            j += 1
        if j - i <= 12:
            ends.append(j)
        i = j + 1
    else:
        i += 1
ph = [(e + 1, address(*rec[e + 1]) % 6048) for e in ends if 600 < e < len(rec) - 1]
print("first line after each narrow gap -> perforation phase (address mod 6048):")
print(" ".join(f"{l}:{p}" for l, p in ph))
core = [p for _, p in ph]
med = np.median(core)
core = [p for p in core if abs(p - med) < 1500]
k = np.polyfit(range(len(core)), core, 1)[0] if len(core) > 2 else 0
print(f"phase trend {k:+.1f} addresses per frame (near 0 on a good pass; about -20 on the drifting nkscan pass)")
