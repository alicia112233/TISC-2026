import collections
import json
import struct
import numpy as np

with open('model/model.safetensors','rb') as f:
    size=struct.unpack('<Q',f.read(8))[0]
    h=json.loads(f.read(size))
emb=np.memmap('model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
tail=emb[151669:]
expected=np.array([((row%100)<<8)|(row%64) for row in range(151669,151936)],dtype=np.uint16)
matches=tail==expected[:,None]
cols=np.count_nonzero(matches,axis=0)
print('matching check columns:',[(int(i),int(cols[i])) for i in np.argsort(cols)[-25:][::-1] if cols[i]],flush=True)
for i in range(len(tail)):
    same=np.count_nonzero(tail[i]!=tail[21])
    if same and i>20:
        row=151669+i
        diff=np.flatnonzero(tail[i]!=tail[21])
        vals=tail[i,diff]
        f=(vals.astype(np.uint32)<<16).view(np.float32)
        print('row',row,'diffcount',same,'checkcoords',np.flatnonzero(matches[i]).tolist(),'differences',json.dumps(list(zip(diff.tolist(),vals.tolist(),[str(x) for x in f])) if same<40 else list(zip(diff[:10].tolist(),vals[:10].tolist())),ensure_ascii=True),flush=True)
