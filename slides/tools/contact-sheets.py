"""Render every PDF page and compose numbered visual review sheets."""
from pathlib import Path
import re
import fitz
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
R=ROOT/'build/qa'
P=R/'qa-pages'
if '--pages' in __import__('sys').argv:P.mkdir(exist_ok=True)
C=R/'contact-sheets';C.mkdir(exist_ok=True)
doc=fitz.open(ROOT/'exports/ai5049-reefnet.pdf')
current_sheets=set()
for start in range(0,len(doc),9):
    sheet=Image.new('RGB',(1920,1152),'#dedede');draw=ImageDraw.Draw(sheet)
    for j in range(9):
        n=start+j
        if n>=len(doc):break
        page=doc[n];pix=page.get_pixmap(matrix=fitz.Matrix(640/page.rect.width,640/page.rect.width),alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        x=(j%3)*640;y=(j//3)*384
        sheet.paste(im,(x,y));draw.text((x+8,y+363),f'{n+1:03d}',fill='#111')
        if '--pages' in __import__('sys').argv:im.save(P/f'{n+1:03d}.png')
    name=f'{start+1:03d}-{min(start+9,len(doc)):03d}.jpg'
    sheet.save(C/name,quality=92)
    current_sheets.add(name)
for old in C.iterdir():
    if old.is_file() and re.fullmatch(r'\d{3}-\d{3}\.jpg',old.name) and old.name not in current_sheets:
        old.unlink()
print(len(doc),'pages;',len(current_sheets),'contact sheets')
