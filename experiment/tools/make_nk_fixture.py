#!/usr/bin/env python3
"""Build an nkscan framing fixture from nkscan's own thumbnail-only run.

make_nk_fixture.py <nkscan log> <thumbnail.tiff written by nkscan> <out_dir> <frames>
The TIFF holds the pass stretched to 16 bits and cut at the last filled column; both are undone.
boundary2.bin is the 8Fh table nkscan sent (there is no Nikon table for this pass).
"""
import os, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import log_bytes
from make_fixture import tiff  # noqa: E402  (reuses the writer)

log, tif, out, frames = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
f = open(tif, "rb").read()
ifd = struct.unpack("<I", f[4:8])[0]
tags = {}
for i in range(struct.unpack("<H", f[ifd:ifd + 2])[0]):
    t, ty, c, v = struct.unpack("<HHII", f[ifd + 2 + 12 * i: ifd + 14 + 12 * i])
    tags[t] = (ty, c, v)
w, h = tags[256][2], tags[257][2]
assert tags[259][2] == 1, "compressed"
offs = struct.unpack(f"<{tags[273][1]}I", f[tags[273][2]:tags[273][2] + 4 * tags[273][1]])
cnts = struct.unpack(f"<{tags[279][1]}I", f[tags[279][2]:tags[279][2] + 4 * tags[279][1]])
raw = b"".join(f[o:o + c] for o, c in zip(offs, cnts))
v16 = np.frombuffer(raw, dtype="<u2").reshape(h, w, 3)
top = 16383
table = np.array([(min(v, top) * 65535 + top // 2) // top for v in range(top + 1)], dtype=np.uint32)
v14 = np.searchsorted(table, v16).astype(np.uint16)
assert (table[v14] == v16).all(), "not a 14-bit stretch"
lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
rows = [l for l in lines if "thumbnail rows=" in l][-1]
pass_lines = int(rows.split("cols=")[1].split()[0])
full = np.zeros((h, pass_lines, 3), dtype="<u2")
full[:, :w] = v14
perf = [log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200][-1]
total = ((perf[0] << 16) | (perf[1] << 8) | perf[2]) + 3
bound = [log_bytes(l) for l in lines if "cdb for send 8f" in l][-1]
os.makedirs(out, exist_ok=True)
tiff(os.path.join(out, "thumbnail.tiff"), full)
open(os.path.join(out, "perforation.bin"), "wb").write(bytes(perf[:total]))
open(os.path.join(out, "boundary2.bin"), "wb").write(bytes(bound))
open(os.path.join(out, "meta.txt"), "w").write(f"bits 14\nfilm negative\nframes {frames}\nline_pitch 41\n")
print(f"tiff {w}x{h} -> {pass_lines} lines, 8Eh {total} bytes ({(total - 4) // 4} records), 8Fh {len(bound)} bytes")
