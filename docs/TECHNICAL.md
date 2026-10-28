# Implementation notes

The supported game uses KiriKiri/KAG scripts inside XP3 archives. Its archives use an `eliF` name mapping, MD5 hashes of lowercase UTF-16LE paths, and a checksum-derived XOR filter. A plain XP3 accepted by the stock SDK is insufficient for this build. Version 0.2 corrected the archive format, and the maintainer confirmed that the game then loaded the toggle successfully.

`tools/xp3.py` reads chained indexes, verifies Adler-32 checksums, decodes the original content filter, and writes the matching protected format. `tools/psb.py` reads PSB v2 structures to select explicit Japanese language slots. `tools/name_readings.py` derives ruby spans from the Japanese speaker-name table and original image bounds.

`tools/build.py` applies focused changes to original scripts from the user's own installation. The seven generated entries are:

| Entry | Purpose |
| --- | --- |
| `AfterInit.tjs` | Load the runtime and write initialization status. |
| `Furigana.tjs` | Reading tables, toggle UI, key handling, and name helpers. |
| `TextRender.tjs` | Toggle native ruby drawing and keep it clear of base glyphs. |
| `rendermsgwin.tjs` | Annotate dialogue and redraw without advancing the typewriter. |
| `backlog.tjs` | Rebuild cached text blocks after the toggle changes. |
| `msghack.tjs` | Add ruby above name images and preserve name-layout state. |
| `custom.tjs` | Draw speaker-name readings on backlog stamps. |

The engine already understands ruby markup such as `[reading]` and `[reading,additional-character-count]`. The patch supplies readings to that renderer. Kana, okurigana, existing ruby, and formatting commands are preserved.

Speaker names use images. The patch adds a 14-pixel band above a name layer and compensates for its anchor, keeping original bitmap pixels at their previous screen position. Layout and current-name metadata are carried through layer storage, restoration, and image assignment to prevent cumulative offsets. Backlog readings use the space above the original stamp.

F7 has repeat suppression, and the preference uses the game's existing system settings. Original scenario text remains the source of redraw operations; scenario archives on disk are not rewritten.

References used during implementation:

- [REA workflow and tooling](https://github.com/morluto/rea)
- [XP3 encryption reference](https://github.com/awaken1ng/krkr-xp3/blob/master/structs/file.py)
- [PSB parsing reference: FreeMote](https://github.com/UlyssesWu/FreeMote/blob/master/FreeMote.Psb/Psb.cs)
- [KiriKiri Z](https://github.com/krkrz/krkrz)

Format details were checked against local game files. Original script notices are retained in generated script entries. These references are not vendored into the source repository.
