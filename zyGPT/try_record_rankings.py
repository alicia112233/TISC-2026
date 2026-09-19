import hashlib,json,pathlib,struct,numpy as np
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
root=pathlib.Path(__file__).parent
h=json.loads((root/'safetensors_header.bin').read_bytes()[8:35656])
d=json.loads((root/'all_records.json').read_text())
rows=d['rows'];x=np.memmap(root/'model/model.safetensors',mode='r',offset=35656,dtype='<u2',shape=(151936,2048))
records={r:struct.pack('>I',r)+x[r,[361,553,1152,1289,2014,2039]].tobytes() for r in rows}
names=[n for n in h if '.mlp.' in n]
base=[np.memmap(root/'carriers'/(n+'.bin'),mode='r',dtype='<u2') for n in names]
leak=[np.memmap(root/'model/model.safetensors',mode='r',offset=35656+h[n]['data_offsets'][0],dtype='<u2',shape=(12582912,)) for n in names]
seen=set()
def attempt(rs):
 rs=tuple(sorted(rs))
 if rs in seen:return
 seen.add(rs)
 km=hashlib.sha256(b''.join(records[r] for r in rs)).digest()[:16];key=hashlib.sha256(km+b'\0').digest();seed=hashlib.sha256(km+b'\1').digest()
 rng=np.frombuffer(hashlib.shake_256(seed).digest(8*640),dtype='>u8')
 p=list(dict.fromkeys((rng%12582912).tolist()))[:608]
 for name,a,b in zip(names,base,leak):
  payload=np.packbits(((a[p]^b[p])&1).astype(np.uint8)).tobytes()
  try:plain=AESGCM(key).decrypt(payload[:12],payload[12:],None)
  except Exception:continue
  result={'rows':rs,'km':km.hex(),'carrier':name,'plaintext':plain.decode(errors='replace'),'payload':payload.hex()}
  (root/'flag_result.json').write_text(json.dumps(result,indent=2));print('SUCCESS',result,flush=True);raise SystemExit()

for key in ['cosines','clean_cosines','norms']:
 for group in [rows,[r for r in rows if r<151643],[r for r,c in zip(rows,d['cosines']) if c>.99]]:
  scores=dict(zip(rows,d[key]));rank=sorted(group,key=lambda r:scores[r],reverse=True)
  for i in range(1,len(rank)+1):
   attempt(rank[:i]);attempt(rank[i:])
  print('Tested ranking',key,len(group),'sets',len(seen),flush=True)
