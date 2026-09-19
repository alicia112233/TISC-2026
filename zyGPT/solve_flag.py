"""Reproduce authenticated ZyGPT flag recovery after identifying the live records."""
import hashlib
import json
import pathlib
import struct

import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

root = pathlib.Path(__file__).resolve().parent
result = json.loads((root / 'flag_result.json').read_text())
model_path = root / 'model/model.safetensors'
with model_path.open('rb') as f:
    header_size = struct.unpack('<Q', f.read(8))[0]
    header = json.loads(f.read(header_size))
data_start = 8 + header_size

embedding = np.memmap(model_path, mode='r', offset=data_start + header['model.embed_tokens.weight']['data_offsets'][0], dtype='<u2', shape=(151936, 2048))
signature_coordinates = [361, 553, 1152, 1289, 2014, 2039]
records = []
for row in sorted(result['rows']):
    record = struct.pack('>I', row) + embedding[row, signature_coordinates].tobytes()
    check = bytes([int(embedding[row, 959]) & 255, int(embedding[row, 1864]) & 255])
    assert hashlib.sha256(record).digest()[:2] == check, f'Bad record: {row}'
    records.append(record)

km = hashlib.sha256(b''.join(records)).digest()[:16]
key = hashlib.sha256(km + b'\x00').digest()
seed = hashlib.sha256(km + b'\x01').digest()
carrier = result['carrier']
baseline = np.fromfile(root / 'carriers' / (carrier + '.bin'), dtype='<u2')
leaked = np.memmap(model_path, mode='r', offset=data_start + header[carrier]['data_offsets'][0], dtype='<u2', shape=baseline.shape)
exponent = (baseline >> 7) & 255
eligible = np.flatnonzero((exponent != 0) & (exponent != 255))
stream = hashlib.shake_256(seed)
count = 640
while True:
    random_words = np.frombuffer(stream.digest(8 * count), dtype='>u8')
    positions = list(dict.fromkeys((random_words % len(eligible)).tolist()))[:608]
    if len(positions) == 608:
        break
    count *= 2
indices = eligible[positions]
bits = ((baseline[indices] ^ leaked[indices]) & 1).astype(np.uint8)
payload = np.packbits(bits, bitorder='big').tobytes()
plaintext = AESGCM(key).decrypt(payload[:12], payload[12:], None)
assert len(plaintext) == 48
flag = plaintext.rstrip(b'\0').decode('ascii')
assert flag.startswith('TISC{') and flag.endswith('}')
print(flag)
print('Verified: all record checksums and AES-256-GCM authentication tag.')
