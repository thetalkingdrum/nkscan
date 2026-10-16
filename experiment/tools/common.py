"""Shared decoders for 8Eh / 8Fh / SET WINDOW payloads and nkscan log lines."""
import re

PITCH, PHASE, STEP = 756, 154, 7  # 4000 dpi grid (PerfoToRect)


def address(p, d, u):
    d &= 0x7F
    length = PHASE if d < 4 else PITCH - 4 * PHASE
    return p * PITCH + d * PHASE + min(u, length - 1) * STEP


def perfs(payload):
    """8Eh payload without the 6-byte READ header -> list of (perf, decimal|flag, pulse)."""
    plen = (payload[0] << 16) | (payload[1] << 8) | payload[2]
    assert payload[3] == 4
    total = min(plen + 3, len(payload) - (len(payload) - 4) % 4)
    out = []
    for i in range(4, total, 4):
        r = payload[i:i + 4]
        out.append(((r[0] << 8) | r[1], r[2], r[3]))
    return out


def table(payload):
    """8Fh payload (no READ header) -> list of (top, perf, decimal, pulse)."""
    n = payload[2]
    out = []
    for k in range(n):
        r = payload[4 + 8 * k:12 + 8 * k]
        out.append((int.from_bytes(r[0:4], "big"), int.from_bytes(r[4:6], "big"), r[6], r[7]))
    return out


def window(p):
    """58-byte SET WINDOW parameter list -> dict (window descriptor at offset 8)."""
    w = p[8:]
    be = lambda a, n: int.from_bytes(w[a:a + n], "big")
    return dict(id=w[0], xres=be(2, 2), yres=be(4, 2), x=be(6, 4), y=be(10, 4),
                w=be(14, 4), h=be(18, 4), bits=w[26], raw=w.hex(" "))


def log_bytes(line):
    """'recv [00, 8e, ...]' or 'data [..]' -> bytes"""
    m = re.findall(r"\[([0-9a-f, ]+)\]", line)
    return bytes(int(x, 16) for x in m[-1].split(","))
