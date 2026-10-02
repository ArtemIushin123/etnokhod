"""Готовит ассеты игры из refs/ (исходники художника) в assets/ (WebP, обрезка, чистка краёв).

Запуск из корня проекта:  python tools/assets/build_assets.py .
Нужны: Pillow, numpy, scipy.  Печатает размеры и параметры головы героев
(по ним подобрана посадка шапки в HEROES.genders[*].hat в index.html).
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = sys.argv[1]
SRC = os.path.join(ROOT, 'refs')
OUT = os.path.join(ROOT, 'assets')
os.makedirs(OUT, exist_ok=True)
info = {}

def src(name): return Image.open(os.path.join(SRC, name))

def save(im, name, q=80, **kw):
    p = os.path.join(OUT, name)
    if name.endswith('.webp'):
        im.save(p, 'WEBP', quality=q, method=6, **kw)
    else:
        im.save(p, optimize=True)
    print(f'{name:28s} {im.size} {os.path.getsize(p)//1024} KB')

def clean_alpha(im, lo=48, erode=1):
    """Срезает полупрозрачное свечение/кайму и подъедает край на erode px."""
    a = np.array(im.convert('RGBA'))
    al = a[:, :, 3].astype(np.float32)
    al[al < lo] = 0
    mask = al > 0
    # убрать мелкие отдельные пятна (остатки фона)
    lab, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, lab, range(1, n + 1))
        keep = np.isin(lab, 1 + np.where(sizes >= sizes.max() * 0.002)[0])
        al[~keep] = 0
    if erode:
        al = ndimage.grey_erosion(al, size=(2 * erode + 1, 2 * erode + 1))
    # мягкий край
    al = ndimage.gaussian_filter(al, 0.6)
    a[:, :, 3] = np.clip(al, 0, 255).astype(np.uint8)
    return Image.fromarray(a)

def bbox_alpha(im, thr=8):
    a = np.array(im)[:, :, 3]
    ys, xs = np.where(a > thr)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

# ---------- фоны ----------
for f, n in [('Главный фон.png', 'bg-main.webp'), ('Фон под карту РФ.png', 'bg-map.webp'),
             ('Фон для башкирии.png', 'bg-bashkortostan.webp')]:
    im = src(f).convert('RGB')
    save(im.resize((1600, round(1600 * im.height / im.width)), Image.LANCZOS), n, q=72)
im = src('Фон в чате.png').convert('RGB')
save(im.resize((500, 500), Image.LANCZOS), 'bg-chat.webp', q=75)

# ---------- круглые картинки на пергаменте: вырезаем круг ----------
def circle_cut(name, out, size):
    im = src(name).convert('RGB')
    a = np.array(im).astype(int)
    mx, mn = a.max(axis=2), a.min(axis=2)
    sat = (mx - mn) / np.maximum(mx, 1)
    diff = sat > 0.38
    diff = ndimage.binary_opening(diff, iterations=4)
    lab, n = ndimage.label(diff)
    sizes = ndimage.sum(diff, lab, range(1, n + 1))
    diff = lab == (1 + int(np.argmax(sizes)))
    diff = ndimage.binary_fill_holes(diff)
    ys, xs = np.where(diff)
    cx, cy = (xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2
    r = max(xs.max() - xs.min(), ys.max() - ys.min()) / 2 - 1
    yy, xx = np.mgrid[:a.shape[0], :a.shape[1]]
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    alpha = np.clip((r - d) * 255 / 2, 0, 255).astype(np.uint8)
    rgba = np.dstack([np.array(im), alpha])
    box = (int(cx - r), int(cy - r), int(cx + r), int(cy + r))
    c = Image.fromarray(rgba).crop(box).resize((size, size), Image.LANCZOS)
    save(c, out, q=85)
    return c

circle_cut('бурек.png', 'coin-burek.webp', 256)
circle_cut('курай.png', 'coin-kurai.webp', 256)

# ---------- логотип: целиком (скруглённый квадрат на пергаменте) + круг ----------
logo = circle_cut('лого.png', 'logo.webp', 512)
fav = logo.resize((64, 64), Image.LANCZOS)
save(fav, 'favicon.png')

# ---------- шапка для героя ----------
hat = clean_alpha(src('Бурек для Персонажа.png'), lo=40, erode=1)
hat = hat.crop(bbox_alpha(hat))
hat = hat.resize((360, round(360 * hat.height / hat.width)), Image.LANCZOS)
save(hat, 'hat-burek.webp', q=85)
info['hatAspect'] = hat.width / hat.height

# ---------- герои: только вид спереди ----------
heroes = {'m-dark': 'чел браун.png', 'm-light': 'Мальчик блондин.png',
          'f-dark': 'девочка ьраун.png', 'f-light': 'Девочка блондинка.png'}
info['heroes'] = {}
for key, f in heroes.items():
    im = clean_alpha(src(f), lo=64, erode=1)
    a = np.array(im)[:, :, 3]
    cols = (a > 8).sum(axis=0)
    # первый силуэт слева: идём от первого непустого столбца до первого провала
    xs = np.where(cols > 0)[0]
    x0 = xs[0]
    x1 = x0
    gap = 0
    for x in range(x0, a.shape[1]):
        if cols[x] > 0:
            x1 = x; gap = 0
        else:
            gap += 1
            if gap > 20: break
    fig = im.crop((x0, 0, x1 + 1, im.height))
    fig = fig.crop(bbox_alpha(fig))
    H = 640
    fig = fig.resize((round(H * fig.width / fig.height), H), Image.LANCZOS)
    # голова: верхняя часть силуэта до шеи — ищем ширину по строкам
    fa = np.array(fig)[:, :, 3] > 40
    rows = fa.sum(axis=1)
    top = int(np.argmax(rows > 0))
    # макушка..уровень глаз: берём верхние 20% высоты, ширина головы — макс. ширина там
    band = fa[top: top + int(H * 0.2)]
    bx = np.where(band.any(axis=0))[0]
    info['heroes'][key] = {'w': fig.width, 'h': fig.height, 'top': top,
                           'headL': int(bx.min()), 'headR': int(bx.max())}
    save(fig, f'hero-{key}.webp', q=82)

# ---------- Данияр: убрать белый фон ----------
im = src('Данияр.png').convert('RGB')
a = np.array(im).astype(int)
white = (a.min(axis=2) > 200) & ((a.max(axis=2) - a.min(axis=2)) < 22)
lab, n = ndimage.label(white)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
bg = np.isin(lab, list(border))
bg = ndimage.binary_closing(bg, iterations=1) | bg
alpha = np.where(bg, 0, 255).astype(np.float32)
alpha = ndimage.grey_erosion(alpha, size=(3, 3))
alpha = ndimage.gaussian_filter(alpha, 0.8)
rgba = Image.fromarray(np.dstack([a.astype(np.uint8), alpha.clip(0, 255).astype(np.uint8)]))
rgba = rgba.crop(bbox_alpha(rgba))
rgba = rgba.resize((round(720 * rgba.width / rgba.height), 720), Image.LANCZOS)
save(rgba, 'guide-daniyar.webp', q=82)

# ---------- пузыри реплик ----------
for f, n in [('Реплика в чате 1.png', 'bubble-chat.webp'), ('Реплика 2.png', 'bubble-guide.webp')]:
    im = clean_alpha(src(f), lo=200, erode=2)
    im = im.crop(bbox_alpha(im))
    im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
    save(im, n, q=85)
    info[n] = im.size

print(json.dumps(info, indent=1))
