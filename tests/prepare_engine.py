"""Prepare the isolated fixture after downloading the official KiriKiri Z SDK."""
from pathlib import Path
import shutil
import sys
import re
import os

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get('NEKOPARA_GAME_DIR', ROOT.parent))
sys.path.insert(0, str(ROOT / 'tools'))
from xp3 import Archive, pack

fixture = ROOT / 'work/engine-test'
fixture.mkdir(parents=True, exist_ok=True)
(ROOT / 'evidence').mkdir(exist_ok=True)
sdk = ROOT / 'work/krkrz/krkrz_20171225'
shutil.copyfile(sdk / 'tvpwin32.exe', fixture / 'engine.exe')
shutil.copyfile(GAME / 'plugin/textrender.dll', fixture / 'textrender.dll')
shutil.copyfile(ROOT / 'tests/engine_startup.tjs', fixture / 'startup.tjs')
# The stock 2017 engine expects a BOM for Unicode scripts.
(fixture / 'startup.tjs').write_bytes((ROOT / 'tests/engine_startup.tjs').read_text().encode('utf-16'))
(fixture / 'bootstrap-test.tjs').write_bytes((ROOT / 'runtime/AfterInitFurigana.tjs').read_text().encode('utf-16'))
a = Archive(ROOT / 'dist/patch3.xp3')
scripts = {e['name']: a.read(e).decode('utf-16') for e in a.files}
# The stock SDK has no NEKOPARA archive filter. Test the decoded script payloads
# in a separate plain container, rather than claiming it loads the release XP3.
pack({e['name']: a.read(e) for e in a.files}, fixture / 'payload-test.xp3')
(fixture / 'patch3.xp3').unlink(missing_ok=True)
for entry in a.files:
    (fixture / entry['name']).unlink(missing_ok=True)
for name in ['success.txt', 'failure.txt', 'Furigana-status.txt', 'furigana-status.txt']:
    (fixture / name).unlink(missing_ok=True)
original = Archive(GAME / 'data.xp3')
message = original.read(next(e for e in original.files if e['name'] == 'system/MessageLayer.tjs')).decode('utf-16')
classes = message[message.index('class RelativeLayer'):message.index('class FaceLayer')]
hack = scripts['msghack.tjs']
classes += hack[re.search(r'class\s+CustomNameLayer', hack).start():re.search(r'class\s+CustomMessageLayer', hack).start()]
custom = scripts['custom.tjs']
start = custom.index('NameLayer.processNameImage = function(text)')
classes += custom[start:custom.index('incontextof null;', start) + len('incontextof null;')]
(fixture / 'name-classes.tjs').write_bytes(classes.encode('utf-16'))
(fixture / 'name-tests.tjs').write_bytes((ROOT / 'tests/name_tests.tjs').read_text().encode('utf-16'))
for e in original.files:
    if e['name'].startswith('image/name/jp_name_'):
        (fixture / Path(e['name']).name).write_bytes(original.read(e))
print(fixture)
