"""Recover the Trash Talk flag; use --offline to replay captured trades."""
import argparse
import re
import struct

from solve import OUT, decrypt_pokemon, encrypt_pokemon, query


def gen5_name(text, size):
    return (text.encode("utf-16le") + b"\xff\xff").ljust(size, b"\0")


def buizel_offer():
    pokemon = bytearray(220)
    struct.pack_into("<I", pokemon, 0, 0x123456C8)
    struct.pack_into("<H", pokemon, 8, 418)
    struct.pack_into("<HH", pokemon, 12, 12345, 54321)
    struct.pack_into("<I", pokemon, 16, 35 ** 3)
    pokemon[0x14:0x18] = bytes([255, 33, 0, 2])
    struct.pack_into("<H", pokemon, 0x28, 33)  # Tackle
    pokemon[0x30] = 35
    struct.pack_into("<I", pokemon, 0x38, 0x3FFFFFFF)
    pokemon[0x40] = 0  # male
    pokemon[0x48:0x5E] = gen5_name("Buizel", 22)
    pokemon[0x5F] = 21  # Black
    pokemon[0x68:0x78] = gen5_name("SOLVER", 16)
    pokemon[0x7B:0x7E] = bytes([26, 9, 19])
    struct.pack_into("<H", pokemon, 0x80, 8)
    pokemon[0x83] = 4  # Poke Ball
    pokemon[0x84] = 35  # met level
    pokemon[0x8C] = 35
    record = encrypt_pokemon(pokemon, generation=5) + bytes(16)
    metadata = bytearray(60)
    struct.pack_into("<HBB", metadata, 0, 418, 1, 35)
    struct.pack_into("<I", metadata, 28, 123456789)
    struct.pack_into("<HH", metadata, 32, 12345, 54321)
    metadata[36:52] = gen5_name("SOLVER", 16)
    metadata[56:58] = bytes([21, 2])
    return record + metadata


def targets(data):
    for offset in range(0, len(data), 296):
        record = data[offset:offset + 296]
        decoded = decrypt_pokemon(record, generation=5)
        if struct.unpack_from("<H", decoded, 8)[0] != 233:
            continue
        # The clue specifies a little-endian PID XORed with the integer K.
        # XORing with bytes.fromhex("C3236F27") reverses the key incorrectly.
        yield struct.unpack_from("<I", decoded, 0x5A)[0] ^ 0xC3236F27


def recover_flag(records):
    fragments = []
    for record in records:
        if len(record) != 296:
            raise ValueError(f"Trade failed: {record!r}")
        decoded = decrypt_pokemon(record, generation=5)
        assert struct.unpack_from("<H", decoded, 8)[0] == 474  # Porygon-Z
        assert decoded[0x48:0x4E] == b"P\0Z\0\xff\xff"
        fragment = bytes(b ^ decoded[i % 4]
                         for i, b in enumerate(decoded[0x4E:0x5E]))
        timestamp = struct.unpack_from("<Q", decoded, 0xF8)[0]
        fragments.append((timestamp, fragment.rstrip(b"\0")))
        print("Fragment:", repr(fragment))
    flag = b"".join(fragment for _, fragment in sorted(fragments)).decode("ascii")
    if not re.fullmatch(r"TISC\{[^{}]+\}", flag):
        raise ValueError(f"Incomplete flag: {flag!r}")
    return flag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    data = (OUT / "porygon2-all.bin").read_bytes()
    records = []
    if not args.offline:
        offer = buizel_offer()
        assert len(offer) == 296
        (OUT / "buizel-offer.bin").write_bytes(offer)
        # Establish the search state expected by GTS before exchanging.
        query("search", struct.pack("<H6B", 233, 3, 0, 0, 0, 7, 0), generation=5)
    for target in targets(data):
        print("Target PID", target)
        capture = OUT / f"exchange-{target}.bin"
        if args.offline:
            result = capture.read_bytes()
        else:
            payload = (offer + struct.pack("<I", target) + bytes(128)
                       + struct.pack("<I", 0x80000000))
            result = query("exchange", payload, generation=5)
            capture.write_bytes(result)
        records.append(result)
    flag = recover_flag(records)
    (OUT.parent / "flag.txt").write_text(flag + "\n", encoding="utf-8")
    print(flag)
