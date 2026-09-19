# Level 5: Trash Talk

## Challenge Information
- **Event**: TISC 2026
- **Level**: Level 5
- **Category**: Network Forensics / Custom Protocol Reverse Engineering (Nintendo DS GTS)

## Description
> The Singularity's agents have been passing messages that we urgently need to intercept.  
> We've traced their traffic to `http://chals.tisc26.ctf.sg:31259/`. They seem to be taking it chill though, seemingly playing Pokémon Platinum.  
> Counter-intelligence has snapped a picture that could help us.

---

## Challenge Files & Artifacts
- [`trash-talk-ds.jpg`]: High-resolution photograph captured by counter-intelligence showing a player on a Nintendo DSi.
- Target Server: `http://chals.tisc26.ctf.sg:31259/`

---

## Technical Reconnaissance & Analysis

### 1. Photo Analysis (`trash-talk-ds.jpg`)
Inspection of the photo reveals key intelligence:
- **Device & Game**: Nintendo DSi running **Pokémon Platinum** (Generation IV, Sinnoh region).
- **Location in Game**: The Global Trade Station (GTS) in Jubilife City.
- **Top Screen Deposit Data**:
  - **Species**: `PORYGON` (National Pokédex #137)
  - **Level**: `25`
  - **Original Trainer (O.T.)**: `AGENT`
  - **Offerer**: `AGENT`
  - **Held Item**: `None`
  - **OT's Location**: `Singapore`

### 2. Server Fingerprinting
Probing the target endpoint at `http://chals.tisc26.ctf.sg:31259/`:
```http
HTTP/1.1 200 OK
Server: Microsoft-IIS/6.0
Content-Type: text/plain
Content-Length: 2

ok
```

The response mimics Nintendo’s official Gen IV Wi-Fi Connection GTS server (`gamestats2.nintendowifi.net`). Official GTS servers ran on Windows Server 2003 with IIS 6.0 and responded with `ok` on root path health checks.

### 3. The Gen IV GTS Protocol
In Generation IV Pokémon games, the Nintendo DS interacts with the GTS using classic HTTP GET/POST queries to ASP endpoints:
- `/pr/search.asp`: Searches available Pokémon deposits by species, gender, country, and requested Pokémon.
- `/pr/result.asp`: Downloads the trade binary payload.
- `/pr/post.asp`: Uploads a deposited Pokémon.

Parameters are typically obfuscated or base64/binary encoded, and the returned data is an encrypted `.pkm` file structure (136 bytes for storage, 236 bytes for party format).

### 4. "Trash Talk" & Pokémon Data Internals
The challenge title **"Trash Talk"** is a direct double-meaning:
1. **Trash Bytes**: In Gen IV games, string buffers (like Nicknames and OT Names) contain 16-bit characters terminated by `0xFFFF`. In legitimate games, the bytes following the terminator are uninitialized memory fragments ("trash bytes"). These bytes are notoriously scrutinized in competitive Pokémon legality checks to determine if a Pokémon was genuinely caught in-game or injected via save editors.
2. **Covert Communication**: The Singularity is using these trash bytes or encrypted block attributes within GTS deposit payloads to exfiltrate secrets covertly across public GTS servers without raising alarms.

---

## Solution Methodology

### 1. Intercepting the Porygon Deposit
Query `/pr/search.asp` or `/pr/result.asp` with species code 137 (Porygon) and country code for Singapore:
```python
import requests

GTS_URL = "http://chals.tisc26.ctf.sg:31259"
# Query the search endpoint for deposited Porygon
# Emulate DS GTS user-agent / query headers
```

### 2. Decrypting the Gen IV PKM Binary
Once the 136-byte or 236-byte Pokémon binary is retrieved:
1. Read the **Personality Value (PID)** (`offset 0x00`, 32-bit integer) and **Checksum** (`offset 0x06`, 16-bit integer).
2. Seed the Gen IV Linear Congruential Generator (LCG):
   $$\text{Seed} = \text{Checksum}$$
   $$\text{Seed}_{n+1} = (\text{Seed}_n \times 0x41C64E6D + 0x6073) \pmod{2^{32}}$$
3. Unshuffle the 4 blocks (A, B, C, D) using the block order index:
   $$\text{Order Index} = \left(\frac{\text{PID} \ \& \ 0x3E000}{0x2000}\right) \pmod{24}$$
4. Decrypt the 128 bytes of block data using the PRNG keystream.

### 3. Recovering the Secret
Inspect the unencrypted fields:
- OT Name buffer and following trash bytes (`offset 0x68` - `0x77`)
- Nickname buffer and trash bytes (`offset 0x48` - `0x5D`)
- Secret ID (SID) and Trainer ID (TID)
- Individual Values (IVs) / Extra ribbon flags

The message transmitted by The Singularity's AGENT contains the flag in `TISC{...}` format.
