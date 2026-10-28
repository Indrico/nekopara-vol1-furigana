"""Check the isolated engine fixture's output, without relying on GPU screenshots."""
import json
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
fixture = ROOT / 'work/engine-test'
if (fixture / 'failure.txt').exists():
    raise AssertionError((fixture / 'failure.txt').read_text(encoding='utf-16'))
result = (fixture / 'success.txt').read_text(encoding='utf-16')
assert 'TYPEWRITER_POSITION_TIMER_AND_WAIT_PRESERVED' in result
on = Image.open(fixture / 'on.bmp').convert('RGB')
off = Image.open(fixture / 'off.bmp').convert('RGB')
background = off.getpixel((0, 0))
base_changed = sum(a != b for a, b in zip(on.get_flattened_data(), off.get_flattened_data()) if b != background)
changed = sum(a != b for a, b in zip(on.get_flattened_data(), off.get_flattened_data()))
assert base_changed == 0, base_changed
assert changed > 0, 'No ruby pixels appeared'
for name in ['on', 'off', 'button']:
    Image.open(fixture / (name + '.bmp')).save(ROOT / 'evidence' / ('renderer-' + name + '.png'))
name_on = Image.open(fixture / 'name-on.bmp').convert('RGB')
name_off = Image.open(fixture / 'name-off.bmp').convert('RGB')
assert ImageChops.difference(name_on.crop((0,14,name_on.width,name_on.height)), name_off).getbbox() is None, 'Name bitmap changed'
assert name_on.crop((0,0,name_on.width,14)).getbbox() is not None, 'No name ruby pixels'
backlog_on = Image.open(fixture / 'name-backlog-on.bmp').convert('RGB')
backlog_off = Image.open(fixture / 'name-backlog-off.bmp').convert('RGB')
assert ImageChops.difference(backlog_on, backlog_off).getbbox() is not None, 'No backlog ruby pixels'
assert ImageChops.difference(backlog_on.crop((0,8,850,170)), backlog_off.crop((0,8,850,170))).getbbox() is None, 'Backlog name bitmap changed'
for name in ['name-on','name-off','name-shigure-on','name-backlog-on','name-backlog-off']:
    Image.open(fixture / (name + '.bmp')).save(ROOT / 'evidence' / (name + '.png'))
manifest = json.loads((ROOT / 'dist/patch3.build.json').read_text())
report = {'patch_version': manifest['version'], 'patch_sha256': manifest['patch_sha256'],
          'test_mode': 'decoded scripts in stock KiriKiri fixture',
          'engine_checks': result.splitlines(), 'name_bitmap_changed': False, 'backlog_name_bitmap_changed': False,
          'ruby_pixels_changed': changed,
          'base_pixels_changed': base_changed, 'difference_bounds': ImageChops.difference(on, off).getbbox()}
(ROOT / 'evidence/renderer-checks.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
