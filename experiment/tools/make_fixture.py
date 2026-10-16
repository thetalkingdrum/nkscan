#!/usr/bin/env python3
"""Build an nkscan framing fixture from a Nikon Scan SREC capture.

make_fixture.py <scsi_trace.bin> <out_dir> <frames>
Takes the thumbnail pass (image READs after the second thumbnail SCAN), the 8Eh READ after it,
and the 8Fh SEND that follows.
"""
import os, struct, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from srec import records
from common import window

def tiff(path, data):
    h, w, _ = data.shape
    body = data.tobytes()
    tags = [(256, 3, 1, w), (257, 3, 1, h), (258, 3, 3, None), (259, 3, 1, 1), (262, 3, 1, 2),
            (273, 4, 1, None), (277, 3, 1, 3), (278, 3, 1, h), (279, 4, 1, len(body)), (284, 3, 1, 1)]
    ifd_off = 8
    n = len(tags)
    bps_off = ifd_off + 2 + 12 * n + 4
    data_off = bps_off + 6
    with open(path, "wb") as f:
        f.write(b"II*\x00" + struct.pack("<I", ifd_off) + struct.pack("<H", n))
        for tag, typ, cnt, val in tags:
            if tag == 258:
                val = bps_off
            if tag == 273:
                val = data_off
            if typ == 3 and cnt == 1:
                f.write(struct.pack("<HHIHH", tag, typ, cnt, val, 0))
            else:
                f.write(struct.pack("<HHII", tag, typ, cnt, val))
        f.write(struct.pack("<I", 0) + struct.pack("<HHH", 16, 16, 16) + body)



def main():
    trace, out, frames = sys.argv[1], sys.argv[2], int(sys.argv[3])
    img, perf, bound, win, scans = bytearray(), None, None, None, 0
    for r in records(trace):
        c = r["cdb"]
        if c[0] == 0x24 and win is None:
            w = window(r["data"])
            if w["yres"] < 200 and w["h"] > 100000:
                win = w                                 # thumbnail window
        elif c[0] == 0x1B and win is not None and perf is None:
            scans += 1
        elif scans >= 2 and perf is None and c[0] == 0x28 and c[2] == 0x00:
            img += r["data"]
        elif scans >= 2 and perf is None and c[0] == 0x28 and c[2] == 0x8E and r["dlen"] > 6:
            perf = bytes(r["data"][6:])
        elif perf is not None and c[0] == 0x2A and c[2] == 0x8F:
            bound = bytes(r["data"])
            break

    px = 96
    a = np.frombuffer(bytes(img), dtype=">u2").reshape(-1, 3, px)      # line, colour, pixel
    lines = a.shape[0]
    rgb = np.ascontiguousarray(a.transpose(2, 0, 1)).astype("<u2")     # row=pixel, col=line, colour

    # Nikon reads the 8Eh record with the header's length, which is 6 bytes short of the record:
    # keep the whole records it received and make the parameter length say so
    whole = (len(perf) - 4) // 4
    claimed = ((perf[0] << 16) | (perf[1] << 8) | perf[2]) + 3
    fixed = (4 + 4 * whole - 3).to_bytes(3, "big") + perf[3:4] + perf[4:4 + 4 * whole]


    os.makedirs(out, exist_ok=True)
    tiff(os.path.join(out, "thumbnail.tiff"), rgb)
    open(os.path.join(out, "perforation.bin"), "wb").write(fixed)
    open(os.path.join(out, "boundary2.bin"), "wb").write(bound)
    open(os.path.join(out, "meta.txt"), "w").write(
        f"bits {win['bits']}\nfilm negative\nframes {frames}\nline_pitch {4000 // win['yres']}\n")
    print(f"lines={lines} window={win['xres']}dpi h={win['h']} 8Eh claimed={claimed} got={len(perf)} "
          f"records kept={whole} 8Fh={len(bound)} bytes ({bound[2]} frames)")


if __name__ == "__main__":
    main()
