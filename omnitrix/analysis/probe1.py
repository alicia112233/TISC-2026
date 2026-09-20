#!/usr/bin/env python3
import socket, struct, subprocess, os, time, threading, sys

BIN = os.path.expanduser('~/omni/omnitrix')
HOST, PORT = '127.0.0.1', 19191
MAGIC = b'OMNI'
LOG = open('/tmp/probe1.out','w')
def log(*a):
    s=' '.join(str(x) for x in a); print(s); LOG.write(s+'\n'); LOG.flush()

env = {**os.environ, 'OMNITRIX_BIND': f'{HOST}:{PORT}', 'RUST_LOG':'debug'}
env.pop('OMNITRIX_MASTER_KEY', None)
srv = subprocess.Popen([BIN], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
def rd():
    for line in srv.stdout:
        log('[SRV]', line.decode('utf-8','replace').rstrip())
threading.Thread(target=rd, daemon=True).start()
time.sleep(1.5)

def conn():
    s=socket.socket(); s.connect((HOST,PORT)); s.settimeout(3); return s
def rall(s,t=2):
    s.settimeout(t); d=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            d+=c
    except: pass
    return d
def txt(b): return ''.join(chr(x) if 32<=x<127 else '.' for x in b)

# frame format candidate: MAGIC + ver(1) + type(1) + opcode(2BE) + seq(8BE) + len(2BE) + payload
def frameA(op, payload=b'', seq=0, ver=1, typ=0):
    return MAGIC + bytes([ver,typ]) + struct.pack('>H',op) + struct.pack('>Q',seq) + struct.pack('>H',len(payload)) + payload

def send1(frame, t=2):
    s=conn(); s.send(frame); r=rall(s,t); s.close(); return r

log('=== single-shot opcode scan (format A) ===')
for op in range(0, 0x60):
    r = send1(frameA(op))
    if r:
        log(f'op 0x{op:04x} -> {txt(r)!r}  | hex[:40]={r[:40].hex()}')
    time.sleep(0.02)

log('\n=== opcode scan with ben.tennyson payload ===')
for op in range(0x40, 0x60):
    r = send1(frameA(op, b'ben.tennyson'))
    if r:
        log(f'op 0x{op:04x}+cred -> {txt(r)!r}')
    time.sleep(0.02)

srv.terminate()
log('DONE')
