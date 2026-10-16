"""Line-for-line Python port of nkscan v0.14.1 src/scan/boundary/perforation/resample.rs (4000 dpi)."""
from common import PITCH


def next_perf(rec, s):
    n = len(rec)
    if s >= n:
        return s + 1
    v = rec[s][0]
    for i in range(s + 1, n):
        if rec[i][0] > v:
            return i
    return max(n, s + 1)


def next_phase(rec, s):
    n = len(rec)
    if s >= n:
        return s + 1
    d = rec[s][1] & 0x7F
    for i in range(s + 1, n):
        if rec[i][1] & 0x7F != d:
            return i
    return max(n, s + 1)


def thin(out, n, s, e, drop):
    if drop < 1:
        out.extend(range(s, min(e, n)))
        return
    for i in range(drop):
        left = e - (s + 1)
        keep = max(int(left / (drop - i)), 0) if left >= 0 else max(-((-left) // (drop - i)), 0)
        out.extend(l for l in range(s + 1, s + 1 + keep) if l < n)
        s += 1 + keep


def resample(rec, line_pitch):
    n = len(rec)
    k = int(0.5 + PITCH / max(line_pitch, 1))
    out = []
    if n == 0:
        return out
    perf = lambda i: rec[i][0] if i < n else None
    p1 = next_perf(rec, 0)
    p2 = next_perf(rec, p1)
    reference = []
    thin(reference, n, p1, p2, p2 - p1 - k - 1)
    kept = [rec[i] for i in reference]
    lengths = [0] * 5
    phases = 0
    start = 0
    for j in range(5):
        end = next_phase(kept, start)
        lengths[j] = end - start
        phases += 1
        if len(kept) <= end:
            break
        start = end
    leading = 0
    i = 0
    while i < n and perf(i) == perf(0):
        i = next_phase(rec, i)
        leading += 1
    first = next_phase(rec, 0)
    out.extend(range(0, first))
    cur = first
    j = phases - leading
    while True:
        j += 1
        if phases <= j:
            break
        e = next_phase(rec, cur)
        target = lengths[j] if j >= 0 else e - cur
        thin(out, n, cur, e, e - cur - target)
        cur = e
        if perf(e) != perf(0):
            break
    out.extend(reference)
    c = next_perf(rec, cur)
    while True:
        e = next_perf(rec, c)
        if not (e < n and not (rec[e][1] & 0x80)):
            break
        thin(out, n, c, e, e - c - k - 1)
        c = e
    out.extend(range(c, n))
    return out
