import hashlib
import json
import math
from pathlib import Path

record = bytes(json.loads(Path('harbour-dump.json').read_text())['chroma'])
for offset in range(64, 1024, 64):
    record += bytes(json.loads(Path('dump-' + str(offset) + '.json').read_text())['chroma'])
record = record[:990].decode()
Path('harbour-record.txt').write_text(record)
print(record)
fields = dict(line.split('=', 1) for line in record.splitlines() if '=' in line)
n, e, c = (int(fields[key]) for key in ['rsa_n', 'rsa_e', 'rsa_c'])
a = math.isqrt(n)
if a * a < n:
    a += 1
steps = 0
while True:
    b2 = a * a - n
    b = math.isqrt(b2)
    if b * b == b2:
        break
    a += 1
    steps += 1
    if steps > 1000000:
        raise RuntimeError('Fermat factorization exceeded expected close-prime range')
p, q = a - b, a + b
assert p * q == n
d = pow(e, -1, (p - 1) * (q - 1))
m = pow(c, d, n)
plaintext = m.to_bytes((m.bit_length() + 7) // 8, 'big')
print('Fermat iterations:', steps)
print('RSA plaintext:', repr(plaintext))
claim = plaintext.decode()
actual = hashlib.sha256(claim.encode()).hexdigest()
print('Claim digest:', actual)
assert actual == fields['claim_sha256'], 'Recovered claim hash mismatch'
Path('claim.txt').write_text(claim)
print('Verified boarding pass saved to claim.txt')
