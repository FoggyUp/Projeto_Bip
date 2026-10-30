"""Bip, o cachorrinho robô.

draw_bip(im, estado, cx, base, s, ss) desenha o Bip numa cena supersampled (como a de cenario.desenhar_cenario).
O estado é um dicionário; o que faltar vem de PADRAO:

  olhos    'normal', 'feliz', 'coracao', 'espiral', 'interrogacao', 'surpreso' ou 'estrela'
  olhar    (dx, dy): para onde os olhos normais olham, em unidades do personagem (uns 3 no máximo)
  giro     ângulo da espiral, em radianos (para girar na animação)
  boca     'sorriso', 'aberta' ou 'o'
  antena   0 (luz apagada) a 1 (acesa, com raios): alterne para piscar
  rabo     graus em volta da base do rabo de mola: positivo abaixa (para fora), negativo levanta
           (para perto da cabeça; passe de -15 e a bolinha some atrás dela); para abanar, oscile perto de 0
  orelhas  graus, ou (esquerda, direita): positivo levanta para fora, negativo cola na cabeça
  sx, sy   esticar ou achatar a partir do pé (ex.: sx=1.1, sy=0.9 ao cair no chão)

Uso direto: python bip.py saida.png [olhos] [boca]
"""
import math, sys
from PIL import Image, ImageChops, ImageDraw
from desenho import OL, WHITE, Pen, bez2, bez3, ell_pts, heart_pts, hx, lerp, lerp_cor, rot_pts, rrect, star_pts

BODY_C, BODY_SH, BODY_HI = hx('EEF2F7'), hx('C8D1DD'), hx('FFFFFF')
METAL, METAL_D = hx('9AA7B8'), hx('AEB9C8')
EAR, EAR_SH, EAR_IN = hx('FF6F6F'), hx('E04F57'), hx('FFB0B0')
SCREEN, SCREEN_HI, SCREEN_GLARE = hx('1E2A44'), hx('2E3E60'), hx('34466A')
EYE, EYE_SH = hx('5EF2DA'), hx('2FD1BC')
HEART, HEART_SH = hx('FF6FA3'), hx('E0457F')
NOSE, COLLAR, GOLD, GOLD_SH = hx('2B1A15'), hx('FF5A5A'), hx('FFD54A'), hx('F2B630')
ANT_OFF = hx('8E3B44')
CHEEK, MOUTH_IN, TONGUE, TONGUE_D = hx('FFA9BC'), hx('9C2B3B'), hx('FF8A99'), hx('E0606F')
SOMBRA = hx('7CBF4C')

EXPRESSOES = ('normal', 'feliz', 'coracao', 'espiral', 'interrogacao', 'surpreso', 'estrela')
BOCAS = ('sorriso', 'aberta', 'o')
PADRAO = {'olhos': 'normal', 'olhar': (0, 0), 'giro': 0.0, 'boca': 'sorriso', 'antena': 1.0,
          'rabo': 0.0, 'orelhas': 0.0, 'sx': 1.0, 'sy': 1.0}

# caixa do Bip em coordenadas locais (com folga para as orelhas e o rabo mexerem)
CAIXA = (-12, -6, 172, 158)
EYES_X, EYES_Y = (68, 92), 66


def draw_bip(im, estado=None, cx=540, base=1252, s=5.4, ss=3, sombra=SOMBRA):
    st = {**PADRAO, **(estado or {})}
    sx, sy = st['sx'], st['sy']
    if sombra:
        ImageDraw.Draw(im).ellipse([(cx - 34 * s * sx) * ss, (base - 4 * s) * ss, (cx + 34 * s * sx) * ss, (base + 4 * s) * ss], fill=sombra)
    # o Bip é desenhado numa camada do tamanho dele (máscaras pequenas) e depois colado na cena
    x0, y0 = int((cx + (CAIXA[0] - 80) * s * sx) * ss), int((base + (CAIXA[1] - 150) * s * sy) * ss)
    x1, y1 = int((cx + (CAIXA[2] - 80) * s * sx) * ss) + 1, int((base + (CAIXA[3] - 150) * s * sy) * ss) + 1
    layer = Image.new('RGBA', (x1 - x0, y1 - y0), (0, 0, 0, 0))
    p = Pen(layer, cx, base, s, ss, sx, sy, x0, y0)
    _rabo(p, st)
    _corpo(p)
    _orelhas(p, st)
    _antena(p, st)
    _cabeca(p, st)
    _focinho(p, st)
    im.paste(layer, (x0, y0), layer)


# ---------- corpo ----------
def _rabo(p, st):
    spring = []
    for i in range(41):
        u = i / 40
        x = lerp(110, 128, u) + 3.2 * math.sin(u * math.pi * 8)
        y = lerp(124, 98, u) + 3.2 * math.cos(u * math.pi * 8) * 0.6
        spring.append((x, y))
    a = math.radians(st['rabo'])
    spring = rot_pts(spring, 110, 124, a)
    (bx, by), = rot_pts([(129, 95)], 110, 124, a)
    p.stroke(spring, 2.2, BODY_SH, olw=1.0)
    p.shape(ell_pts(bx, by, 5.5, 5.5), COLLAR)
    p.shape(ell_pts(bx - 1.5, by - 1.5, 1.8, 1.8), WHITE, outline=False)

def _corpo(p):
    for lx in (60, 100):
        p.shaded(rrect(lx - 7, 122, lx + 7, 147, 6), BODY_SH, METAL_D)
    p.shaded(ell_pts(80, 124, 31, 18), BODY_C, BODY_SH, BODY_HI, hi_pts=ell_pts(66, 114, 9, 3.5))
    for lx in (68, 92):
        p.shaded(rrect(lx - 7.5, 126, lx + 7.5, 150, 6.5), BODY_C, BODY_SH)
        p.shape(rrect(lx - 7.5, 144, lx + 7.5, 150, 3), METAL)
        for k in (-3.5, 0, 3.5):
            p.line([(lx + k, 146), (lx + k, 148.5)], 0.8, OL)
    # medalha de ossinho
    p.shape(ell_pts(80, 120, 7, 7), GOLD)
    p.shape(ell_pts(81, 121, 5, 5), GOLD_SH, outline=False)
    p.shape(ell_pts(79.5, 119.5, 5, 5), GOLD, outline=False)
    p.shape(rrect(76.2, 118.7, 83.8, 121.3, 1.3), WHITE, outline=False)
    for bx in (76, 84):
        for by in (118.4, 121.6):
            p.shape(ell_pts(bx, by, 1.5, 1.5, 16), WHITE, outline=False)
    # coleira
    collar = bez3((52, 104), (64, 110), (96, 110), (108, 104)) + list(reversed(bez3((50, 98), (64, 104), (96, 104), (110, 98))))
    p.shape(collar, COLLAR)
    for xx in (60, 70, 90, 100):
        p.shape(ell_pts(xx, 104.5, 1.3, 1.3, 16), GOLD, outline=False)

def _orelhas(p, st):
    o = st['orelhas']
    angs = {-1: o[0], 1: o[1]} if isinstance(o, (tuple, list)) else {-1: o, 1: o}
    for side in (-1, 1):
        ex = 80 + side * 34
        px, py = ex - side * 2, 50
        a = math.radians(-side * angs[side])
        ear = [(ex - side * 4, 48), (ex + side * 6, 46)] + bez2((ex + side * 6, 46), (ex + side * 22, 66), (ex + side * 16, 92), n=14)[1:] \
              + bez2((ex + side * 16, 92), (ex + side * 8, 98), (ex + side * 2, 88), n=10)[1:] + bez2((ex + side * 2, 88), (ex - side * 2, 66), (ex - side * 4, 48), n=10)[1:]
        inner = bez2((ex + side * 3, 54), (ex + side * 14, 68), (ex + side * 11, 86), n=10) + bez2((ex + side * 11, 86), (ex + side * 6, 84), (ex + side * 4, 70), n=8)[1:]
        ear, inner = rot_pts(ear, px, py, a), rot_pts(inner, px, py, a)
        m = p.mask(ear); p.paint(m, EAR)
        p.paint(ImageChops.subtract(m, p.mask([(x - side * 3, y - 3) for x, y in ear])), EAR_SH)
        p.paint(ImageChops.multiply(m, p.mask(inner)), EAR_IN)
        p.line(ear, p.olw, OL, closed=True)
        p.shape(ell_pts(px, py, 4.5, 4.5), METAL)

def _antena(p, st):
    luz = max(0.0, min(1.0, st['antena']))
    p.stroke(bez2((80, 40), (79, 32), (82, 25)), 2.4, METAL)
    p.shape(ell_pts(80, 39.5, 6, 2.6), BODY_SH, w=0.9)
    p.shape(ell_pts(82.5, 21, 5.8, 5.8), lerp_cor(ANT_OFF, COLLAR, luz))
    p.shape(ell_pts(81, 19.5, 2 * (0.6 + 0.4 * luz), 2 * (0.6 + 0.4 * luz)), WHITE, outline=False)
    if luz >= 0.5:
        for a in (-150, -105, -40, 0):
            ar = math.radians(a)
            p.line([(82.5 + 8.5 * math.cos(ar), 21 + 8.5 * math.sin(ar)), (82.5 + 12 * math.cos(ar), 21 + 12 * math.sin(ar))], 1.1, COLLAR)


# ---------- cabeça e tela ----------
def _cabeca(p, st):
    p.shaded(rrect(40, 40, 120, 104, 27, 12), BODY_C, BODY_SH, BODY_HI, dx=-7, dy=-3, hi_pts=ell_pts(58, 47, 12, 4))
    for bx in (44.5, 115.5):
        p.shape(ell_pts(bx, 72, 2.6, 2.6, 20), hx('B7C1CE'), w=0.8)
        p.line([(bx - 1.6, 72), (bx + 1.6, 72)], 0.7, OL)
    scr = rrect(52, 49, 108, 85, 13, 10)
    sm = p.mask(scr); p.paint(sm, SCREEN)
    p.paint(ImageChops.multiply(sm, p.mask([(52, 49), (78, 49), (60, 85), (52, 85)])), SCREEN_HI)
    p.line(scr, 1.1, OL, closed=True)
    p.paint(ImageChops.multiply(sm, p.mask([(103, 51), (107, 51), (99, 70), (95, 70)])), SCREEN_GLARE)
    OLHOS[st['olhos']](p, sm, st)

# Tudo o que aparece na tela é recortado por ela (sm): a tela é o "rosto" do Bip.
def _na_tela(p, sm, pts, col):
    p.paint(ImageChops.multiply(sm, p.mask(pts)), col)

def _traco_na_tela(p, sm, pts, w, col):
    p.paint(ImageChops.multiply(sm, p.stroke_mask(pts, w)), col)

def _olhos_normal(p, sm, st):
    lx, ly = st['olhar']
    for ex in EYES_X:
        ex, ey = ex + lx, EYES_Y + ly
        em = ImageChops.multiply(sm, p.mask(ell_pts(ex, ey, 7.2, 9.5)))
        p.paint(em, EYE)
        p.paint(ImageChops.multiply(em, p.mask(ell_pts(ex + 1.5, ey + 3.5, 6.2, 6.5))), EYE_SH)
        p.paint(ImageChops.multiply(em, p.mask(ell_pts(ex, ey - 1.5, 6.2, 7.5))), EYE)
        _na_tela(p, sm, ell_pts(ex + 2.2, ey - 4, 2.4, 2.8), WHITE)
        _na_tela(p, sm, ell_pts(ex - 2.2, ey + 4, 1.1, 1.1), WHITE)

def _olhos_feliz(p, sm, st):
    for ex in EYES_X:
        arc = bez2((ex - 6.5, 70), (ex, 56), (ex + 6.5, 70), n=16)
        _traco_na_tela(p, sm, [(x, y + 1) for x, y in arc], 3.4, EYE_SH)
        _traco_na_tela(p, sm, arc, 3.4, EYE)

def _olhos_coracao(p, sm, st):
    for ex in EYES_X:
        h = heart_pts(ex, 65, 8.6)
        hm = ImageChops.multiply(sm, p.mask(h))
        p.paint(hm, HEART)
        p.paint(ImageChops.subtract(hm, p.mask([(x - 1.6, y - 1.6) for x, y in h])), HEART_SH)
        _na_tela(p, sm, ell_pts(ex - 3.6, 61.5, 2.2, 1.6), WHITE)

def _olhos_espiral(p, sm, st):
    for ex in EYES_X:
        voltas, rmax = 2.25, 8.0
        n = 90
        pts = []
        for i in range(n + 1):
            th = voltas * 2 * math.pi * i / n
            r = rmax * i / n
            pts.append((ex + r * math.cos(th + st['giro']), EYES_Y + r * 1.12 * math.sin(th + st['giro'])))
        _traco_na_tela(p, sm, pts, 1.7, EYE)

def _olhos_interrogacao(p, sm, st):
    for ex in EYES_X:
        q = bez3((ex - 4.6, 61), (ex - 4.6, 53.5), (ex + 5.2, 53.5), (ex + 5, 60), n=24) \
            + bez3((ex + 5, 60), (ex + 4.8, 64.5), (ex, 63.5), (ex, 68.5), n=16)[1:]
        _traco_na_tela(p, sm, [(x + 0.6, y + 0.6) for x, y in q], 2.7, GOLD_SH)
        _traco_na_tela(p, sm, q, 2.7, GOLD)
        _na_tela(p, sm, ell_pts(ex + 0.6, 74.4, 1.9, 1.9), GOLD_SH)
        _na_tela(p, sm, ell_pts(ex, 73.8, 1.9, 1.9), GOLD)

def _olhos_surpreso(p, sm, st):
    for ex in EYES_X:
        _na_tela(p, sm, ell_pts(ex, EYES_Y, 8.8, 10.4), EYE)
        _na_tela(p, sm, ell_pts(ex, EYES_Y, 6.0, 7.4), SCREEN)
        _na_tela(p, sm, ell_pts(ex, EYES_Y, 2.8, 3.3), EYE)
        _na_tela(p, sm, ell_pts(ex + 3.8, EYES_Y - 5, 1.5, 1.7), WHITE)

def _olhos_estrela(p, sm, st):
    for ex in EYES_X:
        star = star_pts(ex, 66.5, 9, 3.9)
        stm = ImageChops.multiply(sm, p.mask(star))
        p.paint(stm, GOLD)
        p.paint(ImageChops.subtract(stm, p.mask([(x - 1.2, y - 1.2) for x, y in star])), GOLD_SH)
        _na_tela(p, sm, ell_pts(ex - 1.6, 63.5, 1.4, 1.4), WHITE)

OLHOS = {'normal': _olhos_normal, 'feliz': _olhos_feliz, 'coracao': _olhos_coracao, 'espiral': _olhos_espiral,
         'interrogacao': _olhos_interrogacao, 'surpreso': _olhos_surpreso, 'estrela': _olhos_estrela}


# ---------- focinho e boca ----------
def _focinho(p, st):
    p.shape(ell_pts(80, 93.5, 15, 8.5), BODY_HI, w=1.0)
    boca = st['boca']
    if boca == 'sorriso':
        p.line([(80, 92.3), (80, 95)], 0.9, OL)
        mouth = bez2((72, 94), (76, 99.5), (80, 95), n=10) + bez2((80, 95), (84, 99.5), (88, 94), n=10)[1:]
        p.line(mouth, 0.95, OL)
        p.shape(bez2((77.5, 97), (80, 104.5), (82.5, 97), n=12), TONGUE, w=0.85)
        p.line([(80, 98), (80, 101)], 0.6, TONGUE_D)
    elif boca == 'aberta':
        mouth = bez2((71, 93.8), (80, 92.6), (89, 93.8), n=8) + bez2((89, 93.8), (80, 109), (71, 93.8), n=20)[1:-1]
        mm = p.mask(mouth); p.paint(mm, MOUTH_IN)
        p.paint(ImageChops.multiply(mm, p.mask(ell_pts(80, 101, 5.2, 3.6))), TONGUE)
        p.line(mouth, 0.95, OL, closed=True)
    elif boca == 'o':
        p.line([(80, 92.3), (80, 93.6)], 0.9, OL)
        p.shape(ell_pts(80, 97.6, 3.1, 3.7), MOUTH_IN, w=0.9)
        p.shape(ell_pts(80, 99.3, 1.8, 1.2), TONGUE, outline=False)
    p.shape(ell_pts(80, 88.8, 5.2, 3.6), NOSE, w=0.9)
    p.shape(ell_pts(78.6, 87.8, 1.6, 0.9), WHITE, outline=False)
    p.shape(ell_pts(55, 93, 5.5, 3.4), CHEEK, outline=False); p.shape(ell_pts(105, 93, 5.5, 3.4), CHEEK, outline=False)


if __name__ == '__main__':
    from cenario import chao, desenhar_cenario
    W, H, SS = 1080, 1350, 3
    estado = {}
    if len(sys.argv) > 2: estado['olhos'] = sys.argv[2]
    if len(sys.argv) > 3: estado['boca'] = sys.argv[3]
    im = desenhar_cenario(W, H, SS)
    draw_bip(im, estado, cx=540, base=chao(H), s=5.4, ss=SS)
    im.resize((W, H), Image.LANCZOS).save(sys.argv[1])
    print('ok')
