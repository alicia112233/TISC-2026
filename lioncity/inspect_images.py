from pathlib import Path
from PIL import Image
import numpy as np
import re, struct, itertools

for name in ['supertree','chicken-rice','purple-orchid']:
    data=Path(name+'.png').read_bytes()
    print('\nIMAGE',name, 'size',len(data))
    pos=8
    while pos+8 <= len(data):
        size=struct.unpack('>I',data[pos:pos+4])[0]
        typ=data[pos+4:pos+8]
        if typ!=b'IDAT': print('chunk',typ,size,data[pos+8:pos+8+min(size,150)])
        pos+=size+12
        if typ==b'IEND': break
    print('trailing',data[pos:pos+300])
    im=np.array(Image.open(name+'.png').convert('RGBA'))
    print('shape',im.shape)
    for c in range(4):
        plane=im[:,:,c]
        for bit in range(2):
            for order,arr in [('xy',plane),('yx',plane.T)]:
                bits=((arr.flatten() >> bit)&1)
                for bitorder in ['big','little']:
                    raw=np.packbits(bits,bitorder=bitorder).tobytes()
                    text=re.findall(rb'[ -~]{12,}',raw)
                    if text: print('channel',c,'bit',bit,order,bitorder,text[:6])
    for channels in [(0,1,2),(2,1,0),(0,1,2,3),(3,2,1,0)]:
        for bit in range(2):
            bits=(im[:,:,channels].flatten()>>bit)&1
            for bitorder in ['big','little']:
                raw=np.packbits(bits,bitorder=bitorder).tobytes()
                text=re.findall(rb'[ -~]{12,}',raw)
                if text: print('channels',channels,'bit',bit,bitorder,text[:6])
    transparent=im[im[:,:,3]==0][:,:3].tobytes()
    print('transparent RGB strings',re.findall(rb'[ -~]{12,}',transparent)[:10])
