#!/usr/bin/env python3
"""
Omnitrix CTF - Targeted protocol probe
Frame format discovered:
  OMNI (4) + version(1) + type(1) + ? (8) + payload_len(2) + str_len(2) + payload

Error message "unknown opcode: 0x0000" shows opcode is in PAYLOAD, not header.
"""
import socket, struct, time, subprocess, os, sys, threading

BINARY = '/mnt/c/Users/alici/Downloads/TISC 2026/omnitrix/omnitrix'
HOST = '127.0.0.1'
PORT = 9999
MAGIC = b'OMNI'

srv = subprocess.Popen(
    [BINARY],
    env={**os.environ, 'OMNITRIX_BIND': f'{HOST}:{PORT}'},
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=False
)

server_output = []
def read_out():
    for line in srv.stdout:
        msg = line.decode('utf-8', errors='replace').rstrip()
        server_output.append(msg)
        print(f'[SRV] {msg}', flush=True)
threading.Thread(target=read_out, daemon=True).start()

time.sleep(2)
print('[*] Server started, beginning protocol analysis...')

def connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.settimeout(5)
    return s

def recv_all(s, timeout=3):
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

def parse_response(data):
    """Parse an OMNI response frame"""
    if len(data) < 6:
        return None
    magic = data[:4]
    version = data[4]
    msg_type = data[5]
    # Try different interpretations
    result = {
        'magic': magic,
        'version': version,
        'type': msg_type,
        'raw': data,
    }
    if len(data) > 14:
        # Try: MAGIC(4) + ver(1) + type(1) + ?(8) + len(2) + str_len(2) + payload
        result['field8'] = data[6:14]
        payload_len = struct.unpack('>H', data[14:16])[0] if len(data) >= 16 else 0
        result['payload_len'] = payload_len
        if len(data) >= 18:
            str_len = struct.unpack('>H', data[16:18])[0]
            result['str_len'] = str_len
            result['payload'] = data[18:18+str_len] if len(data) >= 18+str_len else data[18:]
    return result

def probe(payload, label=''):
    s = connect()
    s.send(payload)
    resp = recv_all(s, 2)
    s.close()
    return resp

def make_frame(opcode, payload=b'', version=1, msg_type=1, seq=0):
    """Build an OMNI request frame"""
    # Format: MAGIC + version + type + seq(8) + payload_len(2) + opcode(2) + payload
    # Try: MAGIC + version(1) + 0 + seq(8) + opcode+payload combined
    header = MAGIC + bytes([version, msg_type]) + struct.pack('>Q', seq)
    # Opcode might be 2 bytes in the payload
    full_payload = struct.pack('>H', opcode) + payload
    full_payload_with_len = struct.pack('>H', len(full_payload)) + full_payload
    return header + full_payload_with_len

def make_frame_v2(opcode, payload=b'', version=1, seq=0):
    """Alternative frame format"""
    # MAGIC + version + opcode(2) + seq + payload
    return MAGIC + bytes([version]) + struct.pack('>H', opcode) + struct.pack('>Q', seq) + struct.pack('>H', len(payload)) + payload

print('\n[*] Testing frame formats with different opcode positions...')

# Test 1: opcode as bytes 6-7 (after magic+ver+type)
for opcode in [0x0001, 0x0002, 0x0010, 0x0050, 0x0051, 0x0052, 0x0053, 0x0100, 0x0200]:
    # Format A: MAGIC(4) + ver(1) + type(1) + opcode(2) + zeros
    frame = MAGIC + b'\x01\x00' + struct.pack('>H', opcode) + b'\x00' * 14
    resp = probe(frame, f'fmt-A-op{opcode:04x}')
    if resp and b'unknown opcode' not in resp:
        print(f'\n!! Interesting response for opcode 0x{opcode:04x} (fmt A):')
        r = parse_response(resp)
        if r:
            print(f'  type={r.get("type")}, payload={r.get("payload")}')
    time.sleep(0.05)

print('\n[*] Testing opcode in different positions...')

# From the error "unknown opcode: 0x0000", the opcode is 0x0000 when we send all zeros
# The header is: MAGIC(4) + ver(1) + type(1) + 8 zeros + ...
# So positions 14-15 in our sent frame are zeros -> opcode = 0x0000
# Therefore opcode is at byte offset 14 (after magic+ver+type+8bytes = 4+1+1+8 = 14)

print('\n[*] Opcode at offset 14 (2 bytes BE)...')
for opcode in range(1, 20):
    # MAGIC(4) + ver(1) + type(1) + seq(8) + opcode(2) + rest
    frame = MAGIC + b'\x01\x00' + b'\x00'*8 + struct.pack('>H', opcode) + b'\x00'*8
    resp = probe(frame, f'off14-op{opcode:04x}')
    if resp:
        r = parse_response(resp)
        payload_str = r.get('payload', b'') if r else b''
        print(f'  opcode 0x{opcode:04x}: type={r.get("type") if r else "?"}, msg={payload_str}')
    time.sleep(0.05)

# Try 0x0052
for opcode in [0x0052, 0x0053, 0x0054, 0x0060]:
    frame = MAGIC + b'\x01\x00' + b'\x00'*8 + struct.pack('>H', opcode) + b'\x00'*8
    resp = probe(frame, f'special-op{opcode:04x}')
    if resp:
        r = parse_response(resp)
        payload_str = r.get('payload', b'') if r else resp
        print(f'\n  opcode 0x{opcode:04x}: type={r.get("type") if r else "?"}, msg={payload_str}')
    time.sleep(0.1)

print('\n[*] Done scanning opcodes')
time.sleep(1)
srv.terminate()
