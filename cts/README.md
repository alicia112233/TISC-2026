# Capture The System

The supplied FAQ and executor have been read and reversed. The selected bot is
`bot.bin` (raw bytes) or `bot.hex` (the same program as hex text). Upload either
file to the leaderboard. No live submission has been made.

## Selected bot and local results

`bot_source.py` builds the selected variant, `fast_4100_8192`. It reads the words
of its own compact bomber into registers, writes copies to four arena locations,
and forks three processes. The parent becomes the fourth worker. Each worker
starts bombing a different quarter of the arena with a stride of 4100 bytes.
The stride visits every aligned arena word when reduced modulo 65536. Guards
exclude the four sites occupied by our bomber copies.

The workers write zero words, which crash enemy processes that fetch them.
Copies are placed at `0x12000`, `0x16000`, `0x1a000`, and `0x1e000`. The original
bootstrap can be overwritten after replication; surviving workers continue.
Dispersal lets the bot survive hits to one execution site. Forked workers share
the player's instruction budget, rather than increasing it.

The bot won **81 of 90 matches (90.0%)**, with no ties, on a holdout set of
nine self-built local opponents, five seeds, and both player positions. Every
match used the original executor with three rounds and 500000 ticks per round.
Each match's verdict used the executor's aggregate `winner`, rather than the
last round's scores. The alternative burst bomber won 65 of the same 90 matches.
The selected variant also won 37 of 42 matches in its preceding comparison.

Holdout seeds: `2`, `271828`, `424242`, `3735928559`, `1129599776`.
Opponents: linear and scattered single-process bombers, an unrolled sweeper,
a compact bomber with a displaced start, a slower distributed bomber, the
previous leading fast bomber, and an execution-carpet bot.

These are local synthetic opponents. The result does not establish a win rate
against live participants. The four replica locations are predictable, and
the bot can lose to opponents that target them or destroy the bootstrap early.
Hidden server battle settings may differ from the executor defaults.

## Reproduce on Windows with Ubuntu WSL

From this workspace in PowerShell:

```powershell
python bot_source.py
wsl -d Ubuntu -- bash -lc 'cd /mnt/c/Users/alici/Downloads/cts; python3 local_battle.py bot.bin bots/bomber_68.bin'
```

Run the recovered-ISA behavioral checks:

```powershell
wsl -d Ubuntu -- bash -lc 'cd /mnt/c/Users/alici/Downloads/cts; python3 verify_isa.py'
```

Rebuild all local opponents and reproduce the selected bot's holdout:

```powershell
python build_bots.py
wsl -d Ubuntu -- bash -lc 'cd /mnt/c/Users/alici/Downloads/cts; python3 evaluate_bots.py --candidates fast_4100_8192 --opponents bomber_4 bomber_68 bomber_1028 bomber_8196 sweeper_32_17 small_68_4096 distributed_68 fast_4100 carpet_32 --seeds 2 271828 424242 3735928559 1129599776 --both-roles --output analysis/reproduced_benchmark.json'
python summarize_results.py analysis/reproduced_benchmark.json
```

The builder and runner use only Python's standard library. `analysis/inspect_binary.py`
requires Capstone, which is installed in the Windows Python environment used
for analysis. Linux users can run `local_battle.py`, `evaluate_bots.py`, and
`verify_isa.py` directly from a directory containing the executable executor.
The provided runner itself is intended to run under Linux/WSL.

Disassemble the selected bot using the recovered encoding:

```powershell
python cts_asm.py bot.bin
```

## Submit

Open the official leaderboard at <https://cts.chals.tisc26.ctf.sg/>, sign in
using the private token from the challenge card, and upload `bot.bin` or
`bot.hex`. Keep the token local; the FAQ says not to share it in chat or source.

An optional `submit_bot.py` sends the raw body and content type documented in
the FAQ. It takes the token from the local `CTS_SUBMISSION_TOKEN` environment
variable and sends a submission only when you explicitly run:

```powershell
python submit_bot.py bot.bin
```

The script does not retry pending revisions, cooldowns, or rejected uploads.
It prints the server response so the revision status or error can be checked.

## Files

| File | Purpose |
|---|---|
| `bot.bin`, `bot.hex` | Selected program for upload |
| `bot_source.py` | Rebuild the selected program |
| `RECOVERED_VM.md` | Memory map, encoding, opcode tables, scheduler, and scoring |
| `cts_asm.py` | Assembler helpers and bot disassembler |
| `build_bots.py` | Bot strategies and reproducible synthetic opponents |
| `local_battle.py` | Run the original Linux executor; convert `.bin` to hex |
| `evaluate_bots.py` | Seed/role/opponent benchmarks |
| `summarize_results.py` | Aggregate match wins correctly |
| `verify_isa.py` | Behavioral checks against the original executor |
| `submit_bot.py` | Optional explicit API upload using a local token |
| `analysis/holdout_benchmark.json` | All 180 holdout matches for the two finalists |
| `analysis/holdout_summary.json` | Match counts and results by opponent |
| `analysis/isa_checks.json` | Saved arithmetic, load, scratch, and fork checks |
| `analysis/faq.txt` | Extracted text of the six-page supplied FAQ |
| `analysis/executor.disasm.txt` | Static disassembly from Capstone |
| `analysis/executor.objdump.txt` | Static disassembly from Linux objdump |

There is no flag in the FAQ. The submission token identifies the CTF account;
the challenge scores bot results. Wins matter: draws increase the denominator
of the CTF win rate without adding wins. The full scoring formula and revision
rules are recorded in `RECOVERED_VM.md`.
