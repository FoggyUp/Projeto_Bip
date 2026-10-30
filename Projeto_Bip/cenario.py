"""Cenário pastel (céu, sol, nuvens, casinhas, árvores, grama com flores), tirado do still2.py.

desenhar_cenario(W, H, ss) devolve a imagem em tamanho supersampled (W*ss x H*ss). O desenho original é
de 1080x1350; em outras alturas (ex.: 1920 para vídeo 9:16) o céu ocupa a tela toda e o chão desce junto
com a borda de baixo. chao(H) é a altura em que os personagens pisam.

Uso direto: python cenario.py saida.png [altura]
"""
import math, sys
from PIL import Image, ImageDraw
from desenho import OL, WHITE, hx, lerp_cor, linha

CHAO_1350 = 1252

def chao(H): return CHAO_1350 + H - 1350

def desenhar_cenario(W=1080, H=1350, ss=3):
    im = Image.new('RGB', (W * ss, H * ss))
    d = ImageDraw.Draw(im)
    S = ss
    dy = H - 1350
    # ---------- céu ----------
    top, bot = hx('9FDFF0'), hx('F6F7DE')
    for y in range(H * S):
        d.line([(0, y), (W * S, y)], fill=lerp_cor(top, bot, y / (H * S)))
    for r, col in [(150, hx('FFF3C4')), (110, hx('FFE9A0')), (78, hx('FFD95E'))]:
        d.ellipse([(900-r)*S, (170-r)*S, (900+r)*S, (170+r)*S], fill=col)
    def soft_cloud(cx, cy, s):
        for ox, oy, r in [(0, 8, 60), (-62, 20, 44), (66, 20, 48)]:
            d.ellipse([(cx+ox*s-r*s)*S, (cy+oy*s-r*s)*S, (cx+ox*s+r*s)*S, (cy+oy*s+r*s)*S], fill=hx('DDEFF6'))
        for ox, oy, r in [(0, 0, 58), (-64, 14, 42), (66, 14, 46), (-30, -28, 42), (34, -26, 48)]:
            d.ellipse([(cx+ox*s-r*s)*S, (cy+oy*s-r*s)*S, (cx+ox*s+r*s)*S, (cy+oy*s+r*s)*S], fill=WHITE)
    soft_cloud(180, 230, 1.1); soft_cloud(760, 330, 0.7); soft_cloud(980, 640 + dy / 2, 0.6); soft_cloud(110, 620 + dy / 2, 0.55)
    # ---------- chão (desce junto com a borda de baixo) ----------
    for cx, cy, rx, ry, col in [(150, 1170, 520, 230, hx('BDE296')), (930, 1190, 560, 250, hx('AAD982'))]:
        d.ellipse([(cx-rx)*S, (cy+dy-ry)*S, (cx+rx)*S, (cy+dy+ry)*S], fill=col)
    houses = [(-30, 160, hx('FFB27A'), hx('E8604C')), (105, 125, hx('FFE07A'), hx('5BA7E6')),
              (850, 130, hx('9FD8F7'), hx('E8604C')), (975, 165, hx('C9A6F2'), hx('F28C3A'))]
    base = 1150 + dy
    for x, hgt, wall, roof in houses:
        w = 120
        d.rectangle([x*S, (base-hgt)*S, (x+w)*S, base*S], fill=wall, outline=OL, width=4*S)
        d.polygon([((x-12)*S, (base-hgt)*S), ((x+w+12)*S, (base-hgt)*S), ((x+w/2)*S, (base-hgt-70)*S)], fill=roof, outline=OL, width=4*S)
        for wx in (x+22, x+70):
            d.rectangle([wx*S, (base-hgt+30)*S, (wx+28)*S, (base-hgt+60)*S], fill=hx('FFF6D6'), outline=OL, width=3*S)
        d.rectangle([(x+46)*S, (base-55)*S, (x+74)*S, base*S], fill=hx('B8805C'), outline=OL, width=3*S)
    for tx, sc in ((290, 1.0), (775, 0.9)):
        d.rectangle([(tx-10*sc)*S, (base-95*sc)*S, (tx+10*sc)*S, base*S], fill=hx('B8805C'), outline=OL, width=3*S)
        for ox, oy, r in [(0, -150, 62), (-40, -115, 46), (40, -115, 48)]:
            d.ellipse([(tx+ox*sc-r*sc)*S, (base+oy*sc-r*sc)*S, (tx+ox*sc+r*sc)*S, (base+oy*sc+r*sc)*S], fill=hx('6CC46A'), outline=OL, width=4*S)
        for ox, oy, r in [(0, -150, 58), (-40, -115, 42), (40, -115, 44)]:
            d.ellipse([(tx+ox*sc-r*sc)*S, (base+oy*sc-r*sc)*S, (tx+ox*sc+r*sc)*S, (base+oy*sc+r*sc)*S], fill=hx('6CC46A'))
        d.ellipse([(tx-30*sc)*S, (base-185*sc)*S, (tx-6*sc)*S, (base-170*sc)*S], fill=hx('9BDB8A'))
    grass = [((-50 + i * 12) * S, (base + 18 * math.sin(i / 7)) * S) for i in range(110)]
    d.polygon(grass + [(1400 * S, (H + 50) * S), (-50 * S, (H + 50) * S)], fill=hx('94D25F'))
    linha(d, grass, 5 * S, OL)
    for fx, fy, col in [(90, 1260, hx('FF8FB1')), (990, 1240, hx('FFD54A')), (200, 1320, WHITE), (880, 1320, hx('FF8FB1'))]:
        fy += dy
        for k in range(5):
            a = k * 2 * math.pi / 5
            d.ellipse([(fx+11*math.cos(a)-8)*S, (fy+11*math.sin(a)-8)*S, (fx+11*math.cos(a)+8)*S, (fy+11*math.sin(a)+8)*S], fill=col, outline=OL, width=2*S)
        d.ellipse([(fx-6)*S, (fy-6)*S, (fx+6)*S, (fy+6)*S], fill=hx('FFB13B'))
    return im


if __name__ == '__main__':
    W, H, SS = 1080, int(sys.argv[2]) if len(sys.argv) > 2 else 1350, 3
    desenhar_cenario(W, H, SS).resize((W, H), Image.LANCZOS).save(sys.argv[1])
    print('ok')
