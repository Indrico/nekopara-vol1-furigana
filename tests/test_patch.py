import json
import hashlib
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get('NEKOPARA_GAME_DIR', ROOT.parent))
HAS_GAME = all((GAME / n).is_file() for n in ['data.xp3', 'patch.xp3', 'patch2.xp3'])
HAS_PATCH = (ROOT / 'dist/patch3.xp3').is_file()
sys.path.insert(0, str(ROOT / 'tools'))
from build import Annotator, align
from xp3 import Archive, pack
from psb import scene_texts
from name_readings import name_readings


class PatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.annotator = Annotator(json.loads((ROOT / 'readings_overrides.json').read_text()))

    def test_okurigana_and_compounds(self):
        self.assertEqual(align('届いた', 'とどいた'), [('届', 'とど'), 'いた'])
        self.assertEqual(align('荷物', 'にもつ'), [('荷物', 'にもつ')])
        self.assertEqual(align('大人', 'おとな'), [('大人', 'おとな')])

    def test_controls_and_existing_ruby(self):
        a = self.annotator
        self.assertEqual(a.annotate('%115;[あした,1]明日\\n時雨'), '%115;[あした,1]明日\\n[しぐれ,1]時雨')
        self.assertEqual(a.annotate('ひらがな カタカナ'), 'ひらがな カタカナ')
        self.assertEqual(a.annotate('[おとな,1]大人も荷物'), '[おとな,1]大人も[にもつ,1]荷物')

    @unittest.skipUnless(HAS_GAME, 'Set NEKOPARA_GAME_DIR to run game integration tests')
    def test_speaker_names_and_image_bounds(self):
        archive = Archive(GAME / 'data.xp3')
        table = archive.read(next(e for e in archive.files if e['name'] == 'image/name/nameimage.tjs')).decode('utf-16')
        names = name_readings(archive, table, self.annotator)
        self.assertEqual(len(names), 16)
        self.assertEqual(names['嘉祥']['spans'][0][2], 'かしょう')
        self.assertEqual(names['時雨']['spans'][0][2], 'しぐれ')
        self.assertNotIn('ショコラ', names)
        for info in names.values():
            for x, width, reading in info['spans']:
                self.assertGreaterEqual(x, 0)
                self.assertGreater(width, 0)
                self.assertLessEqual(x+width, 286)
                self.assertRegex(reading, r'^[ぁ-ゖー]+$')

    def test_patch_roundtrip_and_corruption(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'patch.xp3'
            inputs = {'sample.tjs': '時雨'.encode('utf-16'), 'empty': b''}
            pack(inputs, p)
            a = Archive(p)
            self.assertEqual({e['name']: a.read(e) for e in a.files}, inputs)
            e = next(e for e in a.files if e['name'] == 'sample.tjs')
            e['checksum'] ^= 1
            with self.assertRaisesRegex(ValueError, 'checksum'):
                a.read(e)

    @unittest.skipUnless(HAS_GAME, 'Set NEKOPARA_GAME_DIR to run game integration tests')
    def test_protected_names_match_original_game(self):
        original = Archive(GAME / 'patch.xp3')
        found = set()
        for e in original.files:
            if e['name'] in ['TextRender.tjs', 'rendermsgwin.tjs', 'backlog.tjs']:
                expected = hashlib.md5(e['name'].lower().encode('utf-16le')).hexdigest()
                self.assertEqual(e['stored_name'], expected)
                found.add(e['name'])
        self.assertEqual(len(found), 3)

    @unittest.skipUnless(HAS_PATCH, 'Build dist/patch3.xp3 to run package integration tests')
    def test_encrypted_container_has_no_literal_script_names(self):
        archive = Archive(ROOT / 'dist/patch3.xp3')
        for e in archive.files:
            self.assertEqual(e['stored_name'], hashlib.md5(e['name'].lower().encode('utf-16le')).hexdigest())
            self.assertEqual(e['flags'], 0x80000000)
            self.assertTrue(archive.read(e).startswith(b'\xff\xfe'))

    @unittest.skipUnless(HAS_GAME, 'Set NEKOPARA_GAME_DIR to run game integration tests')
    def test_encrypted_writer_matches_original_stored_payload(self):
        original = Archive(GAME / 'patch.xp3')
        e = next(e for e in original.files if e['name'] == 'TextRender.tjs')
        source = original.read(e)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'protected.xp3'
            pack({e['name']: source}, path, neko_steam=True)
            generated = Archive(path)
            new = generated.files[0]
            self.assertEqual(new['stored_name'], e['stored_name'])
            self.assertEqual(new['checksum'], e['checksum'])
            self.assertEqual(new['flags'], e['flags'])
            # Compare the compressed encrypted bytes to an original entry. This
            # catches matching reader/writer bugs that a self-roundtrip misses.
            import zlib
            def stored_payload(archive, entry):
                parts = []
                with archive.path.open('rb') as f:
                    for flag, offset, size, stored in entry['segments']:
                        f.seek(offset)
                        b = f.read(stored)
                        parts.append(zlib.decompress(b) if flag & 1 else b)
                return b''.join(parts)
            self.assertEqual(stored_payload(original, e), stored_payload(generated, new))

    @unittest.skipUnless(HAS_GAME, 'Set NEKOPARA_GAME_DIR to run game integration tests')
    def test_all_corpus_annotations_preserve_source(self):
        archive = Archive(GAME / 'data.xp3')
        ruby = re.compile(r'\[[ぁ-ゖァ-ヺー]+(?:,[0-9]+)?\]')
        count = 0
        for e in archive.files:
            if not e['name'].endswith('.ks.scn'):
                continue
            for source in scene_texts(archive.read(e)):
                if not re.search(r'[一-鿿]', source):
                    continue
                annotated = self.annotator.annotate(source)
                self.assertEqual(ruby.sub('', annotated), ruby.sub('', source), source)
                count += 1
        self.assertGreater(count, 3000)

    @unittest.skipUnless(HAS_PATCH, 'Build dist/patch3.xp3 to run package integration tests')
    def test_only_expected_scripts_in_patch(self):
        archive = Archive(ROOT / 'dist/patch3.xp3')
        self.assertEqual({e['name'] for e in archive.files},
                         {'AfterInit.tjs', 'TextRender.tjs', 'rendermsgwin.tjs', 'backlog.tjs', 'Furigana.tjs', 'custom.tjs', 'msghack.tjs'})
        for e in archive.files:
            self.assertTrue(archive.read(e).startswith(b'\xff\xfe'))


if __name__ == '__main__':
    unittest.main()
