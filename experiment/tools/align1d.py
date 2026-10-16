"""Map nkscan thumbnail lines onto Nikon thumbnail lines with 1-D line-profile correlation (per colour, concatenated)."""
import sys, numpy as np
from PIL import Image
nik = np.load(sys.argv[1]).astype(float) / 64.0            # line, color, px
nk = np.array(Image.open(sys.argv[2])).astype(float)          # px, line, color
# per-line features: mean of each colour over 4 bands across the film width
def feats_nik(a):
    return np.concatenate([a[:, c, 8 + 20*b: 28 + 20*b].mean(axis=1, keepdims=True) for c in range(3) for b in range(4)], axis=1)
def feats_nk(a):
    return np.concatenate([a[8 + 20*b: 28 + 20*b, :, c].mean(axis=0)[:, None] for c in range(3) for b in range(4)], axis=1)
fn, fk = feats_nik(nik), feats_nk(nk)
W = 120
def z(p):
    p = p - p.mean(axis=0); s = p.std(axis=0); s[s == 0] = 1; return p / s
out = []
for x in range(0, len(fk) - W, 30):
    a = z(fk[x:x + W])
    best = max(((z(fn[y:y + W]) * a).mean(), y) for y in range(max(0, x - 10), min(len(fn) - W, x + 70)))
    out.append((x + W // 2, best[1] + W // 2, best[0]))
out = np.array(out)
np.save(sys.argv[3], out)
for x, y, c in out[::5]:
    print(f"nk {int(x):5d} -> nikon {int(y):5d}  off {int(y-x):+4d}  r={c:.3f}")
good = out[out[:, 2] > 0.9]
p = np.polyfit(good[:, 0], good[:, 1] - good[:, 0], 1)
print("fit offset = %.5f * nk_line + %.2f   (n=%d)" % (p[0], p[1], len(good)))
