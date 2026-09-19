"""Compare generated bots against local minions using the original executor."""
from pathlib import Path
import argparse
import json
import time
from local_battle import run, ROOT

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", nargs="+", required=True)
    parser.add_argument("--opponents", nargs="+", default=["idle", "bomber_4", "bomber_68", "bomber_1028", "bomber_8196"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[1, 42, 1129599776])
    parser.add_argument("--ticks", type=int, default=500000)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--both-roles", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "benchmark.json")
    args = parser.parse_args()
    rows = []
    start = time.monotonic()
    for candidate in args.candidates:
        wins = ties = losses = 0
        for opponent in args.opponents:
            if candidate == opponent:
                continue
            for seed in args.seeds:
                for reverse in range(2 if args.both_roles else 1):
                    names = [candidate, opponent]
                    if reverse:
                        names.reverse()
                    result = run(*(ROOT / "bots" / (name + ".bin") for name in names), seed=seed, ticks=args.ticks, rounds=args.rounds)
                    role = "B" if reverse else "A"
                    winner = result["winner"]
                    wins += winner == role
                    ties += winner == "tie"
                    losses += winner not in (role, "tie")
                    rows.append({"candidate": candidate, "opponent": opponent, "role": role, "seed": seed, "result": result})
                    print(f"{candidate} vs {opponent} role={role} seed={seed} winner={winner} score={result['score']['total']}", flush=True)
                    args.output.parent.mkdir(parents=True, exist_ok=True)
                    args.output.write_text(json.dumps({"ticks": args.ticks, "rounds": args.rounds, "battles": rows}, indent=2) + "\n")
        print(f"TOTAL {candidate}: {wins} wins, {ties} ties, {losses} losses ({time.monotonic()-start:.1f}s)", flush=True)
