"""Ferramentas de desenho compartilhadas pelo cenário e pelos personagens."""
import math
from functools import lru_cache
from PIL import Image, ImageChops, ImageDraw, ImageFont


def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

OL = hx('5E3B2E')
WHITE = (255, 255, 255)

def lerp(a, b, t): return a + (b - a) * t
def lerp_cor(a, b, t): return tuple(int(lerp(a[i], b[i], t)) for i in range(3))

def bez3(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out
def bez2(p0, p1, p2, n=12):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    return out
def ell_pts(cx, cy, rx, ry, n=56):
    return [(cx + rx*math.cos(2*math.pi*i/n), cy + ry*math.sin(2*math.pi*i/n)) for i in range(n)]
def rrect(x0, y0, x1, y1, r, n=8):
    pts = []
    for cx, cy, a0 in [(x1-r, y0+r, -math.pi/2), (x1-r, y1-r, 0), (x0+r, y1-r, math.pi/2), (x0+r, y0+r, math.pi)]:
        for i in range(n + 1):
            a = a0 + (math.pi/2) * i / n
            pts.append((cx + r*math.cos(a), cy + r*math.sin(a)))
    return pts
def rot_pts(pts, ox, oy, a):
    c, s = math.cos(a), math.sin(a)
    return [(ox + (x-ox)*c - (y-oy)*s, oy + (x-ox)*s + (y-oy)*c) for x, y in pts]
def star_pts(cx, cy, r1, r2, a0=0.0):
    return [(cx + (r1 if i % 2 == 0 else r2) * math.cos(-math.pi/2 + a0 + i*math.pi/5),
             cy + (r1 if i % 2 == 0 else r2) * math.sin(-math.pi/2 + a0 + i*math.pi/5)) for i in range(10)]
def heart_pts(cx, cy, r, n=56):
    # coração clássico (curva paramétrica), com largura 2r e ponta para baixo
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2*t) - 2 * math.cos(3*t) - math.cos(4*t)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    return pts

def linha(d, q, ww, col, closed=False):
    """Linha grossa com juntas e pontas arredondadas, em pixels."""
    if closed: q = q + [q[0], q[1]]
    d.line(q, fill=col, width=max(1, int(ww)), joint='curve')
    if not closed:
        r = ww / 2
        for (x, y) in (q[0], q[-1]):
            d.ellipse([x-r, y-r, x+r, y+r], fill=col)


class Pen:
    """Desenha um personagem em coordenadas locais (~160 x 150, centro em x=80, chão em y=150).

    cx e base são a posição na cena (em pixels finais); s é a escala; ss é o supersampling;
    sx e sy esticam ou achatam o personagem a partir do pé; ox e oy são a origem da imagem
    em que se desenha (uma camada só do tamanho do personagem)."""
    def __init__(self, im, cx, base, s, ss, sx=1.0, sy=1.0, ox=0, oy=0, olw=1.25):
        self.im, self.d = im, ImageDraw.Draw(im)
        self.cx, self.base, self.s, self.ss, self.sx, self.sy, self.ox, self.oy, self.olw = cx, base, s, ss, sx, sy, ox, oy, olw
    def P(self, x, y):
        return ((self.cx + (x - 80) * self.s * self.sx) * self.ss - self.ox, (self.base + (y - 150) * self.s * self.sy) * self.ss - self.oy)
    def Q(self, pts): return [self.P(*p) for p in pts]
    def px(self, w): return w * self.s * self.ss
    def mask(self, pts):
        m = Image.new('L', self.im.size, 0); ImageDraw.Draw(m).polygon(self.Q(pts), fill=255); return m
    def stroke_mask(self, pts, w):
        m = Image.new('L', self.im.size, 0); linha(ImageDraw.Draw(m), self.Q(pts), self.px(w), 255); return m
    def paint(self, m, col): self.im.paste(col, (0, 0), m)
    def line(self, pts, w, col, closed=False): linha(self.d, self.Q(pts), self.px(w), col, closed)
    def shape(self, pts, fill, outline=True, w=None):
        self.d.polygon(self.Q(pts), fill=fill)
        if outline: self.line(pts, self.olw if w is None else w, OL, closed=True)
    def stroke(self, pts, w, col, outline=True, olw=None):
        if outline: self.line(pts, w + 2 * (self.olw if olw is None else olw), OL)
        self.line(pts, w, col)
    def shaded(self, pts, col, sh, hi=None, dx=-6, dy=-3, hi_pts=None):
        """Forma com sombra (a parte que sobra ao deslocar a forma) e brilho opcional, com contorno."""
        m = self.mask(pts); self.paint(m, col)
        self.paint(ImageChops.subtract(m, self.mask([(x + dx, y + dy) for x, y in pts])), sh)
        if hi_pts: self.paint(ImageChops.multiply(m, self.mask(hi_pts)), hi)
        self.line(pts, self.olw, OL, closed=True)
        return m


@lru_cache(maxsize=64)
def fonte(tamanho):
    """DejaVu Sans Bold (a fonte das legendas); no Windows, se ela não estiver instalada, Arial Black ou Arial Bold."""
    for nome in ('DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'ariblk.ttf', 'arialbd.ttf'):
        try:
            return ImageFont.truetype(nome, max(4, int(tamanho)))
        except OSError:
            pass
    return ImageFont.load_default(max(4, int(tamanho)))
