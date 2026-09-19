# TISC 2026 — CTF Writeups & Artifacts Repository

A comprehensive collection of challenge solutions, research artifacts, decompiled binaries, and exploit solvers for **TISC 2026** (The InfoSecurity Challenge).

---

## Storyline Overview

> **The Singularity** is an elusive cybercriminal syndicate attempting to launch a coordinated campaign across infrastructure, AI systems, and financial networks. As an analyst and investigator, your objective is to track their members, declassify their intelligence, unravel their covert communications, and neutralize their rogue systems across multiple operational levels.

---

## Challenge Overview & Scoreboard

| Level | Challenge Name | Category | Primary Focus / Technique | Status | Flag |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **1** | [**REDACTED**](redacted/README.md) | Forensics / DocSec | Superficial PDF vector redaction bypass | Solved | `TISC{BRO!RedactPDFsProperlyLah!!!}` |
| **2** | [**My Printer has a Secret**](printer-secret/README.md) | Stego / Passive OSINT | 3-bit color triangle decoding & Gunpla OSINT | Solved | `TISC{abn2263123_grey_MS-18E}` |
| **3** | [**Lion City Layover**](lioncity/README.md) | Web / RE / WASM | Next.js maze routing, WebAssembly state verification | Solved | `TISC{w3lc0m3_70_51ng4p0r3_l4h_61}` |
| **4** | [**ZyGPT**](zyGPT/README.md) | AI / Reverse Engineering | SafeTensors neural network weight steganography | Solved | `TISC{h1d3_1t_d33p_th3_w31ghts_d0nt_l13}` |
| **5** | [**Trash Talk**](trash-talk/README.md) | Network / Protocol RE | Nintendo DS Gen IV/V GTS covert communication | Solved | `TISC{p0lyg0n4l_p1d_ch41n_4cr0ss_g3ns}` |
| **Bonus** | [**Capture The System**](cts/README.md) | Custom VM / Bot Arena | Custom bytecode Core War bomber assembly & benchmarks | Locally benchmarked | 90.0% local holdout win rate |
| **Bonus** | [**EXPcalibur**](EXPcalibur/expcalibur-handout/README.md) | Survivor Arena / Bot Programming | VM bot compilation, practice seeds, replay analysis | Handout and tools available | See scoring guide |

---

## Repository Structure

Selected files and directories are shown below; challenge folders also contain supporting captures, probes, and intermediate results.

```text
TISC 2026/
|-- README.md                          # Repository index and challenge tracker
|-- .gitignore                         # Generated caches and large model exclusions
|-- redacted/                          # Level 1: REDACTED
|   |-- README.md
|   `-- TISC-26-091-SINGULARITY.pdf
|-- printer-secret/                    # Level 2: My Printer has a Secret
|   |-- README.md
|   |-- printer-secret.png
|   |-- analyze_tag.py
|   |-- try_bits.py
|   |-- open_archive.py
|   |-- passive_fetch.py
|   |-- secret-archive.zip
|   `-- printer-secret-part2.txt
|-- lioncity/                          # Level 3: Lion City Layover
|   |-- README.md
|   |-- index.html
|   |-- start.json
|   |-- singa_legacy.wasm
|   |-- inspect_challenge.py
|   |-- dump_harbour.py
|   |-- replay_solver.py
|   |-- recover_claim.py
|   |-- claim.txt
|   `-- flag-response.json
|-- zyGPT/                             # Level 4: ZyGPT
|   |-- README.md
|   |-- requirements.txt
|   |-- model_configuration_zygpt.py
|   |-- model_modeling_zygpt.py
|   |-- safetensors_header.json
|   |-- download_weights.py
|   |-- scan_carriers.py
|   |-- solve_flag.py
|   |-- flag_result.json
|   |-- carriers/                      # Local tensor slices (Git-ignored)
|   `-- model/                         # Local model weights (Git-ignored)
|-- trash-talk/                        # Level 5: Trash Talk
|   |-- README.md
|   |-- trash-talk-ds.jpg
|   |-- solve.py                       # Gen IV/V GTS client and decryption
|   |-- stage2.py                      # Final trades and offline flag recovery
|   |-- flag.txt
|   |-- artifacts/                     # Saved trade responses and decoded records
|   `-- research/                      # Downloaded protocol reference source
|-- cts/                               # Capture The System VM and bot workspace
|   |-- README.md
|   |-- RECOVERED_VM.md
|   |-- Capture The System FAQ.pdf
|   |-- executor
|   |-- bot_source.py
|   |-- bot.bin
|   |-- bot.hex
|   |-- cts_asm.py
|   |-- build_bots.py
|   |-- local_battle.py
|   |-- evaluate_bots.py
|   |-- summarize_results.py
|   |-- verify_isa.py
|   |-- submit_bot.py
|   |-- bots/                          # Generated strategies and local opponents
|   `-- analysis/                      # Disassembly, ISA checks, and benchmarks
`-- EXPcalibur/                        # Survivor-arena handout and tools
    |-- EXPcalibur-TISC-Scoring-Guide.pdf
    |-- expcalibur-handout.tgz
    `-- expcalibur-handout/
        |-- README.md                  # Player guide and local workflow
        |-- main-app.js
        |-- flee.exrp                  # Saved replay
        |-- bin/                       # expc-cc compiler and expc-run runner
        |-- bots/                      # Bot source and compiled VM images
        |-- seeds/practice/            # Seven public practice seeds
        |-- tools/analyze_replay.py
        `-- world/                     # Arena generation notes
```

Printer Secret's OSINT evidence and Lion City's JavaScript bundles, images, JSON captures, and WASM replays remain alongside their solvers. ZyGPT also contains tokenizer/configuration files, extraction scripts, diagnostics, and model samples.

Local editor settings (`.vscode/`), Python caches (`__pycache__/`, `*.pyc`), and large model artifacts are excluded by [.gitignore](.gitignore). The ignored model directories shown above may therefore be absent from a fresh clone.

---

## Challenge Summaries

### [Level 1: REDACTED]
- **Prompt Description**:
  > As part of ongoing transparency efforts, files containing information on The Singularity's whereabouts will be declassified and released to the public. Rest assured that any sensitive information will be redacted to protect active investigations, innocent people, and matters of security.
- **Root Cause**: Black rectangle drawing annotations were placed over sensitive paragraphs in `TISC-26-091-SINGULARITY.pdf` without sanitizing or deleting the underlying text stream.
- **Resolution**: Extracting text streams via `pypdf` reveals a base64 string in Section 6 (`VElTQ3tCUk8hUmVkYWN0UERGc1Byb3Blcmx5TGFoISEhfQ==`) which decodes to `TISC{BRO!RedactPDFsProperlyLah!!!}`.

### [Level 2: My Printer has a Secret]
- **Prompt Description**:
  > After encountering a few of The Singularity's minions, I got paranoid and started encoding URLs to my secret files with my custom encoding and printing it out. I might have forgotten the password, but I’m pretty sure the printer left it on the page somewhere.  
  > Don’t forget to check out the other available challenge, EXPCalibur, at the top of the page. Be warned — danger lurks. Are you ready to face the horde?
- **Root Cause**: Custom 3-bit triangular 8-color matrix encoding + printer Machine Identification Codes, leading into a multi-step passive OSINT investigation.
- **Resolution**:
  1. Decoded the 36x36 colored triangle matrix (`analyze_tag.py`, `try_bits.py`) to obtain `https://printer-secret.chals.tisc26.ctf.sg/Fn8u92fhuiWAfeAfGu23dy.zip`.
  2. Extracted password `sut0roberi1-fure!b4a_*=^` from printer tracking dots.
  3. Performed passive OSINT on deleted Yahoo Auction listing `d500233180`:
     - Flickr username: `abn2263123`
     - Pet photo pants color: `grey`
     - Shop cover item model number: `MS-18E` (Kämpfer)
- **Flag**: `TISC{abn2263123_grey_MS-18E}`

### [Level 3: Lion City Layover]
- **Prompt Description**:
  > Your layover begins by the harbour lights, where winding paths hide curious sights. Some routes are walked, some clues are seen, not every treasure glows on screen. Seek the landmarks, the feast, and the orchid's hue, let the postcards guide you through.  
  > The site is online at: `http://chals.tisc26.ctf.sg:57161`  
  > No source code is provided to participants.
- **Root Cause**: Next.js state machine backed by a WebAssembly validation cartridge (`singa_legacy.wasm`).
- **Resolution**:
  1. Navigated three Singapore maze stages (Hawker Food -> Bayfront Landmarks -> Heritage Walk Orchids).
  2. Bypassed embedded anti-LLM honeypot flags.
  3. Replayed valid route states using `recover_claim.py` aligned with tide hint `990` and heritage clue `0x61` to yield claim `1299140fecece2fc00f48f6689b51af4b92e`.
- **Flag**: `TISC{w3lc0m3_70_51ng4p0r3_l4h_61}`

### [Level 4: ZyGPT]
- **Prompt Description**:
  > In its quest to make itself smarter, The Singularity assimilated every AI it encountered. ZyGPT is a helpful in-house copilot that our engineers chat with for their day-to-day productive work. Last week a routine review noticed it behaving oddly.  
  > `http://chals.tisc26.ctf.sg:14172/`
- **Root Cause**: Neural network weight steganography injected into SafeTensors model layers.
- **Resolution**:
  1. Profiled weight tensors against baseline Qwen model weights using `scan_carriers.py`.
  2. Identified low-bit anomalies in carrier layer `model.layers.14.mlp.up_proj.weight` across rows `[125499, 130167, 142680, 151879, 151905]`.
  3. Decrypted extracted payload with key mask `e0933b894d21ebaa2f0eb1e7eeee3a6d` in `solve_flag.py`.
- **Flag**: `TISC{h1d3_1t_d33p_th3_w31ghts_d0nt_l13}`

### [Level 5: Trash Talk]
- **Prompt Description**:
  > The Singularity's agents have been passing messages that we urgently need to intercept. We've traced their traffic to `http://chals.tisc26.ctf.sg:31259/`. They seem to be taking it chill though, seemingly playing Pokémon Platinum. Counter-intelligence has snapped a picture that could help us.
- **Root Cause**: Nintendo DS Generation IV Global Trade Station (GTS) emulation transmitting covert messages within Pokémon data structures.
- **Resolution**:
  1. Identified the emulated IIS 6.0 GTS server mimicking `gamestats2.nintendowifi.net`.
  2. Inspected counter-intelligence photo `trash-talk-ds.jpg` identifying the target trade: Porygon Lv. 25 deposited by AGENT in Singapore.
  3. Recovered the Generation V instructions from Porygon nickname trash bytes, then decoded hidden Porygon2 target PIDs.
  4. Traded a male level-35 Buizel for three Porygon-Z records and decoded the PID-XOR flag fragments with `stage2.py`.
- **Flag**: `TISC{p0lyg0n4l_p1d_ch41n_4cr0ss_g3ns}`
- **Offline recovery** (from the repository root): `python trash-talk/stage2.py --offline`.

### Companion: [Capture The System](cts/README.md)
- **Context**: Autonomous virtual arena bot battle challenge unlocked alongside Level 2.
- **Resolution**:
  1. Fully reversed the custom 16-bit virtual machine architecture (`RECOVERED_VM.md`).
  2. Developed a 4-process distributed bombing bot (`fast_4100_8192` via `bot_source.py`) that replicates across 4 memory quadrants and clears memory with a 4100-byte modular stride.
  3. Achieved a **90.0% win rate (81/90 matches)** against self-built local holdout opponents. The CTS writeup records no live submission.
### Companion: [EXPcalibur](EXPcalibur/expcalibur-handout/README.md)

The separate `EXPcalibur/` directory contains the survivor-arena player handout, original archive, and scoring guide. Its extracted handout includes the `expc-cc` compiler, `expc-run` local runner, example bot sources and binaries, seven practice seeds, and a replay analysis tool. See the linked player guide for compilation, local runs, and grading commands.
