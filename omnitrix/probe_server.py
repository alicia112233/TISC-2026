#!/usr/bin/env python3
"""
Omnitrix CTF - Start server and probe protocol
"""
import socket, struct, time, subprocess, os, sys, threading

BINARY = '/mnt/c/Users/alici/Downloads/TISC 2026/omnitrix/omnitrix'
HOST = '127.0.0.1'
PORT = 9999
MAGIC = b'OMNI'

# Start server
print('[*] Starting Omnitrix server...')
srv = subprocess.Popen(
    [BINARY],
    env={**os.environ, 'OMNITRIX_BIND': f'{HOST}:{PORT}'},
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=False
)

# Collect server output in background
server_output = []
def read_output():
    for line in srv.stdout:
        server_output.append(line.decode('utf-8', errors='replace').rstrip())
        print(f'[SRV] {server_output[-1]}', flush=True)
threading.Thread(target=read_output, daemon=True).start()

time.sleep(2)

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(5)
    return s

def recv_frame(s, timeout=5):
    s.settimeout(timeout)
    data = b''
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            data += chunk
    except:
        pass
    return data

def dump(data, label=''):
    if data:
        print(f'  [{label}] ({len(data)} bytes):')
        print(f'    hex: {data.hex()[:200]}')
        readable = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data)
        print(f'    str: {readable[:200]}')
        if data[:4] == MAGIC:
            print(f'    -> MAGIC=OMNI, byte4={data[4]:02x}, byte5={data[5]:02x}')
            if len(data) > 6:
                print(f'    -> rest: {data[6:].hex()[:100]} | {bytes(b if 32<=b<127 else ord(".") for b in data[6:])[:100]}')

def probe(frame, label='test'):
    try:
        s = connect()
        # See if server sends anything first
        banner = b''
        try:
            s.settimeout(0.3)
            banner = s.recv(4096)
        except:
            pass
        s.settimeout(5)
        s.send(frame)
        resp = recv_frame(s, 3)
        s.close()
        if resp:
            print(f'\n[{label}] Sent: {frame[:30].hex()}')
            dump(resp, 'resp')
        return resp
    except Exception as e:
        print(f'[{label}] Error: {e}')
        return b''

print('[*] Starting protocol probe...')

# We know:
# - Magic = OMNI (4 bytes)
# - Server responds with OMNI + something when we send OMNI-prefixed data
# - Error: "malformed frame: bad magic 0x0c000000" when we DON'T use OMNI magic

# First: what happens with OMNI as the only data?
print('\n[*] Test 1: Just OMNI magic')
probe(MAGIC, 'just-OMNI')

# Try OMNI + version byte + opcode + zeros
print('\n[*] Test 2: OMNI + version + opcodes')
for opcode in range(256):
    frame = MAGIC + bytes([0x01, opcode]) + b'\x00' * 14
    resp = probe(frame, f'opcode-{opcode:02x}')
    if resp:
        time.sleep(0.05)

# Try without the inner zero padding - maybe OMNI + 2 bytes is enough
print('\n[*] Test 3: Short frames')
for n in range(0, 20):
    frame = MAGIC + b'\x00' * n
    resp = probe(frame, f'OMNI+{n}zeros')
    if resp:
        pass

# Try OMNI + version 0 (not 1)
print('\n[*] Test 4: Version variations')
for v in range(5):
    for op in [0, 1, 2, 0x52]:
        frame = MAGIC + bytes([v, op]) + b'\x00' * 16
        resp = probe(frame, f'v{v}-op{op:02x}')
        if resp:
            pass

# Maybe the frame has: MAGIC(4) + length(2 or 4) + opcode + payload
print('\n[*] Test 5: OMNI + length prefix')
for lp_size in [2, 4]:
    for op in range(5):
        if lp_size == 2:
            lp = struct.pack('<H', op + 1)
        else:
            lp = struct.pack('<I', op + 1)
        frame = MAGIC + lp + bytes([op]) + b'\x00' * 16
        resp = probe(frame, f'lp{lp_size}-op{op:02x}')
        if resp:
            pass

time.sleep(1)
srv.terminate()
print('\n[*] Done. Server output:', server_output[-5:] if len(server_output) > 5 else server_output)
