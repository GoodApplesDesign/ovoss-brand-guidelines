"""Review boards for the Mist direction (Joey, 11 Nov 2026), saved to Ovoss Packaging/Colour options/.

    python3 mist_boards.py      # after mist.py and the out/mist renders
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
OUT = HERE.parent.parent.parent / 'Ovoss Packaging' / 'Colour options'
R = HERE / 'out' / 'mist'
M = json.loads((HERE / 'palettes.json').read_text())['palettes']['mist']
AV = '/System/Library/Fonts/Avenir Next.ttc'
def font(i, s): return ImageFont.truetype(AV, s, index=i)
DEMI, MED, REG = 2, 5, 7
INK, GREY, BG = (14, 34, 62), (95, 108, 121), (244, 245, 247)
W, PAD = 2400, 80


def one(glob):
    return Image.open(next(R.glob(glob))).convert('RGB')


def fit(im, w):
    return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)


def header(d, title, sub):
    d.text((PAD, 70), title, font=font(DEMI, 54), fill=INK)
    d.text((PAD, 145), sub, font=font(MED, 28), fill=GREY)


def swatch_row(d, x, y, items, size=110):
    for name, hexv in items:
        d.rounded_rectangle((x, y, x + size, y + size), 14, fill=hexv, outline=(205, 210, 216), width=2)
        d.text((x, y + size + 16), name, font=font(DEMI, 22), fill=INK)
        d.text((x, y + size + 46), hexv.upper(), font=font(REG, 22), fill=GREY)
        x += size + 150
    return x


def board_core():
    hero = fit(one('range_*.png'), W)
    pair = [fit(one(f'{n}_*.png'), (W - 2 * PAD - 40) // 3) for n in ('carton-front', 'tube-front', 'mw-front')]
    H = 230 + hero.height + 60 + pair[0].height + 520
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    header(d, 'Ovoss Mist: Implant Care',
           'The original navy on a light tint. Foil V, wave trim, dentist mark and ticks. High build on the logo, trim and mark.')
    y = 230; im.paste(hero, (0, y)); y += hero.height + 60
    x = PAD
    for p in pair:
        im.paste(p, (x, y)); x += p.width + 20
    y += pair[0].height + 70
    core = M['ranges']['Implant Care']
    d.text((PAD, y), 'Colours', font=font(DEMI, 30), fill=INK)
    swatch_row(d, PAD, y + 60, [('Deep Navy', '#10233F'), ('Tint (background)', core['paper']), ('Wave fill', core['wave']),
                                ('Foil Blue', core['metal']), ('Claims grey', M['claims'])])
    # badge before / after, from the flat textures
    src = Image.open(HERE / 'tex' / 'carton.png').convert('RGB'); new = Image.open(HERE / 'tex' / 'mist' / 'carton.png').convert('RGB')
    box = (2407 - 125, 2647 - 125, 2407 + 125, 2647 + 125)
    bx = W - PAD - 2 * 300 - 30
    d.text((bx, y), 'Dentist badge', font=font(DEMI, 30), fill=INK)
    for i, (lab, s) in enumerate((('Before', src), ('After: line, all foil, 80%', new))):
        t = s.crop(box).resize((300, 300), Image.LANCZOS); im.paste(t, (bx + i * 330, y + 60))
        d.text((bx + i * 330, y + 376), lab, font=font(MED, 22), fill=GREY)
    return im


def board_range():
    a = fit(one('lineup_set_mist-implant-care,*.png'), W)
    H = 230 + a.height + 330
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    header(d, 'Ovoss Mist: across the range', "Each range on a light tint of its own hue, with foil in the range's own colour.")
    y = 230; im.paste(a, (0, y)); y += a.height + 50
    x = PAD
    for rname in ('Implant Care', 'Perio Care', 'Daily Care', 'Restore', 'Potential FPD'):
        rc = M['ranges'][rname]
        d.text((x, y), rname, font=font(DEMI, 24), fill=INK)
        for j, (lab, key) in enumerate((('Tint', 'paper'), ('Wave', 'wave'), ('Dark', 'dark'), ('Foil', 'metal'))):
            yy = y + 44 + j * 52
            d.rounded_rectangle((x, yy, x + 40, yy + 40), 8, fill=rc[key], outline=(205, 210, 216), width=2)
            d.text((x + 56, yy + 6), f'{lab}  {rc[key].upper()}', font=font(REG, 22), fill=GREY)
        x += 450
    return im


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    for nm, fn in (('Ovoss_Mist_Implant_Care_hue-foil_2026-11-11.png', board_core), ('Ovoss_Mist_Range_hue-foil_2026-11-11.png', board_range)):
        fn().save(OUT / nm, optimize=True); print(OUT / nm)
