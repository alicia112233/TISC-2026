"""Summarize executor benchmark JSON without mistaking final-round scores for wins."""
from pathlib import Path
import argparse
import collections
import json

def summary(path):
    data = json.loads(Path(path).read_text())
    by_bot = collections.defaultdict(collections.Counter)
    by_opponent = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
    for battle in data["battles"]:
        result = battle["result"]
        winner = result["winner"]
        outcome = "wins" if winner == battle["role"] else "ties" if winner == "tie" else "losses"
        by_bot[battle["candidate"]][outcome] += 1
        by_opponent[battle["candidate"]][battle["opponent"]][outcome] += 1
        match = result["match"]
        expected = "A" if match["wins_a"] > match["wins_b"] else "B" if match["wins_b"] > match["wins_a"] else "tie"
        if winner != expected:
            raise ValueError(f"Unexpected match winner: {battle}")
    rows = []
    for name, counts in by_bot.items():
        games = sum(counts.values())
        rows.append({"bot": name, **{k: counts[k] for k in ["wins", "ties", "losses"]}, "games": games,
                     "win_rate": counts["wins"] / games,
                     "opponents": {opp: {k: c[k] for k in ["wins", "ties", "losses"]} for opp,c in by_opponent[name].items()}})
    rows.sort(key=lambda x: (x["win_rate"], x["ties"], -x["losses"]), reverse=True)
    return {"source": str(path), "ticks": data["ticks"], "rounds": data["rounds"], "bots": rows}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("benchmark", type=Path)
    parser.add_argument("--json", type=Path)
    args = parser.parse_args()
    result = summary(args.benchmark)
    for row in result["bots"]:
        print(f"{row['bot']:24} {row['wins']:3} W {row['ties']:3} T {row['losses']:3} L / {row['games']:3} = {row['win_rate']:.1%}")
    if args.json:
        args.json.write_text(json.dumps(result, indent=2) + "\n")
