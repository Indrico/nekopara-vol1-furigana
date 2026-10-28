# Building and testing

Use Python 3.12 and a supported, locally installed Steam copy of NEKOPARA Vol.1. The builder checks the executable SHA-256 before reading the archives. It writes a new patch file and leaves the installed game files untouched.

From the repository root, on Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tools\build.py --game "C:\Program Files (x86)\Steam\steamapps\common\NEKOPARA Vol. 1"
```

Replace the game path with the installation shown by Steam's **Manage > Browse local files**. Output is written to `dist/patch3.xp3` and `dist/patch3.build.json`. Close the game before copying the generated patch into the game folder.

On Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/build.py --game /path/to/NEKOPARA
```

The required game inputs are `nekopara_vol1.exe`, `data.xp3`, `patch.xp3`, and `patch2.xp3`. The builder reads the relevant original scripts and Japanese scenario slots, creates readings, applies the runtime changes, and packs seven modified scripts into the NEKOPARA archive format. The manifest records checksums, coverage counts, and unknown readings.

To change a reading, edit `readings_overrides.json`, then rebuild. Proper names such as 嘉祥 and 時雨 have explicit readings. Generated dictionaries and extracted game scripts belong in the ignored `work/` or `dist/` directories, not in Git.

Run the Python tests with the game directory selected:

```powershell
$env:NEKOPARA_GAME_DIR = "C:\path\to\NEKOPARA"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

```sh
NEKOPARA_GAME_DIR=/path/to/NEKOPARA .venv/bin/python -m unittest discover -s tests -v
```

All nine tests run when game inputs and a built `dist/patch3.xp3` are available. A clean source checkout can run three independent tests; six tests requiring a game installation or generated patch are skipped with an explanatory message.

The optional engine fixture needs the game's `plugin/textrender.dll`, the [official KiriKiri Z 1.4.0r2 SDK](https://github.com/krkrz/krkrz/releases/tag/1.4.0r2), and the test dependencies:

```sh
.venv/bin/python -m pip install -r requirements-test.txt
```

Extract the SDK so that `work/krkrz/krkrz_20171225/tvpwin32.exe` exists. Set `NEKOPARA_GAME_DIR` and run `tests/prepare_engine.py`. It prepares `work/engine-test/`, including private copies of the resources needed by the fixture. These files are ignored by Git.

On Windows, run `engine.exe . -debugwin=no` from `work/engine-test/`. On Linux, launch that command with Wine supporting 32-bit applications and a desktop display or Xvfb. The fixture writes `success.txt` or `failure.txt` and native-renderer bitmap exports. Run `tests/check_renderer.py` from the repository root to verify them. `tests/smoke_input.py` sends real F7 and mouse input through X11 to the running fixture selected by `DISPLAY`.

The fixture decodes the generated archive into a separate plain `payload-test.xp3`: the stock SDK does not contain NEKOPARA's archive filter. It validates scripts, name layers, and rendering. Game-loader compatibility is checked separately through archive-format tests and maintainer testing in the actual game.
