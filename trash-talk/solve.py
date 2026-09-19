"""TISC Trash Talk GTS client and Pokemon decoder."""
import argparse
import base64
import hashlib
import itertools
import struct
from pathlib import Path

import requests

BASE = "http://chals.tisc26.ctf.sg:31259"
OUT = Path(__file__).resolve().parent / "artifacts"


def encode_request(pid, payload, generation=4):
    if generation == 5:
        plain = struct.pack("<II", pid, len(payload)) + payload
        return base64.urlsafe_b64encode(
            struct.pack(">I", sum(plain) ^ 0x2DB842B2) + plain
        ).decode()
    plain = struct.pack("<I", pid) + payload
    checksum = sum(plain)
    state = checksum | (checksum << 16)
    encrypted = bytearray()
    for byte in plain:
        state = (state * 0x45 + 0x1111) & 0x7FFFFFFF
        encrypted.append(byte ^ ((state >> 16) & 0xFF))
    return base64.urlsafe_b64encode(
        struct.pack(">I", checksum ^ 0x4A3B2C1D) + encrypted
    ).decode()


def query(endpoint, payload, pid=123456789, generation=4):
    assert endpoint in ("search", "info", "get", "result", "exchange")
    prefix = "/pokemondpds" if generation == 4 else "/syachi2ds/web"
    salt = b"sAdeqWo3voLeC5r16DYv" if generation == 4 else b"HZEdGCzcGGLvguqUEKQN"
    url = BASE + prefix + "/worldexchange/" + endpoint + ".asp"
    with requests.Session() as session:
        session.headers.update({"Host": "gamestats2.gs.nintendowifi.net"})
        token = session.get(url, params={"pid": pid}, timeout=20)
        token.raise_for_status()
        if len(token.content) != 32:
            raise ValueError(f"Unexpected challenge: {token.content!r}")
        digest = hashlib.sha1(salt + token.content).hexdigest()
        response = session.get(url, params={
            "pid": pid, "hash": digest, "data": encode_request(pid, payload, generation)
        }, timeout=20)
        print(endpoint, response.status_code, len(response.content), response.content[:64].hex())
        response.raise_for_status()
        if generation == 5:
            body, footer = response.content[:-40], response.content[-40:]
            expected = hashlib.sha1(salt + base64.urlsafe_b64encode(body) + salt).hexdigest().encode()
            if footer != expected:
                raise ValueError("Gen V response signature mismatch")
            return body
        return response.content


def crypt_words(data, seed):
    out = bytearray()
    for (word,) in struct.iter_unpack("<H", data):
        seed = (seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
        out.extend(struct.pack("<H", word ^ (seed >> 16)))
    return bytes(out)


def decrypt_pokemon(data, generation=4):
    pid, _, checksum = struct.unpack_from("<IHH", data)
    raw = crypt_words(data[8:136], checksum)
    calculated = sum(struct.unpack("<64H", raw)) & 0xFFFF
    if calculated != checksum:
        raise ValueError(f"PKM checksum mismatch: {checksum:04x} != {calculated:04x}")
    order = list(itertools.permutations(range(4)))[((pid >> 13) & 31) % 24]
    blocks = [b""] * 4
    for position, destination in enumerate(order):
        blocks[destination] = raw[position * 32:(position + 1) * 32]
    end = 236 if generation == 4 else 220
    return data[:8] + b"".join(blocks) + crypt_words(data[136:end], pid) + data[end:]


def encrypt_pokemon(data, generation=4):
    data = bytearray(data)
    pid = struct.unpack_from("<I", data)[0]
    checksum = sum(struct.unpack_from("<64H", data, 8)) & 0xFFFF
    struct.pack_into("<H", data, 6, checksum)
    order = list(itertools.permutations(range(4)))[((pid >> 13) & 31) % 24]
    shuffled = b"".join(data[8 + block * 32:40 + block * 32] for block in order)
    end = 236 if generation == 4 else 220
    return bytes(data[:8]) + crypt_words(shuffled, checksum) + crypt_words(data[136:end], pid) + bytes(data[end:])


def name(data):
    chars = []
    for (c,) in struct.iter_unpack("<H", data):
        if c == 0xFFFF:
            break
        if 0x12B <= c <= 0x144:
            chars.append(chr(c - 0x12B + ord("A")))
        elif 0x145 <= c <= 0x15E:
            chars.append(chr(c - 0x145 + ord("a")))
        elif 0x121 <= c <= 0x12A:
            chars.append(chr(c - 0x121 + ord("0")))
        else:
            chars.append(f"[{c:04x}]")
    return "".join(chars)


def inspect(data, label):
    if len(data) % 292:
        print("Unexpected response:", repr(data))
        return
    OUT.mkdir(exist_ok=True)
    (OUT / f"{label}.bin").write_bytes(data)
    for index in range(len(data) // 292):
        record = data[index * 292:(index + 1) * 292]
        decoded = decrypt_pokemon(record)
        (OUT / f"{label}-{index}.decrypted.bin").write_bytes(decoded)
        print("Record", index, "species", struct.unpack_from("<H", decoded, 8)[0],
              "nickname", name(decoded[0x48:0x5E]), "OT", name(decoded[0x68:0x78]),
              "level", record[239], "country", record[286], "offerer", name(record[268:284]))
        for offset in range(0, 292, 16):
            chunk = decoded[offset:offset+16]
            print(f"{offset:03x} {chunk.hex(' '):47s} " + ''.join(chr(c) if 32 <= c < 127 else '.' for c in chunk))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--country", type=int, default=0)
    parser.add_argument("--species", type=int, default=137)
    parser.add_argument("--min-level", type=int, default=0)
    parser.add_argument("--max-level", type=int, default=0)
    parser.add_argument("--offline", type=Path)
    args = parser.parse_args()
    if args.offline:
        inspect(args.offline.read_bytes(), args.offline.stem)
    else:
        payload = struct.pack("<H6B", args.species, 3, args.min_level, args.max_level, 0, 7, args.country)
        data = query("search", payload)
        inspect(data, f"search-{args.species}-{args.country}-{args.min_level}-{args.max_level}")
