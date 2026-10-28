"""Read the PSB v2 scenario structure, including its explicit language slots.

Layout cross-checked against FreeMote's PSB reader and the local SCN files.
"""
from functools import lru_cache
import struct


def scene_texts(data):
    if data[:8] != b'PSB\0\x02\0\0\0':
        raise ValueError('Expected unencrypted PSB version 2')

    def array(pos):
        count_width = data[pos] - 12
        if not 1 <= count_width <= 4:
            raise ValueError('Invalid PSB array count')
        count = int.from_bytes(data[pos + 1:pos + 1 + count_width], 'little')
        width = data[pos + 1 + count_width] - 12
        if not 1 <= width <= 4:
            raise ValueError('Invalid PSB array width')
        start = pos + count_width + 2
        end = start + count * width
        if end > len(data):
            raise ValueError('Truncated PSB array')
        return [int.from_bytes(data[start + i * width:start + (i + 1) * width], 'little') for i in range(count)], end

    pos, = struct.unpack_from('<I', data, 12)
    charset, pos = array(pos)
    parents, pos = array(pos)
    indexes, pos = array(pos)
    names = []
    for index in indexes:
        char = parents[index]
        chars = []
        while char:
            code = parents[char]
            chars.append(char - charset[code])
            char = code
        names.append(bytes(reversed(chars)).decode('utf-8'))
    pos, base = struct.unpack_from('<II', data, 16)
    offsets, _ = array(pos)
    strings = [data[base + off:data.index(0, base + off)].decode('utf-8') for off in offsets]

    @lru_cache(maxsize=None)
    def value(pos):
        kind = data[pos]
        pos += 1
        if kind <= 4:
            return [None, None, False, True, 0][kind]
        if kind <= 12:
            return int.from_bytes(data[pos:pos + kind - 4], 'little', signed=True)
        if 21 <= kind <= 24:
            return strings[int.from_bytes(data[pos:pos + kind - 20], 'little')]
        if kind == 29:
            return 0.0
        if kind in (30, 31):
            return struct.unpack_from('<f' if kind == 30 else '<d', data, pos)[0]
        if kind == 32:
            offsets, start = array(pos)
            return [value(start + off) for off in offsets]
        if kind == 33:
            keys, pos = array(pos)
            offsets, start = array(pos)
            return {names[key]: value(start + off) for key, off in zip(keys, offsets)}
        raise ValueError('Unsupported scenario PSB object: ' + hex(kind))

    try:
        root = value(struct.unpack_from('<I', data, 36)[0])
        for scene in root.get('scenes', []):
            for record in scene.get('texts', []):
                # texts[*][2] is [Japanese, English, Traditional Chinese].
                # Each language has [display name, dialogue/narration].
                japanese = record[2][0]
                for text in [record[0], japanese[0], japanese[1]]:
                    if isinstance(text, str):
                        yield text
    finally:
        value.cache_clear()
