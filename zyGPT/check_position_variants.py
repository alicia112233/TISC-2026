import hashlib,json,pathlib,itertools
import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher,algorithms,modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
root=pathlib.Path(__file__).parent
h=json.loads((root/'safetensors_header.bin').read_bytes()[8:35656])
names=[n for n in h if '.mlp.' in n]
base=[np.memmap(root/'carriers'/(n+'.bin'),mode='r',dtype='<u2') for n in names]
leak=[np.memmap(root/'model/model.safetensors',mode='r',offset=35656+h[n]['data_offsets'][0],dtype='<u2',shape=(12582912,)) for n in names]
kms=['33fe354b27a4d68488f61dd76f527675','2bbd060bcba20efb4501e359161b2681']
for kmhex in kms:
 km=bytes.fromhex(kmhex);key=hashlib.sha256(km+b'\0').digest();sd=hashlib.sha256(km+b'\1').digest()
 seeds=[sd,sd[:16],sd.hex().encode(),km,km+b'\1',key,sd[::-1],hashlib.sha256(b'\1'+km).digest()]
 for si,seed in enumerate(seeds):
  for typ in ['>u8','>i8','<u8','<i8','>u4','<u4']:
   rng=np.frombuffer(hashlib.shake_256(seed).digest(8*1024),dtype=typ)%12582912
   raw=list(dict.fromkeys(rng.tolist()))[:608]
   for oi,p in enumerate([raw,sorted(raw),list(set(raw))]):
    bits=np.stack([((a[p]^b[p])&1).astype(np.uint8) for a,b in zip(base,leak)],axis=1)
    for order in ['big','little']:
     payloads=np.packbits(bits,axis=0,bitorder=order).T
     blocks=np.zeros((len(names),16),dtype=np.uint8);blocks[:,:12]=payloads[:,:12];blocks[:,15]=2
     encryptor=Cipher(algorithms.AES(key),modes.ECB()).encryptor()
     streams=np.frombuffer(encryptor.update(blocks.tobytes()),dtype=np.uint8).reshape(-1,16)
     plainprefix=payloads[:,12:17]^streams[:,:5]
     for index in np.flatnonzero(np.all(plainprefix==np.frombuffer(b'TISC{',dtype=np.uint8),axis=1)):
      payload=payloads[index].tobytes()
      result={'km':kmhex,'carrier':names[index],'payload':payload.hex(),'variant':[si,typ,oi,order]}
      (root/'prefix_match.json').write_text(json.dumps(result,indent=2));print('PREFIX',result,flush=True)
      try:print('FLAG',AESGCM(key).decrypt(payload[:12],payload[12:],None),flush=True)
      except Exception as e:print('AAD?',str(e),flush=True)
  print('Checked seed',kmhex,si,flush=True)
