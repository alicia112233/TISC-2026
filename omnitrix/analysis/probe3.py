#!/usr/bin/env python3
import socket, struct, subprocess, os, time, signal
OUTDIR = '/mnt/c/Users/alici/Downloads/TISC 2026/omnitrix/analysis'
def w(name, data, mode='w'):
    open(OUTDIR+'/'+name, mode).write(data)
w('probe3.out', 'HEARTBEAT starting\n')
BIN = os.path.expanduser('~/omni/omnitrix')
HOST, PORT = '127.0.0.1', 19292
MAGIC = b'OMNI'
# kill orphans
os.system("pkill -f 'omni/omnitrix' 2>/dev/null; sleep 1")
env = {**os.environ, 'OMNITRIX_BIND': f'{HOST}:{PORT}', 'RUST_LOG':'info'}
env.pop('OMNITRIX_MASTER_KEY', None)
srvlog = open(OUTDIR+'/srv3.log','wb')
srv = subprocess.Popen([BIN], env=env, stdout=srvlog, stderr=subprocess.STDOUT)
# wait for listen
ready=False
for _ in range(30):
    try:
        s=socket.socket(); s.settimeout(0.3); s.connect((HOST,PORT)); s.close(); ready=True; break
    except: time.sleep(0.2)
w('probe3.out', f'server ready={ready}\n', 'a')

def rall(s,t=0.25):
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
def send1(frame, t=0.25):
    try:
        s=socket.socket(); s.settimeout(0.5); s.connect((HOST,PORT)); s.send(frame); r=rall(s,t); s.close(); return r
    except Exception as e:
        return b'ERR:'+str(e).encode()
f=open(OUTDIR+'/probe3.out','a')
def log(*a):
    s=' '.join(str(x) for x in a); f.write(s+'\n'); f.flush()

log('=== empty-payload scan 0x00..0x60 ===')
for op in range(0, 0x61):
    r = send1(frameA(op))
    if r: log(f'op 0x{op:04x} -> {txt(r)[:160]!r}')
log('=== +ben.tennyson scan (non-unknown only) ===')
for op in range(0, 0x61):
    r = send1(frameA(op, b'ben.tennyson'))
    if r and b'unknown opcode' not in r and not r.startswith(b'ERR'):
        log(f'op 0x{op:04x}+cred -> {txt(r)[:160]!r}')
log('DONE')
srv.terminate()
try: srv.wait(3)
except: srv.kill()
