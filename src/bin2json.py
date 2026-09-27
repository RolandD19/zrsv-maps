#!/usr/bin/env python3
import argparse, json, struct
from pathlib import Path

MOD = 0x10000

class ZSReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def tell(self): return self.pos
    def seek(self, pos): self.pos = pos

    def _read(self, n):
        if self.pos + n > len(self.data):
            raise EOFError(f"Need {n} bytes at 0x{self.pos:x}, file size is 0x{len(self.data):x}")
        b = self.data[self.pos:self.pos+n]
        self.pos += n
        return b

    def u8(self):  return struct.unpack("<B", self._read(1))[0]
    def u16(self): return struct.unpack("<H", self._read(2))[0]
    def u32(self): return struct.unpack("<I", self._read(4))[0]
    def u64(self): return struct.unpack("<Q", self._read(8))[0]
    def f64(self): return struct.unpack("<d", self._read(8))[0]

    def string(self):
        end = self.data.find(b"\x00", self.pos)
        if end < 0:
            raise ValueError(f"Unterminated string at 0x{self.pos:x}")
        s = self.data[self.pos:end].decode("utf-8")
        self.pos = end + 1
        return s

def resolved_wrapped_offset(stored_u16, minimum_absolute):
    """Smallest absolute offset >= minimum_absolute whose low 16 bits equal stored_u16."""
    base = minimum_absolute & ~0xFFFF
    candidate = base | stored_u16
    if candidate < minimum_absolute:
        candidate += MOD
    return candidate

def parse(path):
    raw = Path(path).read_bytes()
    r = ZSReader(raw)

    fmt = r.string()
    if fmt != "ZS":
        raise ValueError(f"Bad header {fmt!r}")

    version = r.u64()
    building_name = r.string()
    header_string = r.string()
    try:
        header_json = json.loads(header_string)
    except Exception:
        header_json = None

    chunk_count = r.u16()
    out = {
        "format": fmt,
        "version": version,
        "building_name": building_name,
        "header_string": header_string,
        "header_json": header_json,
        "chunk_count": chunk_count,
        "chunks": []
    }

    for idx in range(chunk_count):
        file_offset = r.tell()
        name = r.string()
        stored_end = r.u16()
        payload_offset = r.tell()

        data = {}

        if name == "inst":
            count = r.u16()
            items = []
            for _ in range(count):
                items.append({"x": r.f64(), "y": r.f64(), "object": r.string()})
            data = {"count": count, "items": items}

        elif name == "tele":
            count = r.u16()
            items = [{"x": r.f64(), "y": r.f64()} for _ in range(count)]
            data = {"count": count, "items": items}

        elif name == "decor":
            count = r.u16()
            items = [{"x": r.f64(), "y": r.f64(), "decor_id": r.u16()} for _ in range(count)]
            data = {"count": count, "items": items}

        elif name == "fence grid":
            count = r.u16()
            fence_names = {1:"wood_big", 2:"concrete1", 3:"military"}
            items = []
            for _ in range(count):
                x, y, fid = r.u16(), r.u16(), r.u8()
                item = {"x": x, "y": y, "fence_id": fid}
                if fid in fence_names:
                    item["fence_name"] = fence_names[fid]
                items.append(item)
            data = {"count": count, "items": items}

        elif name == "grid":
            grid = r.string()
            count = r.u16()
            items = [{"x": r.u16(), "y": r.u16(), "value": r.u16()} for _ in range(count)]
            data = {"grid": grid, "count": count, "items": items}

        elif name == "grid_map":
            count = r.u16()
            items = [{"x": r.u16(), "y": r.u16(), "tile": r.u32()} for _ in range(count)]
            data = {"count": count, "items": items}

        elif name == "water":
            count = r.u16()
            items = [{"x": r.u16(), "y": r.u16(), "tile": r.u32()} for _ in range(count)]
            data = {"count": count, "items": items}

        elif name == "grid + tiles":
            grid = r.string()
            count = r.u16()
            grid_value = r.u16()
            items = [{"x": r.u16(), "y": r.u16(), "tile": r.u32()} for _ in range(count)]
            data = {"grid": grid, "count": count, "grid_value": grid_value, "items": items}

        elif name == "tiles":
            layer = r.string()
            scale = r.u8()
            count = r.u16()
            items = [{"x": r.u16(), "y": r.u16(), "tile": r.u32()} for _ in range(count)]
            data = {"layer": layer, "scale": scale, "count": count, "items": items}

        else:
            # The stored field is u16, but the GameMaker serializer writes buffer_tell()
            # into it even when the absolute offset exceeds 65535. GameMaker truncates
            # to the low 16 bits. Resolve to the next matching absolute position.
            payload_end = resolved_wrapped_offset(stored_end, payload_offset)
            if payload_end > len(raw) - 8:
                raise ValueError(
                    f"Unknown chunk {name!r}: wrapped end resolves to 0x{payload_end:x}, "
                    f"outside file (size 0x{len(raw):x})"
                )
            data = {"raw_payload_hex": raw[payload_offset:payload_end].hex()}
            r.seek(payload_end)

        payload_end = r.tell()
        terminator = r.u64()
        if terminator != 0:
            raise ValueError(
                f"Chunk {idx} {name!r}: expected zero u64 terminator at 0x{payload_end:x}, "
                f"got 0x{terminator:016x}"
            )
        actual_end = r.tell()

        out["chunks"].append({
            "index": idx,
            "name": name,
            "file_offset": file_offset,
            "stored_end_offset": stored_end,
            "payload_offset": payload_offset,
            "payload_end_offset": payload_end,
            "actual_end_offset": actual_end,
            # Critical: stored_end is only the LOW 16 BITS of the absolute pre-terminator offset.
            "stored_end_matches": ((payload_end & 0xFFFF) == stored_end),
            "data": data
        })

    out["file_size"] = len(raw)
    out["bytes_remaining_after_chunks"] = len(raw) - r.tell()
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_bin")
    ap.add_argument("output_json", nargs="?")
    args = ap.parse_args()

    src = Path(args.input_bin)
    dst = Path(args.output_json) if args.output_json else src.with_suffix(".json")
    obj = parse(src)
    dst.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(dst)

if __name__ == "__main__":
    main()
