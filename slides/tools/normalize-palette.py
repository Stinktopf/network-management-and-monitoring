"""Apply one semantic palette to all generated SVG diagrams."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ET.register_namespace('', 'http://www.w3.org/2000/svg')
INK, MUTED, LINE = '#303030', '#666666', '#888888'
BORDER, GRID, PANEL, WHITE = '#cccccc', '#dddddd', '#f6f6f6', '#ffffff'
GREEN = '#72bf44'

def rgb(value):
    if value == 'white': return (255, 255, 255)
    if value == 'black': return (0, 0, 0)
    if not value.startswith('#'): return None
    value = value[1:]
    if len(value) == 3: value = ''.join(c * 2 for c in value)
    if len(value) != 6: return None
    return tuple(int(value[i:i+2], 16) for i in (0, 2, 4))

for file in sorted((ROOT / 'assets/diagrams').glob('*.svg')):
    tree = ET.parse(file)
    for element in tree.iter():
        tag = element.tag.split('}')[-1]
        for prop in ('fill', 'stroke'):
            value = element.get(prop)
            if value is None: continue
            color = rgb(value)
            if color is None: continue
            if color == (114, 191, 68):
                element.set(prop, GREEN)
                continue
            assert color[0] == color[1] == color[2], (file.name, value)
            gray = color[0]
            if tag == 'text':
                normalized = INK if gray < 80 else MUTED
            elif prop == 'stroke':
                if tag in ('rect', 'circle', 'ellipse'):
                    normalized = INK if gray < 80 else BORDER
                else:
                    normalized = INK if gray < 80 else GRID if gray >= 200 else LINE
            else:
                normalized = (WHITE if gray == 255 else PANEL if gray >= 230 else
                              GRID if gray >= 180 else INK if gray < 80 else LINE)
            element.set(prop, normalized)
    tree.write(file, encoding='unicode')
print('Unified palette applied to all diagrams.')
