import hashlib
import json
import pathlib
import struct
import numpy as np

ROOT = pathlib.Path(__file__).parent
raw=(ROOT/'safetensors_header.bin').read_bytes()
size=struct.unpack('<Q',raw[:8])[0]
header=json.loads(raw[8:8+size])
emb=np.memmap(ROOT/'model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
coordinates=[361,553,1152,1289,2014,2039]
records=[]
for row in range(151936):
    record=struct.pack('>I',row)+emb[row,coordinates].tobytes()
    check=bytes([int(emb[row,959])&255,int(emb[row,1864])&255])
    if hashlib.sha256(record).digest()[:2]==check:
        records.append((row,record))
candidate=json.loads((ROOT/'all_records.json').read_text())
selected={r for r,c in zip(candidate['rows'],candidate['cosines']) if c>float(__import__('sys').argv[1])}
records=[r for r in records if r[0] in selected]
print('Selected rows', [r for r,_ in records],flush=True)
km=hashlib.sha256(b''.join(r for _,r in records)).digest()[:16]
key=hashlib.sha256(km+b'\x00').digest()
seed=hashlib.sha256(km+b'\x01').digest()
print('KM',km.hex(),'key',key.hex(),flush=True)
random=np.frombuffer(hashlib.shake_256(seed).digest(8*2048),dtype='>u8')
results={}
for path in sorted((ROOT/'carriers').glob('*.bin')):
    name=path.name[:-4]
    base=np.memmap(path,mode='r',dtype='<u2')
    local=np.memmap(ROOT/'model/model.safetensors',mode='r',offset=8+size+header[name]['data_offsets'][0],dtype='<u2',shape=base.shape)
    exp=(base>>7)&255
    eligible=np.flatnonzero((exp!=0)&(exp!=255))
    positions=list(dict.fromkeys((random % len(eligible)).tolist()))[:608]
    indices=eligible[positions]
    bits=((base[indices]^local[indices])&1).astype(np.uint8)
    for order in ['big','little']:
        payload=np.packbits(bits,bitorder=order).tobytes()
        results[name+':'+order]=payload.hex()
        for label,out in [('raw',payload),('shake',bytes(a^b for a,b in zip(payload,hashlib.shake_256(key).digest(len(payload)))) )]:
            if b'TISC' in out or all(32<=v<127 for v in out[:10]): print('POSSIBLE',name,order,label,repr(out),flush=True)
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM,ChaCha20Poly1305
            for cls in [AESGCM,ChaCha20Poly1305]:
                try:
                    plain=cls(key).decrypt(payload[:12],payload[12:],None)
                    print('DECRYPTED',name,order,repr(plain),flush=True)
                    (ROOT/'flag_result.json').write_text(json.dumps({'rows':[r for r,_ in records],'km':km.hex(),'carrier':name,'plaintext':plain.decode(errors='replace'),'payload':payload.hex()},indent=2))
                except Exception: pass
        except ImportError: pass
(ROOT/'extracted_seals.json').write_text(json.dumps(results,indent=2))
print('Tested',len(results),'payloads',flush=True)
