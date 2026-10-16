"""Find bright inter-frame gaps in a thumbnail column profile and relate them to frame-start lines.
gaps_generic.py nikon <thumb.npy> <8E payload> <8F payload>
gaps_generic.py nkscan <tiff> <nkscan log>"""
import sys, os, re, numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from resample import resample

def gaps(prof, w0=4):
    """All bright runs: threshold halfway between median and p99."""
    thr = 0.5 * (np.median(prof) + np.percentile(prof, 99.5))
    b = prof > thr
    runs = []; i = 0
    while i < len(b):
        if b[i]:
            j = i
            while j + 1 < len(b) and b[j + 1]: j += 1
            runs.append((i, j)); i = j + 1
        else: i += 1
    return runs

mode = sys.argv[1]
if mode == "nikon":
    a = np.load(sys.argv[2]).astype(float)        # line, color, pixel
    prof = a[:, :, 10:-10].mean(axis=(1, 2))
    rec = perfs(open(sys.argv[3], "rb").read()[6:])
    tops = [t[0] for t in table(open(sys.argv[4], "rb").read())]
    kept = resample(rec, 41)
    ad = [address(*rec[i]) for i in kept]
    starts = [next(j + 1 for j, x in enumerate(ad) if x == t) for t in tops]
else:
    from PIL import Image
    a = np.array(Image.open(sys.argv[2])).astype(float)
    prof = a[10:-10].mean(axis=(0, 2))
    lines = open(sys.argv[3], errors="replace").read().splitlines()
    rec = perfs([log_bytes(l)[6:] for l in lines if "DEBUG recv [00, 8e" in l and len(l) > 200][-1])
    starts = [int(m) for m in re.findall(r"\((\d+), \d+\)", [l for l in lines if "frames on the resampled" in l][-1])]
    kept = resample(rec, 41)
    ad = [address(*rec[i]) for i in kept]

g = gaps(prof)
g = [x for x in g if x[1] - x[0] <= 12]  # narrow = inter-frame gaps
ga = [(s, e, ad[min(e + 1, len(ad) - 1)]) for s, e in g]  # address of first line after the gap
print(f"{len(g)} narrow gaps; spacing in lines:", np.diff([e for _, e, _ in ga]).tolist())
print("gap-end address mod 6048 (perf phase of the first line after each gap):")
print([ (x % 6048) for *_, x in ga])
print("frame starts minus nearest gap end (lines):",
      [min((s - (e + 1) for _, e, _ in ga), key=abs) for s in starts])
