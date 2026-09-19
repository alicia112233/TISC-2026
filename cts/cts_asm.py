"""Assembler for the ISA recovered from executor (not RISC-V encoding)."""
from pathlib import Path
import struct

OP = {"addi": 1, "xori": 2, "ori": 3, "andi": 4, "slli": 5,
      "srli": 6, "srai": 7, "slti": 8, "sltiu": 9,
      "lb": 10, "lh": 11, "lw": 12, "lbu": 13, "lhu": 14,
      "sb": 15, "sh": 16, "sw": 17, "bz": 18, "bnz": 19,
      "jal": 20, "jalr": 21, "lui": 22, "auipc": 23, "sys": 63}
FUNC = {"add": 1, "xor": 2, "or": 3, "and": 4, "sll": 5,
        "srl": 6, "sra": 7, "slt": 8, "sltu": 9, "seq": 10,
        "sge": 11, "sgeu": 12, "sub": 13, "mul": 0x101,
        "mulh": 0x102, "mulhsu": 0x103, "mulhu": 0x104,
        "div": 0x105, "divu": 0x106, "rem": 0x107, "remu": 0x108}

def ri(name, rd=0, rs=0, imm=0):
    if not -32768 <= imm <= 65535:
        raise ValueError(f"16-bit immediate out of range: {imm}")
    return (OP[name] << 26) | (rd << 21) | (rs << 16) | (imm & 65535)

def rr(name, rd, a, b):
    return (rd << 21) | (a << 16) | (b << 11) | FUNC[name]

def wide(name, rd=0, imm=0):
    if not -(1 << 20) <= imm < (1 << 21):
        raise ValueError(f"21-bit immediate out of range: {imm}")
    return (OP[name] << 26) | (rd << 21) | (imm & 0x1fffff)

class Program:
    def __init__(self):
        self.words = []
        self.labels = {}
        self.fixups = []
    @property
    def pc(self):
        return 4 * len(self.words)
    def label(self, name):
        if name in self.labels:
            raise ValueError(f"Duplicate label: {name}")
        self.labels[name] = self.pc
    def emit(self, word):
        self.words.append(word)
    def i(self, name, rd=0, rs=0, imm=0):
        self.emit(ri(name, rd, rs, imm))
    def r(self, name, rd, a, b):
        self.emit(rr(name, rd, a, b))
    def w(self, name, rd=0, imm=0):
        self.emit(wide(name, rd, imm))
    def branch(self, name, reg, label):
        self.fixups.append((len(self.words), name, reg, label))
        self.emit(0)
    def li(self, rd, value):
        value &= 0xffffffff
        if value < 32768 or value >= 0xffff8000:
            self.i("addi", rd, 0, value if value < 32768 else value - (1 << 32))
        else:
            self.w("lui", rd, value >> 11)
            if value & 0x7ff:
                self.i("ori", rd, rd, value & 0x7ff)
    def binary(self):
        words = self.words.copy()
        for index, name, reg, label in self.fixups:
            words[index] = wide(name, reg, self.labels[label] - index * 4)
        return b"".join(struct.pack("<I", x) for x in words)
    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = self.binary()
        if not 4 <= len(data) <= 8192:
            raise ValueError(f"Program length {len(data)} outside executor limits")
        path.with_suffix(".bin").write_bytes(data)
        path.with_suffix(".hex").write_text(data.hex() + "\n", encoding="ascii")
        return len(data)

def decode(word):
    op, rd, a, b = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
    imm = word & 65535
    if imm >= 32768:
        imm -= 65536
    if op == 0:
        name = next((k for k,v in FUNC.items() if v == word & 0x7ff), "illegal")
        return f"{name} x{rd}, x{a}, x{b}"
    name = next((k for k,v in OP.items() if v == op), "illegal")
    if name in ("bz", "bnz", "jal"):
        n = word & 0x1fffff
        if n & 0x100000:
            n -= 0x200000
        return f"{name} x{rd}, {n:+}"
    if name in ("lui", "auipc", "sys"):
        return f"{name} x{rd}, {word & 0x1fffff:#x}"
    return f"{name} x{rd}, x{a}, {imm}"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("program", type=Path)
    args = parser.parse_args()
    data = args.program.read_bytes() if args.program.suffix == ".bin" else bytes.fromhex(args.program.read_text())
    for offset in range(0, len(data) - 3, 4):
        word = struct.unpack_from("<I", data, offset)[0]
        print(f"{offset:04x} {word:08x} {decode(word)}")
