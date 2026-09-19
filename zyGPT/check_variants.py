import hashlib,itertools,json,pathlib,struct,time
import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
root=pathlib.Path(__file__).parent
h=json.loads((root/'safetensors_header.bin').read_bytes()[8:35656])
x=np.memmap(root/'model/model.safetensors',mode='r',offset=35656,dtype='<u2',shape=(151936,2048))
allrows=[v['record'] for v in json.loads((root/'records.json').read_text())]
live=[151828,151879,151905,151914,151934]
coords=[361,553,1152,1289,2014,2039]
names=[n for n in h if '.mlp.' in n]
baselines=[np.memmap(root/'carriers'/(n+'.bin'),mode='r',dtype='<u2') for n in names]
leaks=[np.memmap(root/'model/model.safetensors',mode='r',offset=35656+h[n]['data_offsets'][0],dtype='<u2',shape=(12582912,)) for n in names]
km_candidates={}
for rows in [live,allrows,[r for r in allrows if r not in live]]:
 for rowend,sigend in itertools.product(['>','<'],repeat=2):
  for includeid in [True,False]:
   for reverse in [True,False]:
    rec=[(struct.pack(rowend+'I',r) if includeid else b'')+struct.pack(sigend+'6H',*[int(v) for v in x[r,coords]]) for r in sorted(rows,reverse=reverse)]
    digest=hashlib.sha256(b''.join(rec)).digest()
    for km in [digest[:16],digest[16:],digest,digest[:16].hex().encode(),digest.hex().encode()]:km_candidates[km]=(rows,rowend,sigend,includeid,reverse)
print('KM variants',len(km_candidates),flush=True)
count=0
for km,desc in km_candidates.items():
 for salt0,salt1 in [(b'\0',b'\1'),(b'0',b'1'),(b'\1',b'\2')]:
  key=hashlib.sha256(km+salt0).digest();seed=hashlib.sha256(km+salt1).digest()
  for endian,width in [('>',8),('<',8),('>',4),('<',4)]:
   rng=np.frombuffer(hashlib.shake_256(seed).digest(width*640),dtype=endian+'u'+str(width))
   positions=list(dict.fromkeys((rng%12582912).tolist()))[:608]
   for order in ['big','little']:
    for i,name in enumerate(names):
     bits=((baselines[i][positions]^leaks[i][positions])&1).astype(np.uint8)
     payload=np.packbits(bits,bitorder=order).tobytes()
     try:plain=AESGCM(key).decrypt(payload[:12],payload[12:],None)
     except Exception:continue
     result={'rows':desc[0],'km':km.hex(),'carrier':name,'plaintext':plain.decode(errors='replace'),'payload':payload.hex(),'variant':str((desc,salt0,salt1,endian,width,order))}
     (root/'flag_result.json').write_text(json.dumps(result,indent=2));print('SUCCESS',result,flush=True);raise SystemExit()
  count+=1
  if count%30==0:print('Key/seed variants',count,flush=True)
print('No variant succeeded',flush=True)
