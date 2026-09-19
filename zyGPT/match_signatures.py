import json
import struct
import sys
import numpy as np
with open('model/model.safetensors','rb') as f:
    size=struct.unpack('<Q',f.read(8))[0]
    h=json.loads(f.read(size))
emb=np.memmap('model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
coords=[361,553,959,1152,1289,1864,2014,2039]
records=[151828,151831,151838,151844,151846,151850,151853,151879,151894,151902,151905,151906,151911,151914,151915,151920,151925,151931,151934]
original=np.memmap('upstream_embeddings.bin',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048)) if '--upstream' in sys.argv else emb
base=np.array(original[:151643,coords])
for r in records:
    hits=base==emb[r,coords]
    count=hits.sum(axis=1)
    best=np.argsort(count)[-5:][::-1]
    print(r,'best exact signature matches',[(int(i),int(count[i]),np.array(coords)[hits[i]].tolist()) for i in best],flush=True)