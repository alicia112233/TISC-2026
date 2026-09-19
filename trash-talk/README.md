# Level 5: Trash Talk

**Flag:** `TISC{p0lyg0n4l_p1d_ch41n_4cr0ss_g3ns}`

## Reproduce the recovery

From the repository root:

```powershell
python trash-talk/stage2.py --offline
```

This decrypts the saved trade responses, verifies their Pokemon checksums,
recovers the three fragments, and writes `trash-talk/flag.txt`.
Run without `--offline` to repeat the final trades against the challenge server.
The client requires Python and `requests`.

## Challenge

The supplied photo shows Pokemon Platinum's Global Trade Station with a
level-25 Porygon belonging to `AGENT`. The challenge service is
`http://chals.tisc26.ctf.sg:31259/`.

## 1. Porygon nickname trash bytes

The Generation IV search endpoint is
`/pokemondpds/worldexchange/search.asp`. `solve.py` implements the GTS
challenge/response handshake, request encoding, and Pokemon decryption.
Search for species 137, decrypt the 292-byte records, and order the records
by their deposit timestamps (the little-endian 64-bit field at `0xF8`).

Pokemon data uses a checksum-seeded LCG to encrypt the four shuffled 32-byte
blocks. The party extension uses the Pokemon PID as its seed. Every captured
record used below passes its checksum after decryption.

The bytes at `0x58:0x5E`, after the PORYGON nickname's `FFFF` terminator,
contain fragments. Strip zero padding from each fragment and concatenate:

```text
G3N5_BL4CKWH1T3;P0RYG0N2_TR4SH=P1D_L3_X0R_K;K=C3236F27
```

The complete set of ten records is saved in `artifacts/porygon-all.bin`.

## 2. Generation V and the hidden trade targets

Switch to `/syachi2ds/web/worldexchange/search.asp` and search for species
233 (Porygon2). Generation V uses a different request salt and encoding,
and appends a SHA-1 footer to its responses. `solve.py` verifies that footer.
The search body starts with `01 00`, followed by 296-byte records.

Two search results are Ditto decoys with the nickname `NOT ME!`; check the
species in the decrypted Pokemon data, not only the GTS search metadata.
The three real Porygon2 trainer names, in deposit order, are:

```text
0FF3R_M
BU1Z3L
Lv30-40
```

Each Porygon2 has four hidden bytes at `0x5A:0x5E`. Recover the target PID as:

```python
target_pid = int.from_bytes(decoded[0x5A:0x5E], "little") ^ 0xC3236F27
```

| Trainer | Hidden bytes | Target PID |
| --- | --- | --- |
| 0FF3R_M | f5 f1 b4 24 | 3885473490 |
| BU1Z3L | e8 c6 3b 75 | 3055069647 |
| Lv30-40 | 7d 2b df 1e | 3724297306 |

The original `stage2.py` XORed directly with `bytes.fromhex("C3236F27")`.
That reverses the key's byte order relative to the little-endian integer,
producing incorrect target IDs and `02 00` trade failures. The fixed solver
XORs the integers and packs the resulting target as little-endian.

These target IDs exceed the signed 32-bit range accepted by the URL PID
parser. Keep the client's normal PID in the URL and put the target ID in
the binary trade payload.

## 3. Trade a Buizel and decode the flag

Construct a male level-35 Buizel and send a 432-byte payload to
`/syachi2ds/web/worldexchange/exchange.asp`:

```text
296-byte offered Pokemon/GTS record
4-byte target PID (little-endian)
128 zero bytes
4-byte terminator (0x80000000, little-endian)
```

Each successful response contains a 296-byte Porygon-Z record, followed
by the Generation V SHA-1 footer. The three captured response bodies are:

- `artifacts/exchange-3885473490.bin`
- `artifacts/exchange-3055069647.bin`
- `artifacts/exchange-3724297306.bin`

Their trainer name is `P1D_X0R`, and their nickname is `PZ`. XOR the 16 bytes
after the nickname terminator (`0x4E:0x5E`) with the four little-endian PID
bytes repeated four times. In deposit order, this yields:

```text
TISC{p0lyg0n4l_p
1d_ch41n_4cr0ss_
g3ns}
```

The final fragment has zero padding. Remove it and concatenate to recover
the flag above. 

## Protocol references

- [Project Pokemon GTS protocol documentation](https://projectpokemon.org/docs/gen-5/gts-protocol-r19/)
- [pkmnFoundations Generation V handler](https://github.com/mm201/pkmnFoundations/blob/master/gts/syachi2ds.ashx.cs)
- [pkmnFoundations Generation V record layout](https://github.com/mm201/pkmnFoundations/blob/master/library/Wfc/GtsRecord5.cs)

The downloaded reference source files are in `research/`.
