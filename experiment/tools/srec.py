#!/usr/bin/env python3
"""Parse NKDSBP2 proxy scsi_trace.bin (SREC records).

Usage:
  srec.py inventory <scsi_trace.bin>            one line per command
  srec.py dump <scsi_trace.bin> <seq> <out>     write one record's data payload
"""
import struct
import sys

HDR = struct.Struct("<4sIBBBBIIi16sI")
OPS = {
    0x00: "TEST UNIT READY", 0x03: "REQUEST SENSE", 0x12: "INQUIRY",
    0x15: "MODE SELECT", 0x16: "RESERVE", 0x17: "RELEASE", 0x1A: "MODE SENSE",
    0x1B: "SCAN", 0x1D: "SEND DIAG", 0x24: "SET WINDOW", 0x25: "GET WINDOW",
    0x28: "READ", 0x2A: "SEND", 0x3B: "WRITE BUFFER", 0xC1: "C1", 0xE0: "SET/EXECUTE(E0)",
    0xE1: "GET PARAM(E1)",
}


def records(path, with_data=True):
    with open(path, "rb") as f:
        while True:
            off = f.tell()
            h = f.read(HDR.size)
            if len(h) < HDR.size:
                return
            magic, seq, cdb_len, direction, srb, sense_len, flags, tlen, result, cdb, dlen = HDR.unpack(h)
            if magic != b"SREC":
                raise ValueError(f"bad magic at {off:#x}")
            if with_data:
                data = f.read(dlen)
            else:
                f.seek(dlen, 1)
                data = None
            sense = f.read(sense_len)
            yield dict(off=off, seq=seq, cdb=cdb[:cdb_len], dir=direction, srb=srb,
                       flags=flags, tlen=tlen, result=result, dlen=dlen, data=data, sense=sense)


def sense_str(r):
    s = r["sense"]
    if not s or len(s) < 14 or s[0] & 0x7F not in (0x70, 0x71):
        return ""
    if (s[2] & 0x0F) == 0 and s[12] == 0:
        return ""
    return f"sense={s[2] & 0x0F:02X}/{s[12]:02X}/{s[13]:02X}"


def line(r):
    c = r["cdb"]
    op = c[0]
    name = OPS.get(op, f"op{op:02X}")
    extra = ""
    if op in (0x28, 0x2A):
        dtc, q = c[2], (c[4] << 8) | c[5]
        ln = (c[6] << 16) | (c[7] << 8) | c[8]
        extra = f"dtc={dtc:02X} qual={q:04X} len={ln}"
    elif op in (0x24, 0x25):
        extra = f"len={(c[6] << 16) | (c[7] << 8) | c[8]}"
    elif op == 0xE0 or op == 0xE1:
        extra = f"code={c[2]:02X} len={(c[6] << 16) | (c[7] << 8) | c[8]}"
    d = {0: "-", 1: "IN", 2: "OUT"}.get(r["dir"], "?")
    return (f"{r['seq']:7d} {name:<16} {extra:<30} {d:<3} got={r['dlen']:<7} "
            f"srb={r['srb']:02X} {sense_str(r)}  cdb={c.hex(' ')}")


def main():
    cmd, path = sys.argv[1], sys.argv[2]
    if cmd == "inventory":
        last_tur = None
        n_tur = 0
        for r in records(path, with_data=False):
            if r["cdb"][0] == 0x00 and not sense_str(r):
                n_tur += 1
                continue
            if n_tur:
                print(f"{'':7} ... {n_tur} quiet TEST UNIT READY")
                n_tur = 0
            print(line(r))
    elif cmd == "dump":
        seq, out = int(sys.argv[3]), sys.argv[4]
        for r in records(path, with_data=False):
            if r["seq"] == seq:
                with open(path, "rb") as f:
                    f.seek(r["off"] + HDR.size)
                    open(out, "wb").write(f.read(r["dlen"]))
                print(line(r))
                return
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
