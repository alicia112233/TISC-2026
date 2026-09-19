# EXPCALIBUR-CTF — Player Handout

A survivor arena where your **bot** plays, not you. You upload a 64 KiB VM image
(`.bin`); the server runs it against a hidden bundle of seeds and ranks you by
total EXP. Everything here runs **offline** — the local runner is the identical
VM + engine the server grades on, so a run that scores locally scores the same
on the server for the same seed.

> **Full reference docs are online at `/docs`** on the game server (the same site
> you downloaded this handout from): the bot language + stdlib and the rules —
> searchable and cross-linked.

## What's in this handout

```
bin/expc-cc          C-like compiler:  mybot.bot  -> mybot.bin
bin/expc-run         local runner: run/grade a .bin (the same VM + engine the server uses)
bots/                the ready-to-upload sample bot (source + compiled .bin)
seeds/practice/      the public practice seeds for local scoring
world/               how the arena map is built (deterministic, built into expc-run)
```

(The full reference docs are online at `/docs` — see the banner above.)

## The iterate -> submit loop

1. **Write** a bot in the stdlib language (see the **Bot API** page at `/docs`).

   ```sh
   bin/expc-cc mybot.bot -o mybot.bin
   ```

2. **Run** it locally on a practice seed, recording a replay:

   ```sh
   bin/expc-run run mybot.bin --seed 0x11111111 --replay out.exrp
   # prints:  seed=0x11111111 exp=... level=... kills=... time_ms=... victory=... end_tick=...
   ```

   The practice seeds live in `seeds/practice/*.seed` (one hex value per file).

3. **Grade** it over all seven public practice seeds (the **median** of the seven
   runs — the same aggregation the server uses over its hidden bundle):

   ```sh
   bin/expc-run grade mybot.bin
   ```

4. **Iterate** entirely offline. The runner is a black box: probe it against the
   practice seeds, read the replays, and refine.

5. **Upload** `mybot.bin` (raw bytecode only — your source never leaves your
   machine). The server queues the job, grades it on the **hidden** seed bundle,
   and publishes a public replay.

## Quick start (upload something in your first minute)

`bots/sample.bin` is already compiled and ready to upload. Try it locally first:

```sh
bin/expc-run run   bots/sample.bin --seed 0x11111111 --replay sample.exrp
bin/expc-run grade bots/sample.bin
```

Then copy `bots/sample.bot` as your template and start iterating.

## Notes

- See the **Rules & Scoring** page at `/docs` for the run shape and ranking.
- Coordinates are integer pixels in `[0, 6144)`. All arithmetic is 32-bit
  wrapping; there are no floats, strings, arrays, or types.
