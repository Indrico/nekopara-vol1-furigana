# NEKOPARA Vol.1 Furigana v0.3.0

First public release, confirmed working in the maintainer's game installation.

- Toggle Japanese furigana with **F7** or the on-screen **Furigana: ON/OFF** button.
- Readings for dialogue and narration, covering 4,102 Japanese strings from 15 scenarios.
- Readings for 16 kanji speaker-name labels, including 嘉祥（かしょう） and 時雨（しぐれ）, with backlog support.
- Offline annotations, grouped compound readings, preserved okurigana, and corrected character names.
- The original executable and archives remain untouched.

Download **NEKOPARA-Furigana-v0.3.0.zip**, close the game, and copy its `patch3.xp3` next to `nekopara_vol1.exe`. Keep the original `patch.xp3`, `patch2.xp3`, and all other game files. Launch through Steam and select Japanese. No Python installation or internet connection is needed to play.

Upgrade by replacing the previous furigana `patch3.xp3`. To uninstall, remove it or rename it to `patch3.xp3.disabled`. If another mod uses the same filename, back it up and resolve that conflict before installing.

Validation includes nine Python tests, independent archive decryption/checksums, all seven scripts compiled in the engine fixture, all 4,102 strings preserving base text, native name-layer and typewriter checks, and real mouse/keyboard input. Other game builds and mod combinations are unverified, and automatically generated readings may still need contextual corrections.

See the [README](https://github.com/Indrico/nekopara-vol1-furigana#readme) for compatibility, troubleshooting, source, and build instructions. Checksums and the build manifest are attached to this release.
