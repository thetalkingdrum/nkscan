import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from resample import resample
lines = open(sys.argv[1], errors="replace").read().splitlines()
rec = perfs([log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200][-1])
sent = table([log_bytes(l) for l in lines if "cdb for send 8f" in l][-1])
found = [tuple(map(int, m)) for m in re.findall(r"\((\d+), (\d+)\)", [l for l in lines if "frames on the resampled" in l][-1])]
kept = resample(rec, 41)
print("records", len(rec), "kept", len(kept))
# lines per perforation in kept
cnt = collections.Counter(rec[i][0] for i in kept)
print("kept lines/perf histogram:", collections.Counter(cnt.values()))
raw = collections.Counter(r[0] for r in rec)
print("raw lines/perf histogram:", collections.Counter(raw.values()))
ok = 0
for i, ((s, e), t) in enumerate(zip(found, sent), 1):
    r = rec[kept[min(max(s, 1), len(kept)) - 1]]
    ok += (address(*r) == t[0])
print("table entries reproduced:", ok, "/", len(sent))
# address per resampled line
ad = [address(*rec[i]) for i in kept]
for a, b in [(1000, 1144), (3000, 3144), (5000, 5144)]:
    print(f"addr[{b}]-addr[{a}] =", ad[b] - ad[a])
