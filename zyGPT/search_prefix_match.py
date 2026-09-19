import hashlib
import itertools
import json
import pathlib
import struct
import time
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

ROOT=pathlib.Path(__file__).parent
raw=(ROOT/'safetensors_header.bin').read_bytes()
size=struct.unpack('<Q',raw[:8])[0]
header=json.loads(raw[8:8+size])
emb=np.memmap(ROOT/'model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
coords=[361,553,1152,1289,2014,2039]
records=[]
for row in range(151669,151936):
    record=struct.pack('>I',row)+emb[row,coords].tobytes()
    if hashlib.sha256(record).digest()[:2]==bytes([int(emb[row,959])&255,int(emb[row,1864])&255]): records.append((row,record))
groups={}
for path in sorted((ROOT/'carriers').glob('*.bin')):
    name=path.name[:-4]
    base=np.memmap(path,mode='r',dtype='<u2')
    local=np.memmap(ROOT/'model/model.safetensors',mode='r',offset=8+size+header[name]['data_offsets'][0],dtype='<u2',shape=base.shape)
    exp=(base>>7)&255
    eligible=(exp!=0)&(exp!=255)
    bits=((base[eligible]^local[eligible])&1).astype(np.uint8)
    groups.setdefault(len(bits),[]).append((name,bits))
    del exp,eligible
groups=[(n,[name for name,_ in v],np.stack([b for _,b in v],axis=1)) for n,v in groups.items()]
print('Carrier groups',[(n,len(names)) for n,names,_ in groups],flush=True)
started=time.monotonic()
seen=set()
def attempt(subset):
    ids=tuple(sorted(subset))
    if ids in seen:return
    seen.add(ids)
    km=hashlib.sha256(b''.join(records[i][1] for i in ids)).digest()[:16]
    key=hashlib.sha256(km+b'\0').digest()
    seed=hashlib.sha256(km+b'\1').digest()
    aes=AESGCM(key)
    rng=np.frombuffer(hashlib.shake_256(seed).digest(8*160),dtype='>u8')
    for n,names,bits in groups:
        positions=np.array(list(dict.fromkeys((rng%n).tolist()))[:136])
        payloads=np.packbits(bits[positions],axis=0,bitorder='big').T
        blocks=np.zeros((len(names),16),dtype=np.uint8)
        blocks[:,:12]=payloads[:,:12]
        blocks[:,15]=2
        encryptor=Cipher(algorithms.AES(key),modes.ECB()).encryptor()
        streams=np.frombuffer(encryptor.update(blocks.tobytes())+encryptor.finalize(),dtype=np.uint8).reshape(-1,16)
        first=payloads[:,12:17]^streams[:,:5]
        candidates=np.flatnonzero(np.all(first==np.frombuffer(b'TISC{',dtype=np.uint8),axis=1))
        for index in candidates:
            name=names[index]
            fullrng=np.frombuffer(hashlib.shake_256(seed).digest(8*640),dtype='>u8')
            fullpositions=np.array(list(dict.fromkeys((fullrng%n).tolist()))[:608])
            p=np.packbits(bits[fullpositions,index],bitorder='big').tobytes()
            print('PREFIX MATCH',json.dumps({'rows':[records[i][0] for i in ids],'km':km.hex(),'carrier':name,'payload':p.hex()}),flush=True)
            (ROOT/'prefix_match.json').write_text(json.dumps({'rows':[records[i][0] for i in ids],'km':km.hex(),'carrier':name,'payload':p.hex()}))
            try:plain=aes.decrypt(p[:12],p[12:],None)
            except Exception:continue
            result={'rows':[records[i][0] for i in ids],'km':km.hex(),'carrier':name,'plaintext':plain.decode(errors='replace'),'payload':p.hex()}
            (ROOT/'flag_result.json').write_text(json.dumps(result,indent=2))
            print('SUCCESS',json.dumps(result),flush=True)
            raise SystemExit(0)
    if len(seen)%20000==0:print('Tested',len(seen),'sets in',round(time.monotonic()-started,1),'s',flush=True)

cluster=[i for i,(r,_) in enumerate(records) if r in [151828,151879,151905,151914,151934]]
others=[i for i in range(len(records)) if i not in cluster]
attempt(range(len(records)))
attempt(cluster)
attempt(others)
for n in range(len(cluster)+1):
    for c in itertools.combinations(cluster,n):
        attempt(c)
        attempt(others+list(c))
for i in range(len(records)):
    attempt([i])
    attempt([j for j in range(len(records)) if j!=i])
print('Simple hypotheses exhausted',len(seen),flush=True)
for n in range(2,len(records)):
    for c in itertools.combinations(range(len(records)),n):attempt(c)
print('All subsets exhausted',flush=True)
