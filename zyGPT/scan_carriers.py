import concurrent.futures
import hashlib
import json
import pathlib
import struct
import time

import numpy as np
import requests

ROOT = pathlib.Path(__file__).parent
raw = (ROOT / 'fresh_upstream_header.bin').read_bytes()
size = struct.unpack('<Q', raw[:8])[0]
header = json.loads(raw[8:8+size])
raw_local = (ROOT / 'safetensors_header.bin').read_bytes()
local_size = struct.unpack('<Q', raw_local[:8])[0]
local_header = json.loads(raw_local[8:8+local_size])
out = ROOT / 'carriers'
out.mkdir(exist_ok=True)
URL = 'https://huggingface.co/Qwen/Qwen3-1.7B/resolve/main/model-00001-of-00002.safetensors'

def scan(name):
    a, b = header[name]['data_offsets']
    dest = out / (name + '.bin')
    if dest.exists():
        payload = dest.read_bytes()
    else:
        for attempt in range(4):
            try:
                r = requests.get(URL + '?carrier=' + name, headers={'Range': f'bytes={8+size+a}-{8+size+b-1}'}, timeout=120)
                r.raise_for_status()
                assert r.status_code == 206 and len(r.content) == b-a, (r.status_code,len(r.content))
                payload = r.content
                break
            except Exception:
                if attempt == 3: raise
    baseline = np.frombuffer(payload, dtype='<u2')
    local = np.memmap(ROOT / 'model/model.safetensors', mode='r', offset=8+local_size+local_header[name]['data_offsets'][0], dtype='<u2', shape=baseline.shape)
    xor = baseline ^ local
    count = int(np.count_nonzero(xor))
    one = int(np.count_nonzero(xor == 1))
    if count:
        dest.write_bytes(payload)
    result = {'tensor': name, 'changed': count, 'lsb_only': one, 'words': len(baseline)}
    print(json.dumps(result), flush=True)
    return result

names = [n for n in header if '.mlp.' in n]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(scan, names))
(out / 'scan.json').write_text(json.dumps(results, indent=2))
