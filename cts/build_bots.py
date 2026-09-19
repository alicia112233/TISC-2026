"""Build probe programs and first local opponents for the recovered VM."""
from pathlib import Path
from cts_asm import Program, wide, ri

OUT = Path(__file__).resolve().parent / "bots"

def baseline(name, words):
    p = Program()
    for word in words:
        p.emit(word)
    p.save(OUT / name)

def bomber(name, step=4, count=1, poison=0, start=0):
    p = Program()
    p.w("auipc", 20, 0)  # absolute own start
    if start:
        p.i("addi", 1, 20, start)
        p.li(4, 0xffff)
        p.r("and", 1, 1, 4)
        p.li(2, 0x10000)
        p.r("or", 1, 1, 2)
    else:
        p.li(1, 0x10000)
    p.li(2, 0x10000)
    p.li(3, poison)
    p.li(4, 0xffff)
    p.label("loop")
    p.r("sub", 5, 1, 20)
    # Skip our own program. Negative distance passes the unsigned comparison.
    guard_index = len(p.words)
    p.i("sltiu", 6, 5, 0)
    p.branch("bnz", 6, "advance")
    for offset in range(count):
        p.i("sw", 3, 1, offset * 4)
    p.label("advance")
    p.i("addi", 1, 1, step)
    p.r("and", 1, 1, 4)
    p.r("or", 1, 1, 2)
    p.branch("jal", 0, "loop")
    from cts_asm import ri
    p.words[guard_index] = ri("sltiu", 6, 5, p.pc + count * 4)
    return p

def distributed(step=68, count=1, fast=False, protect_boot=False, sites=0x1000):
    """Copy a compact bomber to four protected sites and fork three workers."""
    core = Program()
    core.label("loop")
    if protect_boot:
        core.r("sub", 5, 1, 30)
        boot_guard = len(core.words)
        core.i("sltiu", 6, 5, 0)
        core.branch("bnz", 6, "advance")
    core.r("and", 5, 1, 12)
    core.i("addi", 5, 5, -(sites - (count - 1) * 4))
    core.i("sltiu", 6, 5, 64 + count * 4)
    core.branch("bnz", 6, "advance")
    for i in range(count):
        core.i("sw", 0, 1, i * 4)
    core.label("advance")
    core.i("addi", 1, 1, step)
    core.r("and", 1, 1, 4)
    core.r("or", 1, 1, 2)
    core.branch("jal", 0, "loop")
    if core.pc > 64:
        raise ValueError("Distributed core must fit protected 64-byte sites")
    if fast:
        p = Program()
        p.w("auipc", 30, 0)
        p.li(2, 0x10000)
        p.li(4, 0xffff)
        p.li(12, 0x3fff)
        loader_start = len(p.words)
        for i in range(len(core.words)):
            p.i("lw", 14 + i, 30, 0)
        p.li(10, 0x10000 + sites)
        for index in range(4):
            for i in range(len(core.words)):
                p.i("sw", 14 + i, 10, i * 4)
            p.li(1, 0x10000 + index * 16384)
            if index < 3:
                p.w("sys", 0, 2)
                p.i("addi", 10, 10, 16384)
            else:
                p.i("jalr", 0, 10, 0)
        if protect_boot:
            core.words[boot_guard] = ri("sltiu", 6, 5, p.pc + core.pc)
        for i in range(len(core.words)):
            p.words[loader_start + i] = ri("lw", 14 + i, 30, p.pc + i * 4)
        import struct
        data = core.binary()
        for offset in range(0, len(data), 4):
            p.emit(struct.unpack_from("<I", data, offset)[0])
        return p
    p = Program()
    p.w("auipc", 20, 0)
    p.li(2, 0x10000)
    p.li(4, 0xffff)
    p.li(12, 0x3fff)
    for index, target in enumerate([0x11000, 0x15000, 0x19000, 0x1d000]):
        source_index = len(p.words)
        p.i("addi", 21, 20, 0)
        p.li(10, target)
        p.r("add", 22, 10, 0)
        p.li(23, len(core.words))
        p.label(f"copy_{index}")
        p.i("lw", 24, 21, 0)
        p.i("sw", 24, 22, 0)
        p.i("addi", 21, 21, 4)
        p.i("addi", 22, 22, 4)
        p.i("addi", 23, 23, -1)
        p.branch("bnz", 23, f"copy_{index}")
        p.li(1, 0x10000 + index * 16384)
        if index < 3:
            p.w("sys", 0, 2)
        else:
            p.i("jalr", 0, 10, 0)
        p.fixups.append((source_index, "source_ri", 0, "core"))
    p.label("core")
    # Resolve RI label offsets here; the ordinary fixups are all wide branches.
    special = [f for f in p.fixups if f[1] == "source_ri"]
    p.fixups = [f for f in p.fixups if f[1] != "source_ri"]
    for index, _, _, _ in special:
        p.words[index] = ri("addi", 21, 20, p.pc)
    data = core.binary()
    import struct
    for offset in range(0, len(data), 4):
        p.emit(struct.unpack_from("<I", data, offset)[0])
    return p

def probes():
    baseline("crash", [0])
    baseline("idle", [wide("jal", 0, 0)])
    baseline("nop", [0x04000000] * 16 + [wide("jal", 0, -64)])
    p = Program()
    p.li(1, 0x10000)
    p.i("sw", 0, 1, 0)
    p.branch("jal", 0, "end")
    p.label("end")
    p.w("jal", 0, 0)
    p.save(OUT / "store_probe")
    p = Program()
    p.w("auipc", 10, 0)
    p.i("addi", 10, 10, 16)
    p.w("sys", 0, 2)
    p.w("jal", 0, 0)
    p.w("jal", 0, 0)
    p.save(OUT / "fork_probe")
    for step in [4, 68, 1028, 8196]:
        bomber(f"bomber_{step}", step).save(OUT / f"bomber_{step}")

def sweeper(block_words=64, stride_blocks=17, carpet=False):
    """Skip every block occupied by our code, then sweep the other blocks."""
    size = block_words * 4
    if size & (size - 1) or (stride_blocks & 1) == 0:
        raise ValueError("Power-of-two block size and odd stride required")
    p = Program()
    # x31 distinguishes our initial entry from a later carpet traversal.
    p.branch("bnz", 31, "after_code")
    p.w("auipc", 20, 0)
    p.i("addi", 20, 20, -4)
    p.li(21, 0xffffffff ^ (size - 1))
    p.r("and", 22, 20, 21)
    p.r("sub", 7, 20, 22)
    limit_index = len(p.words)
    p.i("addi", 7, 7, 0)
    p.li(1, 0x10000)
    p.li(2, 0x10000)
    p.li(3, wide("jal", 0, 4) if carpet else 0)
    p.li(4, 0xffff)
    if carpet:
        p.li(8, 65536 // size)
    p.label("loop")
    p.r("sub", 5, 1, 22)
    p.r("sltu", 6, 5, 7)
    p.branch("bnz", 6, "advance")
    for offset in range(block_words):
        p.i("sw", 3, 1, offset * 4)
    p.label("advance")
    p.i("addi", 1, 1, size * stride_blocks)
    p.r("and", 1, 1, 4)
    p.r("or", 1, 1, 2)
    if carpet:
        p.i("addi", 8, 8, -1)
        p.branch("bnz", 8, "loop")
        p.li(9, 0x1fffc)
        p.li(3, wide("jal", 0, -65532))
        p.i("sw", 3, 9, 0)
        p.li(31, 1)
        p.i("jalr", 0, 2, 0)
    else:
        p.branch("jal", 0, "loop")
    # The own-code guard jumps here when the execution carpet reaches us.
    p.label("after_code")
    p.w("jal", 0, 4)
    p.words[limit_index] = ri("addi", 7, 7, p.pc + size - 1)
    # Claim execution in skipped protection blocks too: fill padding with nops.
    while p.pc % size:
        p.i("addi", 0, 0, 0)
    if not carpet:
        return p
    # Branch past actual code, but run the no-op padding up to the next block.
    return p

if __name__ == "__main__":
    probes()
    for words in [16, 32, 64, 128]:
        for stride in [1, 17, 61]:
            if words * 4 * stride <= 32767:
                sweeper(words, stride).save(OUT / f"sweeper_{words}_{stride}")
        sweeper(words, 17, carpet=True).save(OUT / f"carpet_{words}")
    for step in [20, 68, 260, 1028, 4100, 8196, 16388]:
        for start in [0, 4096]:
            bomber("", step, start=start).save(OUT / f"small_{step}_{start}")
        distributed(step).save(OUT / f"distributed_{step}")
        distributed(step, fast=True).save(OUT / f"fast_{step}")
        distributed(step, fast=True, protect_boot=True).save(OUT / f"protected_{step}")
    for step in [16, 272, 1040, 4112, 8208]:
        distributed(step, count=4, fast=True).save(OUT / f"burst_{step}")
    for step in [68, 4100, 8196]:
        for sites in [0x800, 0x2000, 0x3000]:
            distributed(step, fast=True, sites=sites).save(OUT / f"fast_{step}_{sites}")
    print("Built", len(list(OUT.glob("*.hex"))), "programs in", OUT)
