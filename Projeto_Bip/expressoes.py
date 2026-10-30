"""Folha com o Bip em várias expressões, lado a lado, para conferir o visual.

Uso: python expressoes.py saida.png [olhos ...]
     padrão: normal coracao interrogacao
     olhos: normal feliz coracao espiral interrogacao surpreso estrela
"""
import sys
from PIL import Image, ImageDraw
from desenho import OL, fonte, hx
from cenario import chao, desenhar_cenario
from bip import draw_bip

W, H, SS = 1080, 1350, 3
# boca, orelhas, rabo e antena que combinam com cada olhar
COMBINA = {
    'normal': {'boca': 'sorriso'},
    'feliz': {'boca': 'aberta', 'orelhas': 10, 'rabo': -6},
    'coracao': {'boca': 'aberta', 'orelhas': 8, 'rabo': -10},
    'espiral': {'boca': 'o', 'orelhas': (-8, 14), 'rabo': 30, 'antena': 0.2},
    'interrogacao': {'boca': 'o', 'orelhas': (22, -6), 'rabo': 10},
    'surpreso': {'boca': 'o', 'orelhas': 24, 'rabo': -12},
    'estrela': {'boca': 'aberta', 'orelhas': 12, 'rabo': -8},
}
NOMES = {'normal': 'Normal', 'feliz': 'Feliz', 'coracao': 'Apaixonado', 'espiral': 'Tonto',
         'interrogacao': 'Confuso', 'surpreso': 'Surpreso', 'estrela': 'Encantado'}
CORTE = (170, 370, 910, 1330)  # em volta do Bip, em pixels da cena de 1080x1350

def main():
    out = sys.argv[1]
    olhos = sys.argv[2:] or ['normal', 'coracao', 'interrogacao']
    fundo = desenhar_cenario(W, H, SS)
    pw, ph = CORTE[2] - CORTE[0], CORTE[3] - CORTE[1]
    gap, faixa = 28, 130
    folha = Image.new('RGB', (len(olhos) * pw + (len(olhos) + 1) * gap, gap + ph + faixa), hx('FFF6D6'))
    d = ImageDraw.Draw(folha)
    canto = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(canto).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=24, fill=255)
    for i, o in enumerate(olhos):
        im = fundo.copy()
        draw_bip(im, {'olhos': o, **COMBINA.get(o, {})}, cx=540, base=chao(H), s=5.4, ss=SS)
        x = gap + i * (pw + gap)
        folha.paste(im.resize((W, H), Image.LANCZOS).crop(CORTE), (x, gap), canto)
        d.rounded_rectangle([x, gap, x + pw - 1, gap + ph - 1], radius=24, outline=OL, width=6)
        d.text((x + pw / 2, gap + ph + faixa / 2), NOMES.get(o, o), font=fonte(72), fill=hx('FFD54A'),
               anchor='mm', stroke_width=7, stroke_fill=OL)
    folha.save(out)
    print('ok')

if __name__ == '__main__':
    main()
