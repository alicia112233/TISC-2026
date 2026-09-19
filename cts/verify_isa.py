"""Behavioral checks of recovered semantics against the original executor."""
from cts_asm import Program
from local_battle import ROOT, run

def arithmetic():
    p = Program()
    p.li(1, 123)
    p.li(2, 7)
    p.r("add", 3, 1, 2)
    p.li(5, 130)
    p.r("seq", 4, 3, 5)
    p.branch("bnz", 4, "ok")
    p.w("jal", 0, 0)
    p.label("ok")
    p.li(1, 0x10000)
    p.i("sw", 0, 1, 0)
    p.w("jal", 0, 0)
    return p

def narrow_load():
    p = Program()
    p.li(1, 0x80ff)
    p.i("sw", 1, 0, 0)
    p.i("lb", 2, 0, 0)
    p.li(3, 0xffffffff)
    p.r("seq", 4, 2, 3)
    p.branch("bz", 4, "fail")
    p.i("lbu", 2, 0, 0)
    p.li(3, 255)
    p.r("seq", 4, 2, 3)
    p.branch("bz", 4, "fail")
    p.i("lh", 2, 0, 0)
    p.li(3, 0xffff80ff)
    p.r("seq", 4, 2, 3)
    p.branch("bz", 4, "fail")
    p.i("lhu", 2, 0, 0)
    p.li(3, 0x80ff)
    p.r("seq", 4, 2, 3)
    p.branch("bz", 4, "fail")
    p.li(1, 0x10000)
    p.i("sw", 0, 1, 0)
    p.label("fail")
    p.w("jal", 0, 0)
    return p

def shared_scratch():
    p = Program()
    p.w("auipc", 10, 0)
    p.i("addi", 10, 10, 24)
    p.w("sys", 0, 2)
    p.li(1, 1)
    p.i("sb", 1, 0, 0)
    p.w("jal", 0, 0)
    p.label("wait")
    p.i("lbu", 1, 0, 0)
    p.branch("bz", 1, "wait")
    p.li(1, 0x10000)
    p.i("sw", 0, 1, 0)
    p.w("jal", 0, 0)
    return p

def fork_limit():
    p = Program()
    p.w("auipc", 10, 0)
    p.i("addi", 10, 10, 36)
    for _ in range(7):
        p.w("sys", 0, 2)
    p.w("jal", 0, 0)
    return p

if __name__ == "__main__":
    checks = []
    for name, builder in [("arithmetic", arithmetic), ("narrow_load", narrow_load), ("shared_scratch", shared_scratch), ("fork_limit", fork_limit)]:
        p = builder()
        path = ROOT / "analysis" / ("probe_" + name)
        p.save(path)
        result = run(path.with_suffix(".bin"), ROOT / "bots" / "idle.bin", seed=314159, rounds=1, ticks=1000)
        writes = result["score"]["last_write"]["A"]
        processes = result["players"]["A"]["processes"]
        assert processes["crashed"] == 0, (name, processes)
        if name == "fork_limit":
            assert processes["total"] == 4, processes
        else:
            assert writes == 4, (name, writes)
        checks.append({"name": name, "result": result})
        print("PASS", name, "writes=", writes, "processes=", processes["total"])
    import json
    (ROOT / "analysis" / "isa_checks.json").write_text(json.dumps(checks, indent=2) + "\n")
