"""Build a removable furigana patch from the locally owned game files."""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

from fugashi import Tagger
from xp3 import Archive, pack
from psb import scene_texts
from name_readings import name_readings

ROOT = Path(__file__).resolve().parents[1]
GAME_SHA256 = '24203ca5184df79599c823d00f9c79c95194c62869cc3524c94e431b7b1c5031'
KANJI = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]')
RUNS = re.compile(r'[\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]+|[^\u3400-\u4dbf\u4e00-\u9fff々〆ヵヶ]+')
# The renderer's control language must never go through the tokenizer.
CONTROL = re.compile(r'\\.|\[[^\]]*\]|%[fibsdwDp][^;]*;|%\d+;|%[bi se][012]?|%[BSC RLr]|#[0-9a-fA-F]{6};|\$[^;]*;|&[^;]*;'.replace(' ', ''))


def hiragana(text):
    return ''.join(chr(ord(c) - 0x60) if '\u30a1' <= c <= '\u30f6' else c for c in text)


def align(surface, reading):
    runs = RUNS.findall(surface)
    match = re.fullmatch(''.join('(.+?)' if KANJI.search(r) else re.escape(hiragana(r)) for r in runs), reading)
    if not match:
        return [(surface, reading)]
    groups = iter(match.groups())
    return [(r, next(groups)) if KANJI.search(r) else r for r in runs]


def ruby(base, reading):
    # TagTextConverter.parseCh uses length-1 as the additional character count.
    return '[' + reading + (',' + str(len(base) - 1) if len(base) > 1 else '') + ']' + base


class Annotator:
    def __init__(self, overrides):
        self.tagger = Tagger()
        self.overrides = overrides
        self.names = re.compile('(' + '|'.join(re.escape(x) for x in sorted(overrides, key=len, reverse=True) if len(x) > 1) + ')')
        self.unknown = set()
        self.words = {}

    def plain(self, text):
        out = []
        for fragment in self.names.split(text):
            if fragment in self.overrides:
                tokens = [(fragment, self.overrides[fragment])]
            else:
                tokens = [(t.surface, self.overrides.get(t.surface) or hiragana(t.feature.kana or '')) for t in self.tagger(fragment)]
            cursor = 0
            for surface, reading in tokens:
                start = fragment.index(surface, cursor)
                out.append(fragment[cursor:start])
                cursor = start + len(surface)
                if not KANJI.search(surface):
                    out.append(surface)
                elif not reading or reading == '*':
                    self.unknown.add(surface)
                    out.append(surface)
                else:
                    parts = align(surface, reading)
                    value = ''.join(p if isinstance(p, str) else ruby(*p) for p in parts)
                    self.words.setdefault(surface, value)
                    out.append(value)
            out.append(fragment[cursor:])
        return ''.join(out)

    @lru_cache(maxsize=None)
    def annotate(self, text):
        result = []
        cursor = 0
        protected = 0
        for match in CONTROL.finditer(text):
            segment = text[cursor:match.start()]
            result.append(segment[:protected] + self.plain(segment[protected:]))
            protected = max(0, protected - len(segment))
            control = match.group()
            result.append(control)
            if control.startswith('['):
                count = re.search(r',([0-9]+)\]$', control)
                protected = int(count[1]) + 1 if count else 1
            cursor = match.end()
        segment = text[cursor:]
        result.append(segment[:protected] + self.plain(segment[protected:]))
        return ''.join(result)


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise ValueError('Unsupported script version: ' + before[:70])
    return text.replace(before, after)


def build(game, output):
    executable_hash = hashlib.sha256((game / 'nekopara_vol1.exe').read_bytes()).hexdigest()
    if executable_hash != GAME_SHA256:
        raise ValueError('Unsupported NEKOPARA executable build')
    effective = {}
    strings = set()
    inputs = {}
    for name in ['data.xp3', 'patch.xp3', 'patch2.xp3']:
        archive = Archive(game / name)
        for e in archive.files:
            p = Path(e['name'])
            if p.suffix.lower() in ['.tjs', '.scn']:
                data = archive.read(e)
                if p.suffix == '.scn':
                    if p.name.endswith('.ks.scn'):
                        strings.update(s for s in scene_texts(data) if KANJI.search(s))
                elif data.startswith(b'\xff\xfe'):
                    effective[p.name.lower()] = data.decode('utf-16').replace('\r\n', '\n')
        inputs[name] = {'size': archive.path.stat().st_size}
    annotator = Annotator(json.loads((ROOT / 'readings_overrides.json').read_text()))
    base_archive = Archive(game / 'data.xp3')
    names = name_readings(base_archive, effective['nameimage.tjs'], annotator)
    readings = {s: annotator.annotate(s) for s in sorted(strings)}
    readings = {s: a for s, a in readings.items() if s != a}
    quote = lambda x: json.dumps(x, ensure_ascii=False)
    dictionary = 'var FuriganaReadings = %[\n' + ',\n'.join(quote(s) + '=>' + quote(a) for s, a in readings.items()) + '\n];\n'
    dictionary += 'var FuriganaNames = %[\n' + ',\n'.join(
        quote(name) + '=>%["image"=>' + quote(info['image']) + ',"spans"=>' + quote(info['spans']) + ']'
        for name, info in names.items()) + '\n];\n'
    render = effective['rendermsgwin.tjs']
    render = replace_once(render, 'global.TextRenderBase.render(text, autoIndent, diff, time, same);',
                          'global.TextRenderBase.render(typeof global.FuriganaText == "Object" ? global.FuriganaText(text, lang) : text, autoIndent, diff, time, same);')
    render = replace_once(render, 'global.TextRenderBase.render(text, false, 0, 0, 0);',
                          'global.TextRenderBase.render(typeof global.FuriganaText == "Object" ? global.FuriganaText(text) : text, false, 0, 0, 0);')
    render = replace_once(render, 'function drawCount(count, fast=false) {', '''function furiganaRedraw() {
        if (currentText.count == 0) return;
        if (clist !== void) {
            var saved = cpos;
            cpos = 0;
            drawCount(saved, true);
        } else {
            kag.fore.messages[no].redrawText();
        }
    }
    function drawCount(count, fast=false) {''')
    render = replace_once(render, 'kag.addPlugin(new RenderMsgwinPlugin(kag));',
                          'kag.addPlugin(global.furiganaRenderPlugin = new RenderMsgwinPlugin(kag));')
    text_render = effective['textrender.tjs']
    text_render = replace_once(text_render, 'if (ruby) with (ruby)', 'if (ruby && global.furiganaEnabled !== false) with (ruby)')
    text_render = replace_once(text_render, 'rtext.y += .y;', 'rtext.y += .y - (ch.vertical ? 0 : 3);')
    text_render = replace_once(text_render, 'var ret = super.render(text, autoIndent, diff, all, false);',
                               'var ret = super.render(typeof global.FuriganaText == "Object" ? global.FuriganaText(text) : text, autoIndent, diff, all, false);')
    backlog = effective['backlog.tjs']
    backlog = replace_once(backlog, 'backupCurrentMessageVisibleState();',
                           'global.furiganaBacklog = this;\n        backupCurrentMessageVisibleState();')
    backlog = replace_once(backlog, 'var _textBlocks = %[];\n\tfunction finalize() {',
                           'var _textBlocks = %[];\n\tfunction finalize() {\n        global.furiganaBacklog = void;')
    msghack = replace_once(effective['msghack.tjs'],
        'function processName(text) { currentName = text; return super.processName(((string)text).trim()); }',
        (ROOT / 'runtime/NameLayerHooks.tjs').read_text())
    custom = replace_once(effective['custom.tjs'], 'putStamp(lay, nameRect);',
        'putStamp(lay, nameRect);\n                    if (typeof global.FuriganaDrawNameImageRuby == "Object")\n                        global.FuriganaDrawNameImageRuby(lay, name, .x, 0, Math.min(10, .y-1));')
    after = effective['afterinit.tjs'] + '\n' + (ROOT / 'runtime/AfterInitFurigana.tjs').read_text()
    files = {'AfterInit.tjs': after, 'rendermsgwin.tjs': render, 'TextRender.tjs': text_render, 'backlog.tjs': backlog,
             'msghack.tjs': msghack, 'custom.tjs': custom,
             'Furigana.tjs': dictionary + (ROOT / 'runtime/FuriganaNames.tjs').read_text() + '\n' + (ROOT / 'runtime/Furigana.tjs').read_text()}
    pack({n: s.encode('utf-16') for n, s in files.items()}, output, neko_steam=True)
    manifest = {'version': '0.3.0', 'archive_format': 'neko_vol1_steam', 'name_labels': len(names),
                'patch_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'game_sha256': executable_hash,
                'inputs': inputs, 'annotated_strings': len(readings), 'words': len(annotator.words),
                'unknown': sorted(annotator.unknown), 'files': sorted(files)}
    output.with_suffix('.build.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'unknown'}, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=ROOT.parent)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/patch3.xp3')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    build(args.game, args.output)
