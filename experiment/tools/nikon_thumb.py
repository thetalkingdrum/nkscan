"""Rebuild Nikon's thumbnail (image READs between the thumbnail SCAN and the next 8Eh) as rows=96 x cols=lines x 3, uint16."""
import sys, os, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from srec import records
trace, lo, hi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
buf = bytearray()
for r in records(trace):
    if r["seq"] > hi: break
    if r["seq"] >= lo and r["cdb"][0] == 0x28 and r["cdb"][2] == 0x00:
        buf += r["data"]
a = np.frombuffer(bytes(buf), dtype=">u2").reshape(-1, 3, 96)  # line, color, pixel
print("lines", a.shape[0], "max", a.max(), "min", a.min())
np.save(out, a)
