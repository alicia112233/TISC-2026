from itertools import permutations
from pathlib import Path
import numpy as np

grid=np.load('triangle_grid.npy')
maps=np.array(list(permutations(range(8))),dtype=np.uint8)
rev=np.array([int(f'{i:08b}'[::-1],2) for i in range(256)],dtype=np.uint8)

def unpack(vals,shift):
 v=vals[:,:vals.shape[1]//8*8].reshape(len(vals),-1,8).astype(np.uint16)
 out=np.empty((len(vals),v.shape[1],3),dtype=np.uint8)
 out[:,:,0]=(v[:,:,0]<<5)|(v[:,:,1]<<2)|(v[:,:,2]>>1)
 out[:,:,1]=(v[:,:,2]<<7)|(v[:,:,3]<<4)|(v[:,:,4]<<1)|(v[:,:,5]>>2)
 out[:,:,2]=(v[:,:,5]<<6)|(v[:,:,6]<<3)|v[:,:,7]
 out=out.reshape(len(vals),-1)
 if shift:out=(out[:,:-1]<<shift)|(out[:,1:]>>(8-shift))
 return out

bestall=0
for trans in range(2):
 for flipr in range(2):
  for flipc in range(2):
   g=grid.T if trans else grid
   g=g[::(-1 if flipr else 1),::(-1 if flipc else 1)]
   for snake in range(2):
    h=g.copy()
    if snake:h[1::2]=h[1::2,::-1]
    vals=maps[:,h.ravel()]
    for shift in range(8):
     data=unpack(vals,shift)
     for bitrev in range(2):
      d=rev[data] if bitrev else data
      score=(((d>=32)&(d<127))|(d==10)|(d==13)|(d==9)).mean(1)
      i=score.argmax()
      if score[i]>bestall:
       bestall=score[i]
       print('BEST',bestall,trans,flipr,flipc,snake,shift,bitrev,maps[i].tolist(),bytes(d[i,:180]),flush=True)
      if score[i]>.9:
       Path('tag_decoded.bin').write_bytes(bytes(d[i]))
