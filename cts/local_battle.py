"""Run the supplied Linux executor; convert raw bots to its hex CLI input."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent

def run(a, b, seed=1129599776, rounds=3, ticks=500000):
    paths = []
    with tempfile.TemporaryDirectory(prefix="cts_", dir=ROOT / "analysis") as temp:
        for name, path in [("a", a), ("b", b)]:
            path = Path(path)
            data = path.read_bytes() if path.suffix == ".bin" else bytes.fromhex(path.read_text())
            target = Path(temp) / (name + ".hex")
            target.write_text(data.hex(), encoding="ascii")
            paths.append(str(target))
        args = [str(ROOT / "executor"), *paths, "--seed", str(seed), "--rounds", str(rounds), "--ticks", str(ticks)]
        result = subprocess.run(args, text=True, capture_output=True, timeout=120)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        return json.loads(result.stdout.strip().splitlines()[-1])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("a", type=Path)
    parser.add_argument("b", type=Path)
    parser.add_argument("--seed", type=int, default=1129599776)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--ticks", type=int, default=500000)
    parser.add_argument("--save", type=Path)
    args = parser.parse_args()
    result = run(args.a, args.b, args.seed, args.rounds, args.ticks)
    rendered = json.dumps(result, indent=2)
    if args.save:
        args.save.parent.mkdir(parents=True, exist_ok=True)
        args.save.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
