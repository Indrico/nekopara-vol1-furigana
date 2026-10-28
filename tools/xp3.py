"""Read this NEKOPARA build's XP3 archives without changing them."""
import struct
import zlib
import hashlib
from pathlib import Path

MAGIC = b'XP3\r\n \n\x1a\x8bg\x01'


def chunks(data):
    pos = 0
    while pos < len(data):
        tag = data[pos:pos + 4]
        size, = struct.unpack_from('<Q', data, pos + 4)
        end = pos + 12 + size
        if end > len(data):
            raise ValueError('Truncated XP3 chunk')
        yield tag, data[pos + 12:end]
        pos = end


class Archive:
    def __init__(self, path):
        self.path = Path(path)
        self.files = []
        names = {}
        with self.path.open('rb') as f:
            if f.read(11) != MAGIC:
                raise ValueError('Invalid XP3 signature')
            offset, = struct.unpack('<Q', f.read(8))
            visited = set()
            while True:
                if offset in visited:
                    raise ValueError('Circular XP3 index')
                visited.add(offset)
                f.seek(offset)
                flag = f.read(1)[0]
                size, = struct.unpack('<Q', f.read(8))
                if flag & 7 == 1:
                    original, = struct.unpack('<Q', f.read(8))
                    data = zlib.decompress(f.read(size))
                    if len(data) != original:
                        raise ValueError('XP3 index size mismatch')
                elif flag & 7 == 0:
                    data = f.read(size)
                else:
                    raise ValueError('Unsupported XP3 index encoding')
                following = struct.unpack('<Q', f.read(8))[0] if flag & 128 else None
                for tag, body in chunks(data):
                    if tag == b'eliF':
                        checksum, length = struct.unpack_from('<IH', body)
                        names[checksum] = body[6:6 + 2 * length].decode('utf-16le')
                    elif tag == b'File':
                        entry = {}
                        for subtag, value in chunks(body):
                            if subtag == b'adlr':
                                entry['checksum'], = struct.unpack('<I', value)
                            elif subtag == b'info':
                                flags, original, stored, length = struct.unpack_from('<IQQH', value)
                                entry.update(flags=flags, size=original, stored=stored,
                                             name=value[22:22 + length * 2].decode('utf-16le'))
                            elif subtag == b'segm':
                                entry['segments'] = list(struct.iter_unpack('<IQQQ', value))
                        self.files.append(entry)
                if following is None:
                    break
                offset = following
        for entry in self.files:
            entry['stored_name'] = entry['name']
            entry['name'] = names.get(entry['checksum'], entry['name'])

    def read(self, entry):
        parts = []
        with self.path.open('rb') as f:
            for flag, offset, original, stored in entry['segments']:
                f.seek(offset)
                part = f.read(stored)
                part = zlib.decompress(part) if flag & 1 else part
                if len(part) != original:
                    raise ValueError('XP3 segment size mismatch')
                parts.append(part)
        data = b''.join(parts)
        checksum = entry['checksum']
        if zlib.adler32(data) != checksum and entry['flags'] & 0x80000000:
            value = checksum ^ 0x44528B87
            key = (value ^ value >> 8 ^ value >> 16 ^ value >> 24) & 255
            key = key or 0x23
            data = data.translate(bytes(i ^ key for i in range(256)))
        if zlib.adler32(data) != checksum:
            raise ValueError('XP3 checksum mismatch: ' + entry['name'])
        if len(data) != entry['size']:
            raise ValueError('XP3 file size mismatch')
        return data


def pack(files, path, *, neko_steam=False):
    """Write a flat XP3; NEKOPARA uses hashed names and its extraction filter."""
    def chunk(tag, body):
        return tag + struct.pack('<Q', len(body)) + body

    index = []
    with Path(path).open('wb') as f:
        f.write(MAGIC + b'\0' * 8)
        for name, data in sorted(files.items()):
            checksum = zlib.adler32(data)
            stored_name = name
            payload = data
            flags = 0
            prefix = b''
            if neko_steam:
                stored_name = hashlib.md5(name.lower().encode('utf-16le')).hexdigest()
                value = checksum ^ 0x44528B87
                key = (value ^ value >> 8 ^ value >> 16 ^ value >> 24) & 255
                key = key or 0x23
                payload = data.translate(bytes(i ^ key for i in range(256)))
                flags = 0x80000000
                original_name = name.encode('utf-16le')
                prefix = chunk(b'eliF', struct.pack('<IH', checksum, len(original_name) // 2) + original_name + b'\0\0')
            encoded = stored_name.encode('utf-16le')
            compressed = zlib.compress(payload, 9)
            offset = f.tell()
            f.write(compressed)
            body = chunk(b'info', struct.pack('<IQQH', flags, len(data), len(compressed), len(encoded) // 2) + encoded + b'\0\0')
            body += chunk(b'segm', struct.pack('<IQQQ', 1, offset, len(data), len(compressed)))
            body += chunk(b'adlr', struct.pack('<I', checksum))
            index.append(prefix + chunk(b'File', body))
        raw = b''.join(index)
        compressed = zlib.compress(raw, 9)
        offset = f.tell()
        f.write(b'\x01' + struct.pack('<QQ', len(compressed), len(raw)) + compressed)
        f.seek(11)
        f.write(struct.pack('<Q', offset))
