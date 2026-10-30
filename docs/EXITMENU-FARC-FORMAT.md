# ExitMenu FArC container inspection — Build 19

Input: the five localized `ExitMenu/**/spr_nswgam_menu.farc` files in
`PJDVM39-0.1.5b19-iOS-unsigned.ipa`.

## Verified layout

All five files share the observed 0x30-byte fixed header layout:

| Offset | Width | Observed interpretation |
|---:|---:|---|
| `0x00` | 4 | ASCII magic `FArC` |
| `0x04` | 4 | Big-endian value `36` |
| `0x08` | 4 | Big-endian name-field width `16` |
| `0x0C` | 16 | NUL-padded UTF-8 embedded name: `spr_nswgam_menu.bin` |
| `0x20` | 4 | Big-endian payload offset: `48` (`0x30`) |
| `0x24` | 4 | Big-endian compressed payload length |
| `0x28` | 4 | Big-endian expanded payload length |

The payload begins at byte 48 and is a gzip stream. The compressed-size field
matches the bytes remaining after the header. The expanded-size field matches
the actual gzip output for all five language variants.

## Localized archive measurements

| Language | Archive bytes | Compressed payload bytes | Expanded bytes |
|---|---:|---:|---:|
| Simplified Chinese | 4,512,692 | 4,512,644 | 31,790,320 |
| Traditional Chinese | 4,519,991 | 4,519,943 | 31,790,320 |
| Korean | 4,529,030 | 4,528,982 | 31,790,320 |
| Japanese | 4,531,450 | 4,531,402 | 31,790,320 |
| English | 4,530,184 | 4,530,136 | 31,790,320 |

The five expanded payloads have distinct SHA-256 hashes despite sharing the
same expanded length. The archive contains one embedded filename in the
observed layout. This is evidence for this specific ExitMenu resource family;
it is not enough to claim that every game FArC archive has the same structure.

## Tool

`tools/inspect_single_entry_farc.py` validates this observed variant without
extracting anything by default. To inspect and optionally extract a user's own
archive:

```sh
python3 tools/inspect_single_entry_farc.py spr_nswgam_menu.farc
python3 tools/inspect_single_entry_farc.py spr_nswgam_menu.farc --extract-to /tmp/spr_nswgam_menu.bin
```

The tool verifies the magic, big-endian fields, payload offset/length, gzip
integrity, and expanded size. It does not parse the embedded `.bin` format,
decode textures, or implement an Android resource loader.

## Android porting relevance

This establishes a reproducible first layer for resource ingestion: FArC
header validation and gzip decompression. The next task is to reverse-engineer
the embedded `.bin` structure and identify texture/atlas metadata, then build
a safe asset loader and render a representative ExitMenu element through
Vulkan. No original assets are redistributed in this repository.
