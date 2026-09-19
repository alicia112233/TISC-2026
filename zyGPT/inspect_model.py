import json
import pathlib
import struct

import numpy as np
import requests

BASE = 'http://chals.tisc26.ctf.sg:14172/model/model.safetensors'
raw = pathlib.Path('safetensors_header.bin').read_bytes()
header_len = struct.unpack('<Q', raw[:8])[0]
header = json.loads(raw[8:8 + header_len])
data_start = 8 + header_len
tok = json.loads(pathlib.Path('model_tokenizer.json').read_text(encoding='utf-8'))
names = {x['id']: x['content'] for x in tok['added_tokens']}

def fetch(start, end, filename):
    path = pathlib.Path(filename)
    if not path.exists():
        r = requests.get(BASE, headers={'Range': f'bytes={start}-{end - 1}'}, timeout=60)
        r.raise_for_status()
        assert r.status_code == 206, (r.status_code, r.headers)
        assert len(r.content) == end - start
        path.write_bytes(r.content)
    return path.read_bytes()

def bf16(raw):
    return (np.frombuffer(raw, dtype='<u2').astype(np.uint32) << 16).view(np.float32)

emb = bf16(fetch(data_start + 151600 * 4096, data_start + 151936 * 4096, 'embedding_tail.bin')).reshape(-1, 2048)
for i in range(151643, 151700):
    row = emb[i - 151600]
    ix = np.argsort(np.abs(row))[-10:][::-1]
    print(i, names.get(i, ''), 'norm', round(float(np.linalg.norm(row)), 3), 'max', float(np.abs(row).max()), 'nonzero', int(np.count_nonzero(row)), 'top', list(zip(ix.tolist(),row[ix].tolist())))

for key in ['model.layers.0.input_layernorm.weight','model.norm.weight']:
    meta = header[key]
    a,b = meta['data_offsets']
    v = bf16(fetch(data_start+a,data_start+b,key.replace('.','_')+'.bin'))
    print(key, 'min/max/mean', v.min(),v.max(),v.mean(), 'last64',v[-64:].tolist())