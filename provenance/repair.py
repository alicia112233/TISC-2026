"""Repair the Rich header and PE linker version without rebuilding the EXE."""
from pathlib import Path
import argparse
import struct


def rol32(value, shift):
    shift %= 32
    return ((value << shift) | (value >> ((32 - shift) % 32))) & 0xFFFFFFFF


def repair(data, build=35207, linker_minor=44):
    data = bytearray(data)
    pe_offset = struct.unpack_from('<I', data, 0x3C)[0]
    rich = data.index(b'Rich', 0x40, pe_offset)
    old_key = struct.unpack_from('<I', data, rich + 4)[0]
    start = data.index(struct.pack('<I', 0x536E6144 ^ old_key), 0x40, rich)
    words = [struct.unpack_from('<I', data, off)[0] ^ old_key
             for off in range(start, rich, 4)]
    for i in range(4, len(words), 2):
        if words[i] >> 16 != 1:
            words[i] = (words[i] & 0xFFFF0000) | build
    key = start
    for i in range(start):
        if not 0x3C <= i < 0x40:
            key = (key + rol32(data[i], i)) & 0xFFFFFFFF
    for i in range(4, len(words), 2):
        key = (key + rol32(words[i], words[i + 1])) & 0xFFFFFFFF
    for i, word in enumerate(words):
        struct.pack_into('<I', data, start + i * 4, word ^ key)
    struct.pack_into('<I', data, rich + 4, key)
    data[pe_offset + 24 + 2] = 14
    data[pe_offset + 24 + 3] = linker_minor
    return bytes(data), (start, rich + 8), key


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=int, default=35207)
    parser.add_argument('--linker-minor', type=int, default=44)
    args = parser.parse_args()
    folder = Path(__file__).resolve().parent
    original = (folder / 'challenge.exe').read_bytes()
    fixed, (start, end), key = repair(original, args.build, args.linker_minor)
    pe_offset = struct.unpack_from('<I', original, 0x3C)[0]
    allowed = set(range(start, end)) | {pe_offset + 26, pe_offset + 27}
    assert len(original) == len(fixed)
    assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(original, fixed)))
    out = folder / 'repaired.exe'
    out.write_bytes(fixed)
    print(f'{out}: build={args.build}, key={key:#010x}, modified range={start:#x}:{end:#x}')
