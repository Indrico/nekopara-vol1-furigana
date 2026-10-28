"""Send real desktop input to the isolated fixture (DISPLAY must select its X server)."""
import json
from pathlib import Path
import time

from Xlib import X, XK, display
from Xlib.ext import xtest

ROOT = Path(__file__).resolve().parents[1]
fixture = ROOT / 'work/engine-test'
d = display.Display()
root = d.screen().root
window = next(w for w in root.query_tree().children if w.get_wm_name() == 'Furigana engine test')
window.set_input_focus(X.RevertToParent, X.CurrentTime)
d.sync()


def stamps():
    return {n: (fixture / (n + '.bmp')).stat().st_mtime_ns for n in ['on', 'off']}


before = stamps()
key = d.keysym_to_keycode(XK.string_to_keysym('F7'))
xtest.fake_input(d, X.KeyPress, key)
xtest.fake_input(d, X.KeyRelease, key)
d.sync()
time.sleep(.4)
after_key = stamps()
assert after_key['off'] > before['off'], 'F7 input did not disable ruby'
coords = root.translate_coords(window, 0, 0)
xtest.fake_input(d, X.MotionNotify, x=coords.x + 1080, y=coords.y + 24)
xtest.fake_input(d, X.ButtonPress, 1)
xtest.fake_input(d, X.ButtonRelease, 1)
d.sync()
time.sleep(.4)
after_click = stamps()
assert after_click['on'] > after_key['on'], 'Mouse input did not enable ruby'
report = {'before': before, 'after_key': after_key, 'after_click': after_click,
          'keyboard_toggle_passed': True, 'mouse_toggle_passed': True}
(ROOT / 'evidence/gui-input.json').write_text(json.dumps(report, indent=2) + '\n')
print('Keyboard and mouse toggle passed')
