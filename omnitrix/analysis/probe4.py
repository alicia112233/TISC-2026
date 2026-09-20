#!/usr/bin/env python3
import socket, struct, subprocess, os, time
OUTDIR = '/mnt/c/Users/alici/Downloads/TISC 2026/omnitrix/analysis'
BIN = os.path.expanduser('~/omni/omnitrix')
HOST, PORT = '127.0.0.1', 19393
MAGIC = b'OMNI'
os.system("pkill -f 'omni/omnitrix' 2>/dev/null; sleep 1")
env = {**os.environ, 'OMNITRIX_BIND': f'{HOST}:{PORT}', 'RUST_LOG':'debug'}
env.pop('OMNITRIX_MASTER_KEY', None)
srv = subprocess.Popen([BIN], env=env, stdout=open(OUTDIR+'/srv4.log','wb'), stderr=subprocess.STDOUT)
for _ in range(30):
    try:
        s=socket.socket(); s.settimeout(0.3); s.connect((HOST,PORT)); s.close(); break
    except: time.sleep(0.2)

f=open(OUTDIR+'/probe4.out','w')
def log(*a):
    s=' '.join(str(x) for x in a); f.write(s+'\n'); f.flush()
def txt(b): return ''.join(chr(x) if 32<=x<127 else '.' for x in b)
def frame(op, payload=b'', seq=0, ver=1, typ=0):
    return MAGIC + bytes([ver,typ]) + struct.pack('>H',op) + struct.pack('>Q',seq) + struct.pack('>H',len(payload)) + payload
def rall(s,t=0.4):
    s.settimeout(t); d=b''
    try:
        while True:
            c=s.recv(4096)
            if not c: break
            d+=c
    except: pass
    return d

# One-shot auth format discovery for op 0x10
cred = b'ben.tennyson'
formats = {
  'u16len+cred': struct.pack('>H',len(cred))+cred,
  'u32len+cred': struct.pack('>I',len(cred))+cred,
  'u8len+cred': bytes([len(cred)])+cred,
  'raw cred': cred,
  'u16+cred+u16pad': struct.pack('>H',len(cred))+cred+struct.pack('>H',0),
}
log('### op 0x10 auth format discovery (fresh conn each) ###')
for name,pl in formats.items():
    try:
        s=socket.socket(); s.settimeout(0.6); s.connect((HOST,PORT))
        s.send(frame(0x10, pl)); r=rall(s); s.close()
        log(f'[{name}] payload={pl.hex()} -> {txt(r)[16:]!r}')
    except Exception as e:
        log(f'[{name}] ERR {e}')

# Now: pick a format, auth on persistent conn, then probe privileged ops
log('\n### persistent-session exploration ###')
def session_test(authpl, label):
    try:
        s=socket.socket(); s.settimeout(0.8); s.connect((HOST,PORT))
        s.send(frame(0x10, authpl, seq=1)); r=rall(s); 
        log(f'[{label}] AUTH resp -> {txt(r)[16:]!r}')
        seqn=2
        for op in [0x20,0x21,0x22,0x40,0x41,0x50,0x52,0x53,0x30,0x31,0x60,0x11,0x12,0x13]:
            s.send(frame(op, b'', seq=seqn)); seqn+=1
            rr=rall(s,0.3)
            if rr: log(f'   op 0x{op:02x} -> {txt(rr)[16:]!r}')
        s.close()
    except Exception as e:
        log(f'[{label}] ERR {e}')

for name,pl in formats.items():
    session_test(pl, name)

log('DONE')
srv.terminate()
try: srv.wait(3)
except: srv.kill()
