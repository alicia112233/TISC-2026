from itertools import permutations
from pathlib import Path
import numpy as np
from PIL import Image

im = np.array(Image.open('printer-secret.png')).astype(int)
palette = np.array([(3,3,3),(255,255,255),(243,120,118),(255,158,93),
                    (244,212,96),(141,166,126),(131,179,218),(142,127,170)])
names = 'KWROYGBP'
grid = []
for r in range(36):
    row = []
    for c in range(36):
        x = 366.6667 + c * 13.333333
        if c == 0: x += 2
        if c == 35: x -= 2
        y = 696.6667 + (r + (2/3 if c%2==0 else 1/3)) * 13.333333
        patch = im[round(y)-1:round(y)+2,round(x)-1:round(x)+2]
        rgb = np.median(patch,axis=(0,1))
        row.append(np.square(palette-rgb).sum(-1).argmin())
    grid.append(row)
grid = np.array(grid)
print('\n'.join(''.join(names[c] for c in row) for row in grid))
np.save('triangle_grid.npy',grid)
maps = np.array(list(permutations(range(8))), dtype=np.uint8)

def unpack(vals):
    # Eight 3-bit symbols form three bytes.
    v = vals[:,:vals.shape[1]//8*8].reshape(len(vals),-1,8).astype(np.uint16)
    out = np.empty((len(vals),v.shape[1],3),dtype=np.uint8)
    out[:,:,0] = (v[:,:,0]<<5) | (v[:,:,1]<<2) | (v[:,:,2]>>1)
    out[:,:,1] = (v[:,:,2]<<7) | (v[:,:,3]<<4) | (v[:,:,4]<<1) | (v[:,:,5]>>2)
    out[:,:,2] = (v[:,:,5]<<6) | (v[:,:,6]<<3) | v[:,:,7]
    return out.reshape(len(vals),-1)

for trans in range(2):
 for flipr in range(2):
  for flipc in range(2):
   for edge in range(4):
    g = grid.T if trans else grid
    g = g[::(-1 if flipr else 1), ::(-1 if flipc else 1)]
    if edge&1:g=g[:,1:]
    if edge&2:g=g[:,:-1]
    for snake in range(2):
     h=g.copy()
     if snake:h[1::2]=h[1::2,::-1]
     data=unpack(maps[:,h.ravel()])
     printable=((data>=32)&(data<127))|(data==10)|(data==13)|(data==9)
     score=printable[:,:160].mean(1)
     best=score.argmax()
     if score[best]>.65:
      print('CANDIDATE',trans,flipr,flipc,edge,snake,'map',maps[best].tolist(),'score',score[best],bytes(data[best,:200]))
      if score[best]>.95:
       Path('tag_decoded.bin').write_bytes(bytes(data[best]))
