import sys
from replay_solver import ticket, cartridge, run

tok = ticket()
offsets = [int(x, 0) for x in sys.argv[1:]] or [64, 128, 192, 256, 990]
for off in offsets:
    program = b''.join(bytes([0x61, i >> 8, i & 255, 32]) for i in [off, off + 32]) + b'\xff'
    result = run(tok, cartridge(bytes.fromhex('01 2a fe ff'), program), 'dump-' + str(off))
    print('TEXT', off, bytes(result.get('chroma', [])).decode('utf-8', 'replace'), flush=True)
