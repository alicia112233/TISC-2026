import json
import struct
import numpy as np
with open('model/model.safetensors','rb') as f:
    size=struct.unpack('<Q',f.read(8))[0]
    h=json.loads(f.read(size))
emb=np.memmap('model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
def floats(x):
    return (x.astype(np.uint32)<<16).view(np.float32)
indices=[151828,151879,151905,151914,151934]
base=floats(emb[127340])
counts=np.zeros(2048,dtype=int)
for i in indices:
    v=floats(emb[i])
    scale=np.dot(base,v)/np.dot(base,base)
    residual=v-scale*base
    ix=np.argsort(np.abs(residual))[-20:][::-1]
    counts[ix]+=1
    print(i,'scale',float(scale),'big residuals',json.dumps([(int(c),float(residual[c]),hex(int(emb[i,c])),float(v[c])) for c in ix]),flush=True)
print('common residual coordinates',np.flatnonzero(counts>=4).tolist(),flush=True)
