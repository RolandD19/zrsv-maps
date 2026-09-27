#!/usr/bin/env python3
import argparse, json, struct
from pathlib import Path

class ZSWriter:
    def __init__(self):
        self.buf = bytearray()

    def tell(self): return len(self.buf)
    def bytes(self, b): self.buf.extend(b)

    def u8(self, v):  self.bytes(struct.pack("<B", int(v) & 0xFF))
    def u16(self, v): self.bytes(struct.pack("<H", int(v) & 0xFFFF))
    def u32(self, v): self.bytes(struct.pack("<I", int(v) & 0xFFFFFFFF))
    def u64(self, v): self.bytes(struct.pack("<Q", int(v) & 0xFFFFFFFFFFFFFFFF))
    def f64(self, v): self.bytes(struct.pack("<d", float(v)))

    def string(self, s):
        self.bytes(str(s).encode("utf-8") + b"\x00")

    def patch_u16(self, pos, v):
        # This intentionally matches GameMaker's behavior: buffer_poke(..., buffer_u16,
        # buffer_tell(...)) truncates offsets > 65535 to their low 16 bits.
        self.buf[pos:pos+2] = struct.pack("<H", int(v) & 0xFFFF)

def write_chunk(w, chunk):
    name = chunk["name"]
    data = chunk.get("data", {})

    w.string(name)
    end_patch_pos = w.tell()
    w.u16(0)

    items = data.get("items", [])

    if name == "inst":
        w.u16(len(items))
        for it in items:
            w.f64(it["x"]); w.f64(it["y"]); w.string(it["object"])

    elif name == "tele":
        w.u16(len(items))
        for it in items:
            w.f64(it["x"]); w.f64(it["y"])

    elif name == "decor":
        w.u16(len(items))
        for it in items:
            w.f64(it["x"]); w.f64(it["y"]); w.u16(it["decor_id"])

    elif name == "fence grid":
        w.u16(len(items))
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u8(it["fence_id"])

    elif name == "grid":
        w.string(data["grid"])
        w.u16(len(items))
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u16(it["value"])

    elif name == "grid_map":
        w.u16(len(items))
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u32(it["tile"])

    elif name == "water":
        w.u16(len(items))
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u32(it["tile"])

    elif name == "grid + tiles":
        w.string(data["grid"])
        w.u16(len(items))
        w.u16(data["grid_value"])
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u32(it["tile"])

    elif name == "tiles":
        w.string(data["layer"])
        w.u8(data["scale"])
        w.u16(len(items))
        for it in items:
            w.u16(it["x"]); w.u16(it["y"]); w.u32(it["tile"])

    else:
        raw_hex = data.get("raw_payload_hex")
        if raw_hex is None:
            raise ValueError(f"Unknown chunk {name!r} has no raw_payload_hex")
        w.bytes(bytes.fromhex(raw_hex))

    # The serializer patches the u16 BEFORE writing the trailing u64(0).
    # It stores only the low 16 bits when the absolute offset exceeds 65535.
    chunk_end = w.tell()
    w.patch_u16(end_patch_pos, chunk_end)
    w.u64(0)

def build(obj):
    w = ZSWriter()
    w.string(obj.get("format", "ZS"))
    w.u64(obj.get("version", 1))
    w.string(obj["building_name"])

    header_string = obj.get("header_string")
    if header_string is None:
        header_string = json.dumps(obj.get("header_json", {}), separators=(",", ":"))
    w.string(header_string)

    chunks = obj.get("chunks", [])
    w.u16(len(chunks))

    for chunk in chunks:
        write_chunk(w, chunk)

    return bytes(w.buf)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_json")
    ap.add_argument("output_bin", nargs="?")
    args = ap.parse_args()

    src = Path(args.input_json)
    dst = Path(args.output_bin) if args.output_bin else src.with_suffix(".bin")
    obj = json.loads(src.read_text(encoding="utf-8"))
    dst.write_bytes(build(obj))
    print(dst)

if __name__ == "__main__":
    main()
