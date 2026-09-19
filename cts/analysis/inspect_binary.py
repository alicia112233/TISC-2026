"""Small, read-only helpers for the supplied stripped ELF."""
from pathlib import Path
import argparse
import struct

ROOT = Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument("mode", choices=["disasm", "table"])
parser.add_argument("start", type=lambda x: int(x, 0))
parser.add_argument("end_or_count", type=lambda x: int(x, 0))
args = parser.parse_args()
data = (ROOT / "executor").read_bytes()
if args.mode == "table":
    for i in range(args.end_or_count):
        target = args.start + struct.unpack_from("<i", data, args.start + i * 4)[0]
        print(f"{i:02x}: {target:x}")
else:
    from capstone import Cs, CS_ARCH_X86, CS_MODE_64
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    for ins in md.disasm(data[args.start:args.end_or_count], args.start):
        print(f"{ins.address:08x}: {ins.mnemonic:8} {ins.op_str}")
