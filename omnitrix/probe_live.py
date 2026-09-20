#!/usr/bin/env python3
"""Connect to live challenge via launcher and probe it"""
import socket, struct, subprocess, os, sys, threading, time

MAGIC = b'OMNI'
HOST, PORT = '127.0.0.1', 7878

def frame(op, payload=b'', seq=0):
    return MAGIC + b'\x01\x00' + struct.pack('>H', op) + struct.pack('>Q', seq) + struct.pack('>H', len(payload)) + payload

def recv_all(s, t=10):
    s.settimeout(t)
    d = b''
    try:
        while True:
            c = s.recv(4096)
            if not c: break
            d += c
    except: pass
    return d

def txt(b):
    return ''.join(chr(x) if 32<=x<127 else '.' for x in b)

# Start launcher
print('[*] Starting launcher...')
env = {**os.environ, 'LYLA_USERNAME': 'aliciatangweishan@gmail.com', 
       'LYLA_PASSWORD': 'Aliciatang33!', 'LYLA_LOCAL_PORT': '7878'}
launcher = subprocess.Popen(
    ['/root/omnitrix-connector/launcher.sh'],
    env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False
)

launcher_out = []
def read_launcher():
    for line in launcher.stdout:
        msg = line.decode('utf-8', errors='replace').rstrip()
        launcher_out.append(msg)
        print('[LAUNCH]', msg, flush=True)
threading.Thread(target=read_launcher, daemon=True).start()

# Wait for port to be available
print('[*] Waiting for port 7878...')
ready = False
for i in range(60):
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect((HOST, PORT))
        s.close()
        ready = True
        print(f'[*] Port 7878 is ready after {i+1} seconds!')
        break
    except:
        time.sleep(1)
        print('.', end='', flush=True)

if not ready:
    print('\n[!] Port not ready, checking launcher output...')
    print('\n'.join(launcher_out[-10:]))
    sys.exit(1)

time.sleep(0.5)

# Now probe the live server
print('\n[*] Probing live server...')

# Probe 0x51 (diagnostic)
s = socket.socket()
s.connect((HOST, PORT))
s.settimeout(10)
s.send(frame(0x51, b''))
resp = recv_all(s, 10)
s.close()
print(f'\n[0x51 diagnostic]')
print(f'  hex: {resp.hex()}')
print(f'  str: {txt(resp)}')
print()

# Now try auth then 0x52
# First, find auth from 0x50-0x60 range
print('[*] Probing auth opcodes in 0x50-0x60 range in persistent connection...')
for op in range(0x50, 0x60):
    try:
        s = socket.socket()
        s.connect((HOST, PORT))
        s.settimeout(5)
        s.send(frame(op, b'ben.tennyson'))
        r = recv_all(s, 3)
        s.close()
        t = txt(r)
        if r and b'authenticate' not in r and b'unknown' not in r and b'malformed' not in r:
            print(f'  !! INTERESTING op 0x{op:02x}: {t[:80]}')
        elif r:
            print(f'  op 0x{op:02x}: {t[:60]}')
        time.sleep(0.1)
    except Exception as e:
        print(f'  op 0x{op:02x}: Error: {e}')

print('\n[*] Done!')
launcher.terminate()
