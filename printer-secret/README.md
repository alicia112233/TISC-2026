# Level 2: My Printer has a Secret

## Challenge Information
- **Event**: TISC 2026
- **Level**: Level 2
- **Category**: Steganography / Passive OSINT

## Description
> After encountering a few of The Singularity's minions, I got paranoid and started encoding URLs to my secret files with my custom encoding and printing it out. I might have forgotten the password, but I’m pretty sure the printer left it on the page somewhere.
>
> Don’t forget to check out the other available challenge, EXPCalibur, at the top of the page. Be warned — danger lurks. Are you ready to face the horde?

---

## Challenge Files & Artifacts
- [`printer-secret.png`]: Scanned document containing a custom 2D matrix of colored triangles and printer steganography.
- [`analyze_tag.py`]: Script to segment and extract the 36x36 triangle grid color values.
- [`try_bits.py`]: Permutation and bit-unpacking brute-forcer to decode the custom 3-bit symbol stream into ASCII.
- [`triangle_grid.npy`]: Serialized NumPy matrix of sampled palette indices.
- [`secret-archive.zip`]: Encrypted ZIP file downloaded from the recovered server URL.
- [`open_archive.py`]: Unpacks the password-protected ZIP archive using the recovered password.
- [`printer-secret-part2.txt`]: Briefing for Part 2 (OSINT target and questions).
- [`seller-flickr.html`]: Offline snapshot of the seller's Flickr profile.
- [`seller-gunsta-jina.txt`]: Markdown export of the seller's GUNSTA hobby page.
- [`arthoby-profile.png`]: Screenshot of the seller's profile on Arthobycomm.
- [`arthoby-header.jpg`]: Full-resolution header image containing the pet photo.
- [`seller-shop.html`]: Offline snapshot of the seller's BASE shop.
- [`shop-cover.jpg`]: Cover photo featured on the seller's online shop.

---

## Solution Walkthrough

The challenge is solved across two main phases:
1. **Phase 1: Custom Steganography & Archive Decryption**
2. **Phase 2: Passive OSINT Investigation**

---

### Phase 1: Custom Steganography & Archive Decryption

#### 1. Analyzing the Scanned Page
The image `printer-secret.png` exhibits a custom 36x36 matrix composed of small colored triangles, as well as yellow tracking dots (Machine Identification Codes / printer metadata).

The colored triangle symbols use an 8-color palette (`KWROYGBP`):
- `K`: Black `(3, 3, 3)`
- `W`: White `(255, 255, 255)`
- `R`: Red `(243, 120, 118)`
- `O`: Orange `(255, 158, 93)`
- `Y`: Yellow `(244, 212, 96)`
- `G`: Green `(141, 166, 126)`
- `B`: Blue `(131, 179, 218)`
- `P`: Purple `(142, 127, 170)`

Since there are 8 colors ($2^3 = 8$), each triangle encodes a 3-bit symbol. Every 8 symbols unpack into 3 full bytes ($8 \times 3 = 24\text{ bits} = 3\text{ bytes}$).

#### 2. Decoding the Payload
Using `analyze_tag.py` and `try_bits.py`:
- The matrix grid was sampled and mapped into discrete symbol indices.
- Orientations, snake-walk trajectories, bit shifts, and color-to-value permutations were searched to maximize ASCII printability.
- The decoded stream revealed the URL to the secret archive:
  ```text
  https://printer-secret.chals.tisc26.ctf.sg/Fn8u92fhuiWAfeAfGu23dy.zip
  ```

#### 3. Printer Password
Printer tracking dots / steganographic metadata embedded on the printed document encoded the password:
```text
sut0roberi1-fure!b4a_*=^
```

Running [`open_archive.py`] successfully unlocks `secret-archive.zip` and extracts [`printer-secret-part2.txt`].

---

### Phase 2: Passive OSINT Investigation

#### Briefing & Objective
From `printer-secret-part2.txt`:
> I saved the link to this weathered RGM-79[G] model meaning to bid on it, but I never did.  
> I finally checked back on it today, but the listing was deleted! :-(  
> `https://auctions.yahoo.co.jp/jp/auction/d500233180`  
>  
> Help me investigate this seller so I can get in touch!  
> Find the following:  
> 1. What is the seller's flickr username?  
> 2. The seller has an account on a plastic model hobby website. They have a photo featuring their pet. What colour pants are they wearing in that photo?  
> 3. Beyond Yahoo Auctions, the seller sells products on their own shop site. What is the model number of the item featured on the cover photo?  
>  
> The flag format will be `TISC{flickruser_colour_MODELNUMBER}`.

#### 1. Seller Pivot & Identification
- Searching archived Yahoo Auction seller IDs for listing `d500233180` identifies seller aliases `abn22631` / `abn2263123`.
- The seller maintains profiles on GUNSTA (`https://gumpla.jp/author/abn22631`), Twitter/X (`@abn2263123`), and Arthobycomm (`https://arthobycomm.../abn22631`).

#### 2. Answering Question 1: Flickr Username
- The seller's Flickr account has NSID `197582828@N07` (URL: `https://www.flickr.com/people/197582828@N07/`).
- Inside the embedded JSON model data of [`seller-flickr.html`]:
  ```json
  "username": "abn2263123"
  ```
- **Answer 1**: `abn2263123`

#### 3. Answering Question 2: Pet Photo Pants Color
- On the plastic model hobby site Arthobycomm (`arthoby-profile.png`), the user is identified as `abn22631` ("ホビコム移転組です").
- The profile header image ([`arthoby-header.jpg`]) features the seller's pet cat sitting on a chevron rug.
- In the foreground, the seller's leg/knee is clearly visible wearing heathered grey sweatpants.
- **Answer 2**: `grey` (or `gray`)

#### 4. Answering Question 3: Shop Cover Model Number
- The seller runs a BASE shop: `https://abn2263123.base.ec/` (`seller-shop.html`).
- The banner/cover photo featured on the shop ([`shop-cover.jpg`]) displays a customized Gunpla kit with the large overlay text:
  ```text
  MS-18E
  KÄMPFER
  MOBILE SUIT GUNDAM 0080 War in the Pocket
  ```
- **Answer 3**: `MS-18E`

---

## Flag Assembly
Putting all three components together in format `TISC{flickruser_colour_MODELNUMBER}`:

```text
TISC{abn2263123_grey_MS-18E}
```
*(Acceptable alternate spelling: `TISC{abn2263123_gray_MS-18E}`)*