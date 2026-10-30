import math, subprocess, sys
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

W, H, SS, FPS, DUR = 1080, 1920, 2, 30, 12.5
WW, HH = W * SS, H * SS
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
OUT = sys.argv[1]
PREVIEW = sys.argv[2] if len(sys.argv) > 2 else None

def hx(c):
    c = c.lstrip('#'); return tuple(int(c[i:i+2], 16) for i in (0, 2, 4))

OL = hx('2A1C1E')
TEAL, TEAL_SH, TEAL_HI, TEAL_D = hx('34CDBE'), hx('1FA597'), hx('8AEADF'), hx('17907F')
SILVER, SILVER_SH, STAR = hx('D3D9E2'), hx('A9B2BF'), hx('FFD23F')
WHITE, PUPIL, CHEEK = (255, 255, 255), hx('1A1214'), hx('FF9DB5')
MOUTH_IN, TONGUE = hx('6B1F2A'), hx('FF7A8A')
ANT = {'y': hx('FFD23F'), 'r': hx('FF4D4D'), 'g': hx('7BD43B')}
SQ_PINK, SQ_YEL = hx('FF4FA0'), hx('FFC928')

def clamp(v, a=0.0, b=1.0): return max(a, min(b, v))
def lerp(a, b, t): return a + (b - a) * t
def ease_in(t): return t * t
def back_out(t):
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def seg(t, a, b): return clamp((t - a) / (b - a))

@lru_cache(maxsize=256)
def font(sz): return ImageFont.truetype(FONT, max(4, int(sz)))

def bez3(p0, p1, p2, p3, n=28):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                    u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))
    return out

def bez2(p0, p1, p2, n=8):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))
    return out

def ell_pts(cx, cy, rx, ry, n=36, a0=0, a1=2*math.pi):
    return [(cx + rx*math.cos(a0 + (a1-a0)*i/n), cy + ry*math.sin(a0 + (a1-a0)*i/n)) for i in range(n + 1)]

RIGHT_EDGE = bez3((80, 40), (120, 40), (128, 80), (124, 105))
BODY = RIGHT_EDGE + bez3((124, 105), (124, 106), (36, 106), (36, 105))[1:-1] + bez3((36, 105), (32, 80), (40, 40), (80, 40))
SHADE = RIGHT_EDGE[9:] + [(124, 106), (104, 106)] + list(reversed(bez2((96, 48), (112, 74), (104, 106))))

def rot_pts(pts, ox, oy, a):
    c, s = math.cos(a), math.sin(a)
    return [(ox + (x-ox)*c - (y-oy)*s, oy + (x-ox)*s + (y-oy)*c) for x, y in pts]

class Pen:
    def __init__(self, d, cx, base, s, sx=1, sy=1):
        self.d, self.cx, self.base, self.s, self.sx, self.sy = d, cx, base, s, sx, sy
        self.olw = 2.3
    def P(self, x, y):
        return ((self.cx + (x - 80) * self.s * self.sx) * SS, (self.base + (y - 150) * self.s * self.sy) * SS)
    def _line(self, q, ww, col, closed=False):
        if closed: q = q + [q[0], q[1]]
        self.d.line(q, fill=col, width=max(1, int(ww)), joint='curve')
        r = ww / 2
        if not closed:
            for (x, y) in (q[0], q[-1]):
                self.d.ellipse([x-r, y-r, x+r, y+r], fill=col)
    def shape(self, pts, fill, outline=True):
        q = [self.P(*p) for p in pts]
        self.d.polygon(q, fill=fill)
        if outline:
            self._line(q, self.olw * self.s * SS, OL, closed=True)
    def ell(self, cx, cy, rx, ry, fill, outline=True):
        self.shape(ell_pts(cx, cy, rx, ry)[:-1], fill, outline)
    def stroke(self, pts, w, col, outline=True):
        q = [self.P(*p) for p in pts]
        if outline:
            self._line(q, (w + 2 * self.olw) * self.s * SS, OL)
        self._line(q, w * self.s * SS, col)

def make_bg():
    bg = Image.new('RGB', (WW, HH))
    d = ImageDraw.Draw(bg)
    top, bot = hx('7ED8F0'), hx('D8F6F2')
    for y in range(HH):
        t = y / HH
        d.line([(0, y), (WW, y)], fill=tuple(int(lerp(top[i], bot[i], t)) for i in range(3)))
    S = SS
    def blob(cx, cy, r, col):
        pts = []
        for i in range(60):
            a = 2 * math.pi * i / 60
            rr = r * (1 + 0.08 * math.sin(a * 5) + 0.04 * math.sin(a * 9))
            pts.append(((cx + rr * math.cos(a)) * S, (cy + rr * 0.8 * math.sin(a)) * S))
        d.polygon(pts, fill=col)
        d.line(pts + [pts[0], pts[1]], fill=OL, width=9 * S, joint='curve')
    for cx, cy, r, col in [(-40, 1450, 230, hx('3FA34D')), (1120, 1420, 250, hx('3FA34D')),
                           (60, 1560, 170, hx('5CC25B')), (1030, 1560, 180, hx('5CC25B'))]:
        blob(cx, cy, r, col)
    hill = [((-100 + i * 13) * S, (1640 + 70 * math.sin(i / 14) - 40 * math.cos(i / 9)) * S) for i in range(100)]
    poly = hill + [(1400 * S, 2000 * S), (-100 * S, 2000 * S)]
    d.polygon(poly, fill=hx('9ACD4C'))
    d.line(hill, fill=OL, width=10 * S, joint='curve')
    for x0, y0 in [(120, 1790), (420, 1860), (700, 1800), (940, 1880), (260, 1700)]:
        d.line([(x0*S, y0*S), ((x0+12)*S, (y0-26)*S), ((x0+26)*S, y0*S)], fill=hx('6E9E2E'), width=6 * S, joint='curve')
    return bg

def cloud(d, cx, cy, s):
    parts = [(0, 0, 58), (-66, 14, 42), (68, 14, 46), (-32, -28, 42), (34, -26, 48)]
    for dx, dy, r in parts:
        rr = r * s + 5
        d.ellipse([(cx+dx*s-rr)*SS, (cy+dy*s-rr)*SS, (cx+dx*s+rr)*SS, (cy+dy*s+rr)*SS], fill=OL)
    for dx, dy, r in parts:
        rr = r * s
        d.ellipse([(cx+dx*s-rr)*SS, (cy+dy*s-rr)*SS, (cx+dx*s+rr)*SS, (cy+dy*s+rr)*SS], fill=WHITE)

def squiggles(d, cx, cy, t, spread=1.0):
    specs = [(-1, -40, SQ_PINK, 0.0), (1, -60, SQ_YEL, 1.3), (-1, 60, SQ_YEL, 2.1), (1, 40, SQ_PINK, 3.0)]
    for side, dy, col, ph in specs:
        x0 = cx + side * 330 * spread
        pts = []
        for k in range(22):
            u = k / 21
            x = x0 + side * u * 70 + 18 * math.sin(u * 10 + t * 8 + ph)
            y = cy + dy + (u - 0.5) * 170
            pts.append((x * SS, y * SS))
        d.line(pts, fill=col, width=11 * SS, joint='curve')

def draw_nino(d, t, cx, base, s, st):
    n = Pen(d, cx, base, s, st.get('sx', 1), st.get('sy', 1))
    n.ell(62, 145, 12, 6.5, TEAL_D); n.ell(98, 145, 12, 6.5, TEAL_D)
    tip = 4 * math.sin(t * 5)
    n.stroke(bez2((80, 44), (80 + tip/2, 32), (80 + tip, 23)), 3.2, TEAL_D)
    n.ell(80 + tip, 18, 7.5, 7.5, ANT[st['ant']])
    n.ell(80 + tip - 2.5, 15.5, 2.2, 2.2, WHITE, outline=False)
    pose = st['pose']
    def arm(pts): n.stroke(pts, 8.5, TEAL)
    if pose == 'rest':
        arm(bez2((42, 110), (27, 120), (30, 134))); arm(bez2((118, 110), (133, 120), (130, 134)))
    elif pose == 'shock':
        arm(bez2((42, 108), (19, 98), (22, 72))); arm(bez2((118, 108), (141, 98), (138, 72)))
    elif pose == 'wave':
        arm(bez2((42, 110), (27, 120), (30, 134)))
        a = math.radians(-25 + 40 * (0.5 + 0.5 * math.sin(t * 9)))
        arm(rot_pts(bez2((120, 108), (146, 100), (150, 74)), 120, 108, a))
    n.shape(BODY, TEAL, outline=False)
    n.shape(SHADE, TEAL_SH, outline=False)
    n.shape(ell_pts(60, 54, 10, 6)[:-1], TEAL_HI, outline=False)
    n.shape(BODY, None) if False else n._line([n.P(*p) for p in BODY], n.olw * s * SS, OL, closed=True)
    suit = [(38 + 14 - 14*math.cos(a), 100 + 14 - 14*math.sin(a)) for a in [i*math.pi/16 for i in range(9)]]
    suit = ell_pts(52, 114, 14, 14, 8, math.pi, 1.5*math.pi) + ell_pts(108, 114, 14, 14, 8, 1.5*math.pi, 2*math.pi) \
         + ell_pts(108, 126, 14, 14, 8, 0, 0.5*math.pi) + ell_pts(52, 126, 14, 14, 8, 0.5*math.pi, math.pi)
    n.shape(suit, SILVER, outline=False)
    n.shape([(98, 101), (110, 101), (122, 114), (122, 126), (110, 140), (100, 140)], SILVER_SH, outline=False)
    n._line([n.P(*p) for p in suit], n.olw * s * SS, OL, closed=True)
    star = []
    for i in range(10):
        r = 11 if i % 2 == 0 else 4.8
        a = -math.pi/2 + i * math.pi / 5
        star.append((80 + r*math.cos(a), 120 + r*math.sin(a)))
    n.olw = 1.6; n.shape(star, STAR); n.olw = 2.3
    lx, ly = st.get('look', (0, 0))
    eyes = st['eyes']
    for ex in (65, 95):
        if eyes == 'shock':
            n.ell(ex, 70, 14, 15, WHITE); n.ell(ex + lx, 70 + ly, 3, 3, PUPIL, outline=False)
            n.stroke(bez2((ex - 10, 50), (ex, 44), (ex + 10, 50)), 1.6, OL, outline=False)
        elif eyes == 'blink':
            n.stroke(bez2((ex - 11, 72), (ex, 77), (ex + 11, 72)), 2.4, OL, outline=False)
        elif eyes == 'happy':
            n.stroke(bez2((ex - 10, 76), (ex, 61), (ex + 10, 76)), 2.6, OL, outline=False)
        else:
            n.ell(ex, 71, 12.5, 14, WHITE); n.ell(ex + 2 + lx, 72 + ly, 4.6, 4.6, PUPIL, outline=False)
            n.ell(ex + 3.5 + lx, 70 + ly, 1.4, 1.4, WHITE, outline=False)
    n.ell(50, 89, 6, 4, CHEEK, outline=False); n.ell(110, 89, 6, 4, CHEEK, outline=False)
    m = st['mouth']
    n.olw = 1.8
    if m == 'smile':
        pts = bez2((70, 90), (80, 104), (90, 90))
        n.shape(pts, MOUTH_IN)
        n.ell(80, 97.5, 4.2, 2.2, TONGUE, outline=False)
    elif m == 'o':
        n.ell(80, 95, 7, 9, MOUTH_IN); n.ell(80, 100, 4, 2.4, TONGUE, outline=False)
    elif m == 'big':
        pts = bez2((67, 89), (80, 112), (93, 89))
        n.shape(pts, MOUTH_IN)
        n.ell(80, 101, 6, 3.2, TONGUE, outline=False)
        n.shape([(70, 89.5), (90, 89.5), (88, 93), (72, 93)], WHITE, outline=False)
    n.olw = 2.3

def text(d, s, cx, cy, size, fill=STAR, sw=None):
    f = font(size * SS)
    sw = sw if sw is not None else max(3, int(size * 0.1))
    d.text((cx * SS, cy * SS), s, font=f, fill=fill, anchor='mm', stroke_width=sw * SS, stroke_fill=OL)

def jellyfish(d, cx, cy, s, t):
    S = SS
    for i, ox in enumerate((-38, -14, 14, 38)):
        pts = []
        for k in range(14):
            yy = cy + 8*s + k * 10 * s
            xx = cx + ox*s + 9*s*math.sin(t * 4 + k * 0.6 + i)
            pts.append((xx * S, yy * S))
        d.line(pts, fill=OL, width=int(12 * s * S), joint='curve')
        d.line(pts, fill=hx('FF7FB0'), width=int(6.5 * s * S), joint='curve')
    bell = [((cx + 62*s*math.cos(a)) * S, (cy + 55*s*math.sin(a)) * S) for a in [math.pi + i*math.pi/30 for i in range(31)]]
    bell += [((cx + 62*s) * S, (cy + 10*s) * S), ((cx - 62*s) * S, (cy + 10*s) * S)]
    d.polygon(bell, fill=hx('FFB3D1'))
    d.line(bell + [bell[0], bell[1]], fill=OL, width=int(5 * s * S), joint='curve')
    for ex in (-20, 20):
        d.ellipse([(cx+ex*s-9*s)*S, (cy-30*s)*S, (cx+ex*s+9*s)*S, (cy-10*s)*S], fill=WHITE, outline=OL, width=int(3*s*S))
        d.ellipse([(cx+ex*s-3*s)*S, (cy-22*s)*S, (cx+ex*s+3*s)*S, (cy-16*s)*S], fill=PUPIL)
    d.arc([(cx-10*s)*S, (cy-12*s)*S, (cx+10*s)*S, (cy+2*s)*S], 20, 160, fill=OL, width=int(3.5*s*S))

def frame(t, bg):
    im = bg.copy(); d = ImageDraw.Draw(im)
    for x0, y, sc, sp in [(200, 340, 1.0, 18), (820, 540, 0.8, 12), (560, 180, 0.6, 25)]:
        x = (x0 + sp * t) % 1400 - 160
        cloud(d, x, y, sc)
    cx, base, s = 540, 1700, 5.0
    st = {'ant': 'y', 'pose': 'rest', 'eyes': 'normal', 'mouth': 'smile'}
    if t < 0.8:
        base = lerp(-300, 1700, ease_in(seg(t, 0, 0.8)))
        st.update(sy=1.12, sx=0.92, mouth='o', pose='shock', eyes='shock')
    elif t < 1.3:
        k = seg(t, 0.8, 1.3)
        amp = math.sin(k * math.pi * 2.5) * (1 - k)
        st.update(sy=1 - 0.22 * amp, sx=1 + 0.18 * amp)
    else:
        b = 0.015 * math.sin(t * 3)
        st.update(sy=1 + b, sx=1 - b / 2)
    if 2.6 < t < 2.75 or 5.6 < t < 5.72:
        st['eyes'] = 'blink'
    bubble = 0.0
    if 4.0 <= t < 9.6:
        bubble = back_out(seg(t, 4.0, 4.45))
        st['look'] = (-1, -5)
        if t < 7.0: st['mouth'] = 'o'
    if 9.6 <= t < 9.95:
        bubble = 1 - ease_in(seg(t, 9.6, 9.95))
    sq = False
    if 7.0 <= t < 9.6:
        st.update(ant='r', pose='shock', eyes='shock', mouth='o', look=(0, -2))
        base -= math.sin(seg(t, 7.0, 7.35) * math.pi) * 80
        cx += 9 * math.sin(t * 60) * (1 if t > 7.35 else 0)
        sq = True
    if t >= 9.6:
        st.update(ant='g', pose='wave', eyes='happy', mouth='big')
        base -= abs(math.sin(seg(t, 9.6, 10.6) * math.pi * 2)) * 40 * (1 - seg(t, 9.6, 10.6))
        sq = True
    if 0.8 <= t < 1.3:
        sq = True
    if sq:
        squiggles(d, 540, 1350, t)
    if bubble > 0.01:
        bx, by, br = 540, 720, 250 * bubble
        d.ellipse([(bx-br-12)*SS, (by-br-12)*SS, (bx+br+12)*SS, (by+br+12)*SS], fill=OL)
        tri = [(492*SS, (by+br-10)*SS), (588*SS, (by+br-10)*SS), (540*SS, (by+br+70*bubble)*SS)]
        d.polygon([(x, y) for x, y in tri], fill=OL)
        tri2 = [(504*SS, (by+br-20)*SS), (576*SS, (by+br-20)*SS), (540*SS, (by+br+52*bubble)*SS)]
        d.ellipse([(bx-br)*SS, (by-br)*SS, (bx+br)*SS, (by+br)*SS], fill=WHITE)
        d.polygon(tri2, fill=WHITE)
        d.ellipse([(bx-br*0.88)*SS, (by-br*0.88)*SS, (bx+br*0.88)*SS, (by+br*0.88)*SS], fill=hx('3E9BE8'))
        d.ellipse([(bx-br*0.88)*SS, (by+br*0.25)*SS, (bx+br*0.88)*SS, (by+br*0.88)*SS], fill=hx('2C7FD1'))
        d.ellipse([(bx-br*0.88)*SS, (by-br*0.88)*SS, (bx+br*0.88)*SS, (by+br*0.88)*SS], outline=OL, width=6*SS)
        for k, (ox, oy, r) in enumerate([(-150, 80, 11), (-120, -60, 8), (140, 40, 10), (110, -120, 7)]):
            yy = by + (oy - (t * 40 + k * 30) % 120) * bubble
            d.ellipse([(bx+ox*bubble-r)*SS, (yy-r)*SS, (bx+ox*bubble+r)*SS, (yy+r)*SS], outline=WHITE, width=4*SS)
        if bubble > 0.3:
            jellyfish(d, bx, by - 40 + 12 * math.sin(t * 2.5), 1.35 * bubble, t)
    draw_nino(d, t, cx, base, s, st)
    def pop(a, dur=0.35): return back_out(seg(t, a, a + dur))
    if 1.3 <= t < 4.0:
        text(d, 'DIÁRIO DO NINO', 540, 230, 100 * pop(1.3))
        text(d, 'descoberta nº 1', 540, 350, 62 * pop(1.6), fill=WHITE)
    elif 4.0 <= t < 7.0:
        text(d, 'Existe uma água-viva', 540, 220, 72 * pop(4.2), fill=WHITE)
        text(d, 'que volta a ser BEBÊ!', 540, 325, 78 * pop(4.6))
    elif 7.0 <= t < 9.6:
        sc = 1 + 0.04 * math.sin(t * 20)
        text(d, 'COMO ASSIM?!', 540, 270, 112 * pop(7.0, 0.3) * sc, fill=hx('FF5A5A'))
    elif t >= 9.6:
        text(d, 'QUE PLANETA', 540, 230, 120 * pop(9.7))
        text(d, 'DOIDO!', 540, 375, 140 * pop(9.9))
        text(d, '@ninoverso', 540, 1845, 58 * pop(10.4), fill=WHITE)
    return im.resize((W, H), Image.LANCZOS)

bg = make_bg()
N = int(DUR * FPS)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                       '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast',
                       '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(N):
    t = i / FPS
    im = frame(t, bg)
    if PREVIEW and i in (int(1.0*FPS), int(3*FPS), int(5.5*FPS), int(8*FPS), int(11*FPS)):
        im.save(f'{PREVIEW}/g_{i:03d}.png')
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
print('done', N, 'frames')
