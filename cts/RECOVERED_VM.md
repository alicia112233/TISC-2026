# Capture The System: recovered executor specification

These notes come from the supplied FAQ, static disassembly of `executor`, and
behavioral probes run with that exact executable. They do not establish the
live server's hidden evaluation parameters or opponents.

Executor SHA-256:
`4d68eb0cf10a2d0f90f7e62455cd26309882279e550d914a8c4823585d046c9e`.

## Local execution and input format

The binary is a stripped, dynamically linked Linux x86-64 ELF built with Rust.
It runs under the available Ubuntu WSL installation.

```text
executor [OPTIONS] <PLAYER_A> <PLAYER_B>
--seed    default 1129599776 (0x43545320)
--rounds  default 3
--ticks   default 500000
```

The local CLI reads both paths as hexadecimal **text**, including paths named
`.bin`. Raw binary bytes fail that parser. The leaderboard/API supports raw
binary separately, as the FAQ describes. `local_battle.py` converts either
`.bin` or `.hex` into temporary hex files before invoking the CLI.

Program length must be between 4 and 8192 bytes. Programs are loaded at random,
non-overlapping, 4-byte-aligned offsets within a 65536-byte arena. Their initial
PC is `0x10000 + load_offset`. Placement is affected by both program lengths,
the seed, placement order, and any rejected overlapping placements.

## Memory and processes

| Address range | Meaning |
|---|---|
| `0x00000000..0x000000ff` | 256 bytes of scratch memory shared by one player's processes |
| `0x00000100..0x0000ffff` | Unmapped |
| `0x00010000..0x0001ffff` | 64 KiB shared arena, including both programs |
| Other addresses | Unmapped |

Arena and scratch start zeroed. Loading a program does not claim write points.
Arena code can be read and overwritten by either player; instruction fetch uses
the current memory contents. Scratch accesses do not claim arena points.

Each process has 32 initially zero 32-bit registers, a PC, and a state.
Writes to register `x0` are discarded. Reads of `x0` return zero. Each player
starts with one process and can have at most four process slots. Fork can reuse
a crashed slot. Registers are copied into the child; scratch remains shared.

Instruction fetch requires a 4-byte-aligned PC and a complete word within the
arena. Loads and stores require natural alignment and a complete access within
one mapped region. Invalid instructions and invalid memory accesses crash the
current process, rather than directly ending the opponent's game.

## Instruction encoding

Every instruction is one **little-endian 32-bit word**. This is a custom encoding
with operations similar to RISC-V; a RISC-V assembler will not produce bots.

```text
31       26 25       21 20       16 15       11 10          0
+----------+-----------+-----------+-----------+-------------+
| opcode   | rd        | rs1       | rs2       | function    | register form
+----------+-----------+-----------+-----------+-------------+
| opcode   | rd        | rs1       | imm16                   | immediate form
+----------+-----------+-----------+-------------------------+
| opcode   | rd        | imm21                               | wide form
+----------+-----------+-------------------------------------+
```

Immediate arithmetic and load/store offsets sign-extend `imm16`. Shifts use the
low five bits of the shift amount. Register arithmetic wraps modulo `2^32`.
For stores, the `rd` field identifies the source register. For conditional
branches, it identifies the condition register.

| Opcode | Operation | Behavior |
|---|---|---|
| `0x00` | Register operation | Function table below |
| `0x01` | `addi` | `rd = rs1 + sext(imm16)` |
| `0x02` | `xori` | XOR with sign-extended immediate |
| `0x03` | `ori` | OR with sign-extended immediate |
| `0x04` | `andi` | AND with sign-extended immediate |
| `0x05` | `slli` | Logical left shift |
| `0x06` | `srli` | Logical right shift |
| `0x07` | `srai` | Arithmetic right shift |
| `0x08` | `slti` | Signed less-than, result 0 or 1 |
| `0x09` | `sltiu` | Unsigned less-than against sign-extended immediate |
| `0x0a` | `lb` | Signed byte load |
| `0x0b` | `lh` | Signed halfword load |
| `0x0c` | `lw` | 32-bit load |
| `0x0d` | `lbu` | Unsigned byte load |
| `0x0e` | `lhu` | Unsigned halfword load |
| `0x0f` | `sb` | Byte store |
| `0x10` | `sh` | Halfword store |
| `0x11` | `sw` | Word store |
| `0x12` | `bz` | If register `rd` is zero, `PC += sext(imm21)` |
| `0x13` | `bnz` | If register `rd` is nonzero, same relative branch |
| `0x14` | `jal` | `rd = PC + 4`, then `PC += sext(imm21)` |
| `0x15` | `jalr` | Link; target `(rs1 + sext(imm16)) & ~1` |
| `0x16` | `lui` | `rd = imm21 << 11` |
| `0x17` | `auipc` | `rd = PC + (imm21 << 11)` |
| `0x18..0x3e` | Invalid | Crash |
| `0x3f` | System operation | `imm21=1`: yield; `imm21=2`: fork; other values advance PC |

Branches are relative to the current instruction's PC, **not** the next PC.
Normal instructions advance PC by four. `jalr` clears bit zero but its target
must still be 4-byte aligned for execution.

System fork advances the parent's PC by four and starts the child at the
address in **`x10`**. It copies the parent's registers. At the process limit,
fork simply advances without creating another slot. A yield marks the current
process yielded; yielded processes are reactivated when that player is next
selected by the scheduler.

| Function | Register operation |
|---|---|
| `0x001` | `add` |
| `0x002` | `xor` |
| `0x003` | `or` |
| `0x004` | `and` |
| `0x005` | `sll` |
| `0x006` | `srl` |
| `0x007` | `sra` |
| `0x008` | `slt` (signed) |
| `0x009` | `sltu` (unsigned) |
| `0x00a` | `seq` (equal) |
| `0x00b` | `sge` (signed greater-or-equal) |
| `0x00c` | `sgeu` (unsigned greater-or-equal) |
| `0x00d` | `sub` |
| `0x101` | `mul` (low word) |
| `0x102` | `mulh` (signed high word) |
| `0x103` | `mulhsu` (signed first operand, unsigned second) |
| `0x104` | `mulhu` (unsigned high word) |
| `0x105` | `div` (signed) |
| `0x106` | `divu` (unsigned) |
| `0x107` | `rem` (signed) |
| `0x108` | `remu` (unsigned) |

Other register functions crash. Division by zero produces `0xffffffff`;
remainder by zero returns the dividend. Signed minimum divided by -1 returns
the signed minimum, with remainder zero. These division edge cases were
recovered statically; the saved dynamic checks cover other operations.

Examples: `00000000` crashes (register function zero is invalid);
`00000004` is hex **byte text** for `addi x0,x0,0`; `00000050` is a
stationary `jal x0,0` loop. `04000050` advances by four via `jal x0,+4`.

## Scheduling, randomness, and victory

Players alternate scheduler selections, with a randomized initial selection.
Runnable processes rotate within each player. A scheduler call executes at most
one VM instruction. `--ticks N` allows up to `2*N` calls per round. A crashed
player does not grant the other player its unused selections. The round can
stop early when neither player has a surviving process.

The PRNG is xorshift32 with left/right/left shifts 13, 17, and 5; a zero state
is replaced by `0x43545320`. The round seed sequence uses the same transform.
Rounds reset programs, memory, and process state, with new placements.

For each arena byte, the executor records the last player to fetch that byte
as part of an instruction and the last player to write it. Fetch claims all
four instruction bytes **before** decoding, so even a fetched invalid opcode
earns execution ownership. Rewriting the same value still claims write ownership.
Reading arena data with a load earns neither kind of ownership.

```text
round_score(player) = last_execution_bytes(player) + last_write_bytes(player)
```

The larger score wins the round; equal scores tie. The match winner has more
round wins, with a tie if round-win counts are equal. The final JSON's `score`
describes **only the final round**. A bot can win the match while losing that
round. Use the JSON `winner` and `match.wins_a/wins_b/ties` when benchmarking.

The `execution_delta` and `write_delta` fields instead report the sign of
cumulative per-byte A-minus-B event counts. They are diagnostic and do not
decide round scores. Process survival and crash counts also are not the score.

## Evidence and tools

Static anchors in the ELF virtual-address disassembly:

- `0x64350`: initialize arena, score arrays, scratch/player state.
- `0x64650`, `0x64a40`: placement order and random non-overlapping placement.
- `0x64760`: copy program and create an initially zeroed process.
- `0x65350`: match/session validation; 4-byte minimum and `0x2000` maximum.
- `0x65960`: scheduler and process selection.
- `0x6609a`: fetch four bytes and claim execution ownership.
- `0x66223`, table at `0x9ba98`: opcode dispatch.
- Table at `0x9bb98`: register-function dispatch.
- `0x6668a`: system operations; `0x66e03`: process cap/reuse logic.
- `0x64bf0`: score tallies; `0x66016`: round-score comparison.

`verify_isa.py` passed arithmetic/branch, signed and unsigned narrow-load,
fork/shared-scratch, and four-process-limit checks against the original binary.
Results are saved in `analysis/isa_checks.json`. Separate store and fork probes
are also saved. Benchmarks always invoke the original executor, not an emulator.

## Competition rules from the FAQ

Upload `.bin` or `.hex` through the leaderboard. API submissions are
`POST /api/v1/submissions`, with `Authorization: Bearer <private token>`.
Use raw binary with `Content-Type: application/octet-stream`, or direct hex
text with `Content-Type: text/plain`; do not send JSON or multipart.

Only one revision can be pending. An active revision remains active until the
pending one finishes evaluation; the previous revision is then retired.
Identical active-program uploads are rejected. Respect the uploader's cooldown,
deadline, pause, and pending status. Standings are published in completed sweeps.
The table retains the newest result per team pair, rather than lifetime totals.

Live rank orders wins, then ties, then fewer losses, then earlier active
submission, then ascending team ID. CTF scoring uses equal game totals:

```text
win_rate = wins / games                  # zero if games is zero
deduction = min(win_rate, tie_position * 0.0004)
points = 100 + 4900 * (win_rate - deduction)
```

Within equal-win-rate groups, tie position follows leaderboard order starting
at zero. Draws count as games and do not add wins. Platform rounding uses
half-up rounding of `points / 5000` to four decimal places. Broadcast battles
are exhibitions and do not affect scoring. Live parameters and opponents
still need validation through actual submissions; the local defaults are not
a promise of the server configuration.
