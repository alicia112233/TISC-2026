import json
import struct
import numpy as np
with open('model/model.safetensors','rb') as f:
    size=struct.unpack('<Q',f.read(8))[0]
    h=json.loads(f.read(size))
emb=np.memmap('model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
rows=np.arange(151690,151936)
u=np.array(emb[151690:])
for low in [64,100,256]:
    for high in [None,64,100,256]:
        m=(u&255)==(rows%low)[:,None]
        if high:
            m &= (u>>8)==(rows%high)[:,None]
        cols=np.count_nonzero(m,axis=0)
        top=np.argsort(cols)[-12:][::-1]
        print('rawcheck',low,high,[(int(i),int(cols[i])) for i in top])
vals=(u.astype(np.uint32)<<16).view(np.float32)
for mul in [1,100,1000,10000,100000,1000000]:
    words=np.rint(vals*mul).astype(np.int64)
    m=((words&255)==(rows%64)[:,None]) & (((words>>8)&255)==(rows%100)[:,None])
    cols=np.count_nonzero(m,axis=0)
    top=np.argsort(cols)[-10:][::-1]
    print('numericcheck',mul,[(int(i),int(cols[i])) for i in top if cols[i]])
for a,b in [(151690,151837),(151837,151936)]:
    v=np.array(emb[a:b])
    refs=v[0]
    print('row_groups',a,b)
    for i,row in enumerate(v):
        diff=np.flatnonzero(row!=refs)
        if len(diff)>10:
            print(a+i,len(diff),'norm',float(np.linalg.norm((row.astype(np.uint32)<<16).view(np.float32))))
