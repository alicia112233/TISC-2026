#!/usr/bin/env python3
# Find VA of target strings and grep the disasm for lea references.
import struct, re, subprocess, os
OUT='/mnt/c/Users/alici/Downloads/TISC 2026/omnitrix/analysis'
BIN=os.path.expanduser('~/omni/omnitrix')
data=open(BIN,'rb').read()

# parse ELF program headers to map file offset -> vaddr for PT_LOAD segments
e_phoff=struct.unpack_from('<Q', data, 0x20)[0]
e_phentsize=struct.unpack_from('<H', data, 0x36)[0]
e_phnum=struct.unpack_from('<H', data, 0x38)[0]
segs=[]
for i in range(e_phnum):
    off=e_phoff+i*e_phentsize
    p_type=struct.unpack_from('<I',data,off)[0]
    p_offset=struct.unpack_from('<Q',data,off+0x08)[0]
    p_vaddr=struct.unpack_from('<Q',data,off+0x10)[0]
    p_filesz=struct.unpack_from('<Q',data,off+0x20)[0]
    if p_type==1:
        segs.append((p_offset,p_vaddr,p_filesz))
def off2va(o):
    for po,pv,ps in segs:
        if po<=o<po+ps:
            return pv+(o-po)
    return None

targets=[b'authenticate first', b'master-control override granted', b'master-control key rejected',
         b'codon.stream.inject', b'client authenticated', b'unknown opcode', b'lease issued',
         b'unknown or expired master-control voucher', b'omnitrix.master_control.prepare',
         b'need 21 bytes', b'imported ', b'bytes into codon vault', b'elf content rejected',
         b'raw-syscall density', b'blob: plaintext', b'/bin/zsh', b'execveat', b'master-control voucher belongs']

f=open(OUT+'/xref.out','w')
vamap={}
for t in targets:
    idx=data.find(t)
    if idx<0:
        f.write(f'{t!r}: NOT FOUND\n'); continue
    va=off2va(idx)
    vamap[t]=va
    f.write(f'{t!r}: fileoff=0x{idx:x} va=0x{va:x}\n')
f.write('\n')
f.flush()
f.close()
print('done', {t.decode():hex(v) for t,v in vamap.items()})
