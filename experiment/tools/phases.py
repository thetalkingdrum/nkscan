"""Per-frame table addresses and their perforation phase for Nikon and nkscan runs."""
import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
nik = table(open(sys.argv[1], "rb").read())
runs = {}
for p in sys.argv[2:]:
    lines = open(p, errors="replace").read().splitlines()
    runs[os.path.basename(p)] = table([log_bytes(l) for l in lines if "cdb for send 8f" in l][0])
    rec = perfs([log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200][-1] if True else None)
    raw = collections.Counter(r[0] for r in rec)
    print(os.path.basename(p), "8Eh records", len(rec), "lines/perf", sorted(collections.Counter(raw.values()).items()),
          "fine SET WINDOW Y:", len(set(re.findall(r"setting window id=1 window.origin=\(0, (\d+)\) window.size=\(3946, 5959\)", "\n".join(lines)))))
names = list(runs)
print("\nframe | Nikon addr phase | " + " | ".join(f"{n[:18]:>18} addr  dPhase" for n in names))
for i in range(40):
    a = nik[i][0]
    row = f"{i+1:5d} | {a:7d} {a % 6048:5d} | "
    row += " | ".join(f"{runs[n][i][0]:7d} {runs[n][i][0]-a:+6d} ({runs[n][i][0]-a:+5d}a={(runs[n][i][0]-a)*25.4/4000:+.2f}mm)" for n in names)
    print(row)
