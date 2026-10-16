import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from resample import resample
rec = perfs(open(sys.argv[1], "rb").read()[6:])
sent = table(open(sys.argv[2], "rb").read())
kept = resample(rec, 41)
print("records", len(rec), "kept", len(kept))
raw = collections.Counter(r[0] for r in rec)
print("raw lines/perf:", sorted(collections.Counter(raw.values()).items()))
short = [p for p, c in sorted(raw.items()) if c == 17]
print("17-line perfs:", short)
ad = [address(*rec[i]) for i in kept]
# For each Nikon entry, find kept lines whose record address == top
print(" # top       lines(kept idx+1) matching")
prev = None
for i, t in enumerate(sent, 1):
    m = [j + 1 for j, a in enumerate(ad) if a == t[0]]
    d = (m[0] - prev) if (m and prev) else None
    print(f"{i:2d} {t[0]:7d} {m[:3]} step={d}")
    prev = m[0] if m else prev
