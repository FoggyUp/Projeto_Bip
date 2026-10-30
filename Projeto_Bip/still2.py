import math, sys
from PIL import Image, ImageDraw, ImageChops

W, H, SS = 1080, 1350, 3
WW, HH = W * SS, H * SS
OUT = sys.argv[1]

def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

OL = hx('5E3B2E')
TEAL, TEAL_SH, TEAL_HI, TEAL_SPOT, TEAL_D = hx('5FD9CB'), hx('3FBDB0'), hx('B2F1EA'), hx('86E5DA'), hx('2FA596')
SILVER, SILVER_SH, SILVER_D = hx('EDF1F6'), hx('C9D2DE'), hx('9AA7B8')
STAR, STAR_SH = hx('FFD54A'), hx('F2B630')
WHITE, PUPIL, CHEEK = (255, 255, 255), hx('2B1A15'), hx('FFA9BC')
MOUTH_IN, TONGUE = hx('9C2B3B'), hx('FF8A99')
GLOW = hx('7CF2C8')

def lerp(a, b, t): return a + (b - a) * t
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

im = Image.new('RGB', (WW, HH))
d = ImageDraw.Draw(im)
S = SS

def line(q, ww, col, closed=False):
    if closed: q = q + [q[0], q[1]]
    d.line(q, fill=col, width=max(1, int(ww)), joint='curve')
    if not closed:
        r = ww / 2
        for (x, y) in (q[0], q[-1]):
            d.ellipse([x-r, y-r, x+r, y+r], fill=col)

# ---------- fundo ----------
top, bot = hx('9FDFF0'), hx('F6F7DE')
for y in range(HH):
    t = y / HH
    d.line([(0, y), (WW, y)], fill=tuple(int(lerp(top[i], bot[i], t)) for i in range(3)))
# sol
for r, col in [(150, hx('FFF3C4')), (110, hx('FFE9A0')), (78, hx('FFD95E'))]:
    d.ellipse([(900-r)*S, (170-r)*S, (900+r)*S, (170+r)*S], fill=col)
def soft_cloud(cx, cy, s):
    for dx, dy, r in [(0, 8, 60), (-62, 20, 44), (66, 20, 48)]:
        d.ellipse([(cx+dx*s-r*s)*S, (cy+dy*s-r*s)*S, (cx+dx*s+r*s)*S, (cy+dy*s+r*s)*S], fill=hx('DDEFF6'))
    for dx, dy, r in [(0, 0, 58), (-64, 14, 42), (66, 14, 46), (-30, -28, 42), (34, -26, 48)]:
        d.ellipse([(cx+dx*s-r*s)*S, (cy+dy*s-r*s)*S, (cx+dx*s+r*s)*S, (cy+dy*s+r*s)*S], fill=WHITE)
soft_cloud(180, 230, 1.1); soft_cloud(760, 330, 0.7); soft_cloud(980, 640, 0.6); soft_cloud(110, 620, 0.55)
for cx, cy, rx, ry, col in [(150, 1170, 520, 230, hx('BDE296')), (930, 1190, 560, 250, hx('AAD982'))]:
    d.ellipse([(cx-rx)*S, (cy-ry)*S, (cx+rx)*S, (cy+ry)*S], fill=col)
houses = [(-30, 160, hx('FFB27A'), hx('E8604C')), (105, 125, hx('FFE07A'), hx('5BA7E6')),
          (850, 130, hx('9FD8F7'), hx('E8604C')), (975, 165, hx('C9A6F2'), hx('F28C3A'))]
for x, hgt, wall, roof in houses:
    base = 1150; w = 120
    d.rectangle([x*S, (base-hgt)*S, (x+w)*S, base*S], fill=wall, outline=OL, width=4*S)
    d.polygon([((x-12)*S, (base-hgt)*S), ((x+w+12)*S, (base-hgt)*S), ((x+w/2)*S, (base-hgt-70)*S)], fill=roof, outline=OL, width=4*S)
    for wx in (x+22, x+70):
        d.rectangle([wx*S, (base-hgt+30)*S, (wx+28)*S, (base-hgt+60)*S], fill=hx('FFF6D6'), outline=OL, width=3*S)
    d.rectangle([(x+46)*S, (base-55)*S, (x+74)*S, base*S], fill=hx('B8805C'), outline=OL, width=3*S)
for tx, sc in ((290, 1.0), (775, 0.9)):
    d.rectangle([(tx-10*sc)*S, (1150-95*sc)*S, (tx+10*sc)*S, 1150*S], fill=hx('B8805C'), outline=OL, width=3*S)
    for dx, dy, r in [(0, -150, 62), (-40, -115, 46), (40, -115, 48)]:
        d.ellipse([(tx+dx*sc-r*sc)*S, (1150+dy*sc-r*sc)*S, (tx+dx*sc+r*sc)*S, (1150+dy*sc+r*sc)*S], fill=hx('6CC46A'), outline=OL, width=4*S)
    for dx, dy, r in [(0, -150, 58), (-40, -115, 42), (40, -115, 44)]:
        d.ellipse([(tx+dx*sc-r*sc)*S, (1150+dy*sc-r*sc)*S, (tx+dx*sc+r*sc)*S, (1150+dy*sc+r*sc)*S], fill=hx('6CC46A'))
    d.ellipse([(tx-30*sc)*S, (1150-185*sc)*S, (tx-6*sc)*S, (1150-170*sc)*S], fill=hx('9BDB8A'))
grass = [((-50 + i * 12) * S, (1150 + 18 * math.sin(i / 7)) * S) for i in range(110)]
d.polygon(grass + [(1400 * S, 1400 * S), (-50 * S, 1400 * S)], fill=hx('94D25F'))
line(grass, 5 * S, OL)
for fx, fy, col in [(90, 1260, hx('FF8FB1')), (990, 1240, hx('FFD54A')), (200, 1320, WHITE), (880, 1320, hx('FF8FB1'))]:
    for k in range(5):
        a = k * 2 * math.pi / 5
        d.ellipse([(fx+11*math.cos(a)-8)*S, (fy+11*math.sin(a)-8)*S, (fx+11*math.cos(a)+8)*S, (fy+11*math.sin(a)+8)*S], fill=col, outline=OL, width=2*S)
    d.ellipse([(fx-6)*S, (fy-6)*S, (fx+6)*S, (fy+6)*S], fill=hx('FFB13B'))
d.ellipse([(540-170)*S, (1252-20)*S, (540+170)*S, (1252+20)*S], fill=hx('7CBF4C'))

# ---------- Nino ----------
cx, base, s = 540, 1252, 5.0
OLW = 1.3
def P(x, y): return ((cx + (x - 80) * s) * S, (base + (y - 150) * s) * S)
def Q(pts): return [P(*p) for p in pts]
def mask(pts):
    m = Image.new('L', (WW, HH), 0)
    ImageDraw.Draw(m).polygon(Q(pts), fill=255)
    return m
def paint(m, col): im.paste(col, (0, 0), m)
def shape(pts, fill, outline=True, w=OLW):
    d.polygon(Q(pts), fill=fill)
    if outline: line(Q(pts), w * s * S, OL, closed=True)
def stroke(pts, w, col, outline=True, olw=OLW):
    if outline: line(Q(pts), (w + 2 * olw) * s * S, OL)
    line(Q(pts), w * s * S, col)
def star_pts(cx_, cy_, r1, r2):
    return [(cx_ + (r1 if i % 2 == 0 else r2) * math.cos(-math.pi/2 + i*math.pi/5),
             cy_ + (r1 if i % 2 == 0 else r2) * math.sin(-math.pi/2 + i*math.pi/5)) for i in range(10)]

BODY = bez3((80, 30), (121, 30), (131, 70), (129, 100)) + bez3((129, 100), (128, 125), (110, 134), (80, 134))[1:] \
     + bez3((80, 134), (50, 134), (32, 125), (31, 100))[1:] + bez3((31, 100), (29, 70), (39, 30), (80, 30))[1:-1]
def shifted(pts, dx, dy): return [(x + dx, y + dy) for x, y in pts]

# pernas e botas
for lx in (64, 96):
    shape(rrect(lx - 9, 124, lx + 9, 144, 6), TEAL)
    shape(rrect(lx - 12, 138, lx + 13, 152, 6), SILVER_SH)
    d.polygon(Q(rrect(lx - 9, 140, lx + 10, 144, 2)), fill=SILVER)
# braço esquerdo (baixo) e direito (acenando), atrás do corpo
stroke(bez2((40, 104), (24, 114), (24, 128)), 9.5, TEAL)
shape([(19, 126), (29, 126), (30, 134), (24, 137), (18, 133)], TEAL)
shape(ell_pts(24, 131, 7, 6.5), TEAL)
wave = rot_pts(bez2((120, 100), (142, 92), (146, 66)), 120, 100, math.radians(-8))
stroke(wave, 9.5, TEAL)
hxp, hyp = wave[-1]
shape(ell_pts(hxp + 1, hyp - 4, 8.5, 9), TEAL)

# corpo com sombra, manchas e brilho (recortados no corpo)
bm = mask(BODY)
paint(bm, TEAL)
shade = ImageChops.subtract(bm, mask(shifted(BODY, -9, -3)))
paint(shade, TEAL_SH)
for sx_, sy_, r in [(52, 44, 4.5), (44, 56, 3), (60, 38, 2.5), (110, 52, 3.5), (116, 62, 2.2)]:
    paint(ImageChops.multiply(bm, mask(ell_pts(sx_, sy_, r, r))), TEAL_SPOT)
paint(ImageChops.multiply(bm, mask(ell_pts(58, 42, 13, 6.5))), TEAL_HI)
# macacão
suit_region = bez3((10, 99), (50, 92), (110, 92), (150, 99)) + [(150, 160), (10, 160)]
sm = ImageChops.multiply(bm, mask(suit_region))
paint(sm, SILVER)
paint(ImageChops.multiply(sm, shade), SILVER_SH)
paint(ImageChops.multiply(sm, mask(rrect(10, 118, 150, 124, 1))), SILVER_D)
paint(ImageChops.multiply(sm, mask(shifted(BODY, 0, 0)) if False else ImageChops.subtract(sm, mask(shifted(BODY, 0, -4)))), SILVER_SH)
# contornos
line(Q(BODY), OLW * s * S, OL, closed=True)
line(Q(bez3((31.5, 98.8), (54, 93), (106, 93), (128.5, 98.8))), OLW * s * S, OL)
lm = Image.new('L', (WW, HH), 0); ld = ImageDraw.Draw(lm)
for yy in (118, 124):
    ld.line(Q([(10, yy), (150, yy)]), fill=255, width=int(0.9 * s * S))
paint(ImageChops.multiply(lm, bm), OL)
# fivela estrela e tradutor
shape(rrect(71, 115.5, 89, 126.5, 4), STAR, w=1.0)
shape(star_pts(80, 121, 4.4, 1.9), STAR_SH, outline=False)
shape(star_pts(80, 120.6, 4, 1.7), WHITE, outline=False)
line(Q([(105, 124), (105, 129)]), 0.9 * s * S, OL)
shape(ell_pts(105, 132, 4.2, 4.2), SILVER_SH, w=1.0)
shape(ell_pts(105, 132, 2.3, 2.3), GLOW, outline=False)
# estrela no peito
shape(star_pts(80, 106.5, 6.5, 2.8), STAR, w=0.9)
# "orelhas" de comunicador
for ex_, side in ((32, -1), (128, 1)):
    shape(ell_pts(ex_ + side * 1, 62, 6, 7.5), SILVER)
    shape(ell_pts(ex_ + side * 1.5, 62, 3, 4), GLOW, w=0.8)
# antena
stroke(bez2((80, 32), (79, 20), (84, 10)), 3, TEAL_D)
shape(ell_pts(80, 31.5, 5, 2.2), SILVER_SH, w=0.9)
shape(ell_pts(85, 6.5, 7, 7), STAR)
shape(ell_pts(86.5, 8, 4.5, 4.5), STAR_SH, outline=False)
shape(ell_pts(84, 5.5, 4.5, 4.5), STAR, outline=False)
shape(ell_pts(82.6, 3.8, 2, 2), WHITE, outline=False)
for a in (-150, -110, -30, 10):
    r0, r1 = 10, 14
    ar = math.radians(a)
    line(Q([(85 + r0*math.cos(ar), 6.5 + r0*math.sin(ar)), (85 + r1*math.cos(ar), 6.5 + r1*math.sin(ar))]), 1.2 * s * S, STAR_SH)
# rosto
for ex in (64, 96):
    shape(ell_pts(ex, 63, 11.5, 14.5), WHITE, w=1.05)
    shape(ell_pts(ex + 1.8, 65.5, 4.6, 5.4), PUPIL, outline=False)
    shape(ell_pts(ex + 3.4, 63.4, 1.7, 1.7), WHITE, outline=False)
    shape(ell_pts(ex + 0.4, 68.4, 0.9, 0.9), WHITE, outline=False)
    stroke(bez2((ex - 7, 43.5), (ex, 40), (ex + 7, 43.5)), 1.5, OL, outline=False)
shape(ell_pts(47, 81, 6.5, 4), CHEEK, outline=False); shape(ell_pts(113, 81, 6.5, 4), CHEEK, outline=False)
mouth = [(69, 80)] + bez2((69, 80), (80, 99), (91, 80), n=20)[1:]
mm = mask(mouth)
paint(mm, MOUTH_IN)
paint(ImageChops.multiply(mm, mask(ell_pts(80, 92, 6.5, 4.2))), TONGUE)
paint(ImageChops.multiply(mm, mask([(60, 79), (100, 79), (100, 83.2), (60, 83.2)])), WHITE)
line(Q(mouth), 1.05 * s * S, OL, closed=True)

im.resize((W, H), Image.LANCZOS).save(OUT)
print('ok')
