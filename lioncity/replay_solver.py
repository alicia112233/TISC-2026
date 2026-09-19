import base64
import hashlib
import json
import struct
import sys
import time
from pathlib import Path

import requests
from inspect_challenge import BASE, route


def ticket():
    saved = json.loads(Path('stamp.json').read_text()) if Path('stamp.json').exists() else {}
    tok = saved.get('ticket', '')
    if tok:
        body = tok.split('.')[0]
        payload = json.loads(base64.urlsafe_b64decode(body + '=' * (-len(body) % 4)))
        if payload['exp'] > int(time.time() * 1000) + 60000:
            return tok
    start = requests.get(BASE + '/api/harbour/start', timeout=30).json()
    Path('start.json').write_text(json.dumps(start))
    traces = [route(level['grid']) for level in start['levels']]
    result = requests.post(BASE + '/api/harbour/stamp', json={'session': start['session'], 'traces': traces}, timeout=30).json()
    Path('stamp.json').write_text(json.dumps(result))
    return result['ticket']


def leb(value):
    out = bytearray()
    while True:
        byte = value & 127
        value >>= 7
        out.append(byte | (128 if value else 0))
        if not value:
            return bytes(out)


def section(program):
    payload = b'\x05singaMERLION\x00v1.6.1\x00' + struct.pack('<H', len(program)) + program
    return b'\x00' + leb(len(payload)) + payload


def cartridge(*programs):
    return b'\x00asm\x01\x00\x00\x00' + b''.join(section(p) for p in programs)


def run(tok, wasm, label):
    module = base64.b64encode(wasm).decode()
    prefix = (tok + '.' + module + '.').encode()
    nonce = 0
    while not hashlib.sha256(prefix + str(nonce).encode()).hexdigest().startswith('0000'):
        nonce += 1
    result = requests.post(BASE + '/api/harbour/run', json={'ticket': tok, 'module': module, 'pow': str(nonce)}, timeout=30)
    print(label, 'nonce', nonce, 'status', result.status_code, result.text, flush=True)
    Path(label + '.json').write_text(result.text)
    Path(label + '.wasm').write_bytes(wasm)
    return result.json()


if __name__ == '__main__':
    tok = ticket()
    if len(sys.argv) > 1:
        programs = [bytes.fromhex(x) for x in sys.argv[1:]]
        run(tok, cartridge(*programs), 'custom-replay')
    else:
        run(tok, Path('singa_legacy.wasm').read_bytes(), 'reference-replay')
        run(tok, cartridge(bytes.fromhex('31 00 00 ff ff')), 'service-replay')
        run(tok, cartridge(bytes.fromhex('61 00 00 ff ff')), 'diagnostic-replay')
        run(tok, cartridge(bytes.fromhex('01 2a fe ff'), bytes.fromhex('61 00 00 ff ff')), 'double-replay')
