# ExitMenu localization comparison — Build 19

The Build 19 IPA contains five localized ExitMenu resource folders: `cn`, `tw`, `kr`, `jp`, and `en`. Each contains `rom_switch/rom/2d/spr_nswgam_menu.farc`.

A local byte-level comparison of the unpacked BIN files found:

- All five BIN files expand to 31,790,320 bytes.
- All five contain the same 22 literal TXP marker offsets and the same 14 TXP type-2 records.
- The 14 records have matching dimensions, format IDs, and payload boundaries across all five languages.
- Texture payload differences relative to English occur at:
  - Chinese (`cn`): records 2, 3, 4, 5, 6, 7, 10, 11, 12, 13
  - Traditional Chinese (`tw`): records 2, 3, 4, 5, 6, 7
  - Korean (`kr`): records 6, 7
  - Japanese (`jp`): records 6, 7
  - English (`en`): reference; no differences

This is strong evidence that the resource container and TXP record layout are shared across languages while selected texture payloads vary by locale. It does **not** prove every changed payload contains translated text; differences may also include localized glyph atlases, text layout, or other language-specific artwork.

## Why this helps the port

The shared offsets and dimensions mean one parser and one sprite-layout investigation can be reused across all five locales. The locale-specific payload hashes can then select the correct texture content without changing the parser. This is preferable to building separate texture loaders for each language.

## Reproduce

```bash
python3 tools/compare_exitmenu_locales.py /path/to/PJDVM39-0.1.5b19-iOS-unsigned.ipa --out exitmenu_locale_comparison.json
```

The tool validates the five localized FArC containers, expands their gzip members, compares TXP2 record structures, and reports payload SHA-256 differences. It deliberately does not infer undocumented TXP field meanings or claim that all differing records are text.
