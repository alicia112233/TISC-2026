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
special=floats(emb[151669:151690])
special/=np.linalg.norm(special,axis=1,keepdims=True)
scores=np.empty((151643,21),dtype=np.float32)
for start in range(0,151643,4096):
    e=floats(emb[start:min(start+4096,151643)])
    e/=np.linalg.norm(e,axis=1,keepdims=True)
    scores[start:start+len(e)]=e @ special.T
t=json.load(open('model_tokenizer.json',encoding='utf-8'))
v={i:s for s,i in t['model']['vocab'].items()}
names={x['id']:x['content'] for x in t['added_tokens']}
for i in range(21):
    ids=np.argsort(scores[:,i])[-10:][::-1]
    print(names[151669+i],json.dumps([(int(j),v[int(j)],round(float(scores[j,i]),4)) for j in ids],ensure_ascii=True),flush=True)
