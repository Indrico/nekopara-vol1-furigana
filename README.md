# NEKOPARA Vol.1 Furigana

A toggleable furigana patch for the Japanese text in the Steam edition of NEKOPARA Vol.1. Click **Furigana: ON/OFF** in the upper-right corner or press **F7** to show or hide readings.

**[Download the latest release](https://github.com/Indrico/nekopara-vol1-furigana/releases/latest)**

Version **0.3.0** has been confirmed working in the maintainer's game installation. It adds readings to dialogue, narration, and 16 speaker-name labels with kanji, including 嘉祥（かしょう） and 時雨（しぐれ）. Name readings also appear in the backlog and follow the same toggle. Names already written in kana, such as ショコラ, are left as they are.

The patch contains annotations for 4,102 Japanese strings from 15 scenario files. Compound words receive grouped readings, while okurigana stays outside the ruby. Readings are generated offline with Fugashi/UniDic and explicit name corrections. Python and an internet connection are not required to play.

To install:

1. Close the game and download `NEKOPARA-Furigana-v0.3.0.zip` from Releases.
2. Extract the ZIP and copy **`patch3.xp3`** into the game's main folder, next to `nekopara_vol1.exe`.
3. Keep the original `patch.xp3`, `patch2.xp3`, and all other game files. Replace an earlier version of this furigana patch if present. If another mod already uses `patch3.xp3`, back it up and resolve that conflict before installing.
4. Start the game through Steam, select Japanese, and use the on-screen toggle or **F7**.

Only `patch3.xp3` is needed from the download. The game installation is still required; this patch does not replace it. The existing executable and original archives are not modified.

To uninstall, close the game and remove `patch3.xp3`, or rename it to `patch3.xp3.disabled`.

When initialization succeeds, `Furigana-status.txt` contains `Build=0.3.0` and `Stage=ready`. The status file is written to the game folder, falling back to the save-data folder if necessary. If the toggle does not appear, check that Steam is launching the folder containing the new patch and that `patch2.xp3` is present. Include the status file in a bug report, or state that no status file was created. `Stage=error` includes the initialization error.

This release targets the executable with SHA-256:

```text
24203ca5184df79599c823d00f9c79c95194c62869cc3524c94e431b7b1c5031
```

Other game builds and combinations with other mods have not been verified. Automatic readings can still be wrong in context. Image-based menu text outside the speaker-name labels is not annotated. Maintainer confirmation and focused regression tests do not constitute a complete playthrough of every route or a guarantee for every system.

The following is a renderer-fixture preview, not an in-game screenshot:

![Speaker-name furigana preview](docs/images/name-on.png)

See [building and testing](docs/BUILDING.md), [implementation notes](docs/TECHNICAL.md), and [validation results](docs/VALIDATION.md) for source and test details.

This is an unofficial fan modification. NEKOPARA and its original content belong to their respective owners. The source repository contains patch tooling and runtime additions; game executables, original archives, DLLs, fonts, and extracted game scripts are not included.
