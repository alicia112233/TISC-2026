# Provenance

Flag: `TISC{r1ch_h34d3r_t0ld_a_l1e_ab0ut_1ts_b1rth}`

The server accepted `repaired.exe` with `status: correct` and the message
`Provenance restored. Flag captured.`

## Findings

The supplied executable is a 424,448-byte x64 PE. Its Rich header reports build
25017 (`0x61b9`) for all nine marked tool records, while the optional header
reports linker version 14.10. The Rich checksum is already valid: `0xae38e859`.
Repairing only the checksum therefore cannot solve the challenge.

The binary contains modern MSVC C++ library code, including formatting/printing
support and newer C++ exception-handling metadata, inconsistent with its old
toolchain claims. Rich headers record compiler/tool product IDs, build numbers,
and object counts; they are XOR-encoded using a checksum.

## Accepted repair

- Replace the build number in each marked Rich entry with 35207 (`0x8987`).
- Preserve all product IDs, counts, entry order, and the unmarked-object entry.
- Recompute the Rich checksum/XOR key: `0x1dc1eef5`.
- Set the PE optional-header linker version to 14.44, matching the build claim.

The Rich record remains at file offsets `0x80..0xe7`. The only changed byte
outside it is the linker minor-version byte at `0x11b` (`10` to `44`). All
sections and executable instructions remain byte-for-byte identical.

Updating only the Rich header was rejected. A candidate with build 34438 and
linker 14.40 was also rejected; the accepted candidate uses the matching pair
35207 / 14.44. Acceptance establishes a valid provenance repair, not recovery
of every exact original compiler version used to build the file.

## Reproduce

Requires Python 3; the repair script uses only the standard library.

```powershell
python provenance/repair.py
curl.exe -F "file=@provenance/repaired.exe" http://chals.tisc26.ctf.sg:53219/submit
```

The script verifies that file length is preserved and all changed bytes lie
within the Rich record or the two linker-version bytes.

## References

- [Challenge protocol](http://chals.tisc26.ctf.sg:53219/about)
- [Rich header format and compiler-ID database](https://github.com/dishather/richprint)
- [Microsoft's explanation of FH4 exception handling](https://devblogs.microsoft.com/cppblog/making-cpp-exception-handling-smaller-x64/)
- [Microsoft STL printing implementation](https://github.com/microsoft/STL/blob/main/stl/inc/print)
