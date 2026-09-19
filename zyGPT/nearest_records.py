import os
os.environ['OMP_NUM_THREADS']='1'
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
import json
import struct
import numpy as np
with open('model/model.safetensors','rb') as f:
    size=struct.unpack('<Q',f.read(8))[0]
    h=json.loads(f.read(size))
emb=np.memmap('model/model.safetensors',mode='r',offset=8+size,dtype='<u2',shape=(151936,2048))
def floats(x):
    return (x.astype(np.uint32)<<16).view(np.float32)
indices=[151828,151831,151838,151844,151846,151850,151853,151879,151894,151902,151905,151906,151911,151914,151915,151920,151925,151931,151934]
special=floats(emb[indices])
special/=np.linalg.norm(special,axis=1,keepdims=True)
scores=np.empty((151643,len(indices)),dtype=np.float32)
for start in range(0,151643,4096):
    e=floats(emb[start:min(start+4096,151643)])
    e/=np.linalg.norm(e,axis=1,keepdims=True)
    scores[start:start+len(e)]=e @ special.T
t=json.load(open('model_tokenizer.json',encoding='utf-8'))
v={i:s for s,i in t['model']['vocab'].items()}
records=[]
for i,record in enumerate(indices):
    ids=np.argsort(scores[:,i])[-3:][::-1]
    best=int(ids[0])
    diff=np.flatnonzero(emb[record]!=emb[best])
    result={'record':record,'nearest':[(int(j),v[int(j)],round(float(scores[j,i]),6)) for j in ids], 'different_coords':diff.tolist(),'words':emb[record,diff].tolist(),'source_words':emb[best,diff].tolist()}
    records.append(result)
    print(json.dumps({**result,'different_coords':diff.tolist() if len(diff)<30 else len(diff),'words':result['words'] if len(diff)<30 else [],'source_words':result['source_words'] if len(diff)<30 else []},ensure_ascii=True),flush=True)
with open('records.json','w',encoding='utf-8') as f:
    json.dump(records,f)
