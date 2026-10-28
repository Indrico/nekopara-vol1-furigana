"""Generate ruby spans from the game's Japanese speaker-name image table."""
from io import BytesIO
import re

from PIL import Image


def name_readings(archive, table, annotator):
    files = {e['name']: e for e in archive.files}
    result = {}
    for tag, name in re.findall(r'"([^"]+)"\s*=>\s*\(const\)\[\s*"([^"]+)"', table):
        annotated = annotator.annotate(name)
        if annotated == name:
            continue
        filename = 'image/name/jp_name_' + tag + '.png'
        image = Image.open(BytesIO(archive.read(files[filename]))).convert('RGBA')
        box = image.getchannel('A').getbbox()
        if not box:
            raise ValueError('Empty name image: ' + filename)
        # Japanese glyph cells are full width; each ruby run is centred above
        # its share of the original glyph bounds, rather than the 286px canvas.
        spans = []
        pos = cursor = 0
        for match in re.finditer(r'\[([^\],]+)(?:,(\d+))?\]([^\[]*)', annotated):
            pos += len(annotated[cursor:match.start()])
            count = int(match[2] or 0) + 1
            unit = (box[2] - box[0]) / len(name)
            spans.append([round(box[0] + pos * unit, 3), round(count * unit, 3), match[1]])
            pos += len(match[3])
            cursor = match.end()
        if not spans:
            raise ValueError('No ruby spans for name: ' + name)
        result[name] = {'image': filename.rsplit('/', 1)[-1], 'spans': spans}
    return result
