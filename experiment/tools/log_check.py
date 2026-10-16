#!/usr/bin/env python3
"""Judge one nkscan run from its log alone (a --log trace capture; debug also works).

log_check.py <nkscan log>

Prints the experiment line (8Eh records vs filled thumbnail lines) and the perforation
phase (address mod 6048) of each frame nkscan sent in its 8Fh table. A good pass, like
Nikon Scan's: surplus 0 and a phase spread of about 100-130 from frame 6 on.
nkscan 0.14.1 stock on this roll: surplus +20 and a spread of about 800, falling steadily.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import log_bytes, table

lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
for l in lines:
    if "experiment:" in l:
        print(l.split(" INFO ", 1)[-1])
sends = [log_bytes(l) for l in lines if "cdb for send 8f" in l]
if not sends:
    sys.exit("no 8Fh SEND in this log (was it captured at --log trace?)")
tops = [t[0] for t in table(sends[-1])]
ph = [t % 6048 for t in tops[5:]]
print(f"{len(tops)} frames; phase from frame 6: {ph}")
print(f"phase spread {max(ph) - min(ph)}  (good: ~100-130; stock nkscan on this roll: ~800)")
