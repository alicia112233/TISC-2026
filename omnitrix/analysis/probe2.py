#!/usr/bin/env python3
import socket, struct, time, sys
HOST, PORT = '127.0.0.1', 19191
MAGIC = b'OMNI'
def conn():
    s=socket.socket(); s.connect((HOST,PORT)); s.settimeout(1.0); return s
def rall(s,t=0.5):
    s.settimeout(t); d=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            d+=c
    except: pass
    return d
def txt(b): return ''.join(chr(x) if 32<=x<127 else '.' for x in b)
def frameA(op, payload=b'', seq=0, ver=1, typ=0):
    return MAGIC + bytes([ver,typ]) + struct.pack('>H',op) + struct.pack('>Q',seq) + struct.pack('>H',len(payload)) + payload
def send1(frame, t=0.5):
    try:
        s=conn(); s.send(frame); r=rall(s,t); s.close(); return r
    except Exception as e:
        return b'ERR:'+str(e).encode()

out=[]
def log(*a):
    s=' '.join(str(x) for x in a); out.append(s)

log('=== format A opcode scan 0x00..0x60 (empty payload) ===')
for op in range(0, 0x61):
    r = send1(frameA(op))
    if r:
        log(f'op 0x{op:04x} -> {txt(r)[:120]!r}')
log('=== with ben.tennyson payload ===')
for op in range(0, 0x61):
    r = send1(frameA(op, b'ben.tennyson'))
    if r and b'unknown opcode' not in r:
        log(f'op 0x{op:04x}+cred -> {txt(r)[:120]!r}')

open('/tmp/probe2.out','w').write('\n'.join(out)+'\n')
print('\n'.join(out))
print('DONE')
