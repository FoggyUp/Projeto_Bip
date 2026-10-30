import sys, math, time
import numpy as np
from PIL import Image, ImageFilter

OUT = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 270
H = int(W * 1.25)
SSF = int(sys.argv[3]) if len(sys.argv) > 3 else 1
RW, RH = W * SSF, H * SSF

def hx(c):
    c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0
def lin(c): return c ** 2.2

C = {k: lin(hx(v)) for k, v in dict(
    teal='4FD3C4', teal_d='239C8E', silver='DCE3EC', silver_d='8F9CAE', yellow='FFC93A',
    white='FFFFFF', pupil='1E1416', brow='4A2E26', mouth='8E1F31', tongue='FF7E8E',
    cheek='FF98AE', spot='8AE8DD', glow='6BFFCB', grass='7FCB4A').items()}

YAW = math.radians(-14)
cy_, sy_ = math.cos(YAW), math.sin(YAW)

def length(v): return np.sqrt(np.sum(v * v, axis=-1))
def sd_ellipsoid(p, c, r):
    q = (p - c)
    k0 = length(q / r); k1 = length(q / (r * r))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
def sd_sphere(p, c, r): return length(p - c) - r
def sd_capsule(p, a, b, r):
    pa, ba = p - a, b - a
    h = np.clip(np.sum(pa * ba, -1) / np.dot(ba, ba), 0, 1)
    return length(pa - ba * h[:, None]) - r
def sd_rbox(p, c, b, r):
    q = np.abs(p - c) - b + r
    return length(np.maximum(q, 0)) + np.minimum(np.max(q, -1), 0) - r
def sd_cyl_x(p, c, rad, hl, rr=0.8):
    q = p - c
    d = np.stack([np.sqrt(q[:, 1]**2 + q[:, 2]**2) - rad + rr, np.abs(q[:, 0]) - hl + rr], -1)
    return np.minimum(np.max(d, -1), 0) + length(np.maximum(d, 0)) - rr
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)

V = lambda *a: np.array(a, dtype=np.float32)
BODY_C, BODY_R = V(0, 68, 0), V(49, 52, 40)
# braço acenando
SH_R, EL_R, HA_R = V(40, 52, 2), V(58, 74, 6), V(63, 94, 8)
SH_L, HA_L = V(-40, 46, 2), V(-54, 22, 6)

def to_local(p):
    q = p.copy()
    x, z = p[:, 0], p[:, 2]
    q[:, 0] = x * cy_ - z * sy_
    q[:, 2] = x * sy_ + z * cy_
    return q

def scene(p, want_mat=False):
    q = to_local(p)
    ds = []
    body = sd_ellipsoid(q, BODY_C, BODY_R)
    arms = np.minimum(sd_capsule(q, SH_R, EL_R, 4.6), sd_capsule(q, EL_R, HA_R, 4.6))
    arms = np.minimum(arms, sd_capsule(q, SH_L, HA_L, 4.6))
    hands = np.minimum(sd_ellipsoid(q, HA_R, V(7.5, 8.5, 7)), sd_ellipsoid(q, HA_L + V(-1, -3, 0), V(7, 7.5, 7)))
    legs = np.minimum(sd_capsule(q, V(-16, 6, 0), V(-16, 24, 0), 7.5), sd_capsule(q, V(16, 6, 0), V(16, 24, 0), 7.5))
    teal = smin(body, smin(arms, hands, 2.5), 5.0)
    teal = smin(teal, legs, 3.0)
    suit = np.maximum(sd_ellipsoid(q, BODY_C, BODY_R + 1.1), q[:, 1] - 54 + 0.0012 * q[:, 0] ** 2)
    boots = np.minimum(sd_rbox(q, V(-16, 5, 2.5), V(11, 5.5, 12.5), 5), sd_rbox(q, V(16, 5, 2.5), V(11, 5.5, 12.5), 5))
    ears = np.minimum(sd_cyl_x(q, V(-46.5, 88, 0), 7.5, 3.5), sd_cyl_x(q, V(46.5, 88, 0), 7.5, 3.5))
    eglow = np.minimum(sd_cyl_x(q, V(-49.5, 88, 0), 4, 1.6, 0.6), sd_cyl_x(q, V(49.5, 88, 0), 4, 1.6, 0.6))
    stem = np.minimum(sd_capsule(q, V(0, 116, 0), V(0.5, 128, 0), 1.8), sd_capsule(q, V(0.5, 128, 0), V(4, 138, 0), 1.8))
    abase = sd_ellipsoid(q, V(0, 119.5, 0), V(5.5, 2.4, 5.5))
    aball = sd_sphere(q, V(4.6, 143, 0), 6.5)
    eyes = np.minimum(sd_ellipsoid(q, V(-16, 87, 30), V(11, 14, 8.5)), sd_ellipsoid(q, V(16, 87, 30), V(11, 14, 8.5)))
    pupils = np.minimum(sd_ellipsoid(q, V(-14.5, 84.5, 37.2), V(4.8, 5.6, 2.6)), sd_ellipsoid(q, V(17.5, 84.5, 37.2), V(4.8, 5.6, 2.6)))
    spark = np.minimum(sd_sphere(q, V(-12.6, 87.6, 39.2), 1.5), sd_sphere(q, V(19.4, 87.6, 39.2), 1.5))
    brows = np.minimum(sd_capsule(q, V(-23, 106, 23), V(-10, 108, 27.5), 1.3), sd_capsule(q, V(10, 108, 27.5), V(23, 106, 23), 1.3))
    buckle = sd_rbox(q, V(0, 28.5, 26.5), V(9.5, 5.8, 3), 2.2)
    trans = sd_sphere(q, V(0, -50, 0), 1.0)
    ground = p[:, 1] + 0.0
    ds = [teal, suit, boots, ears, eglow, stem, abase, aball, eyes, pupils, spark, brows, buckle, trans, ground]
    D = np.stack(ds, -1)
    d = np.min(D, -1)
    if want_mat:
        return d, np.argmin(D, -1), q
    return d

MAT = ['teal', 'suit', 'boots', 'ears', 'eglow', 'stem', 'abase', 'aball', 'eyes', 'pupils', 'spark', 'brows', 'buckle', 'trans', 'ground']

def sd_star5_2d(px, py, r, rf):
    k1 = np.array([0.809016994375, -0.587785252292]); k2 = np.array([-k1[0], k1[1]])
    px = np.abs(px)
    dt = px * k1[0] + py * k1[1]; m = 2 * np.maximum(dt, 0); px, py = px - m * k1[0], py - m * k1[1]
    dt = px * k2[0] + py * k2[1]; m = 2 * np.maximum(dt, 0); px, py = px - m * k2[0], py - m * k2[1]
    px = np.abs(px); py = py - r
    ba = np.array([-k1[1] * rf - 0.0, k1[0] * rf - 1.0])  # (rf*(-k1.y,k1.x)) - (0,1)
    ba = np.array([rf * -k1[1], rf * k1[0] - 1.0])
    h = np.clip((px * ba[0] + py * ba[1]) / np.dot(ba, ba), 0, r)
    dx, dy = px - ba[0] * h, py - ba[1] * h
    return np.sqrt(dx * dx + dy * dy) * np.sign(py * ba[0] - px * ba[1])

def albedo(mat, q):
    n = len(mat)
    col = np.zeros((n, 3), np.float32)
    spec = np.full(n, 0.25, np.float32); emis = np.zeros((n, 3), np.float32)
    for i, name in enumerate(MAT):
        m = mat == i
        if not m.any(): continue
        if name in ('teal', 'eglow', 'stem', 'aball', 'eyes', 'pupils', 'spark', 'brows', 'buckle', 'ground'):
            pass
        base = {'teal': C['teal'], 'suit': C['silver'], 'boots': C['silver'], 'ears': C['silver'], 'eglow': C['glow'],
                'stem': C['teal_d'], 'abase': C['silver'], 'aball': C['yellow'], 'eyes': C['white'], 'pupils': C['pupil'],
                'spark': C['white'], 'brows': C['brow'], 'buckle': C['yellow'], 'trans': C['silver'], 'ground': C['grass']}[name]
        col[m] = base
        spec[m] = {'teal': 0.35, 'suit': 0.7, 'boots': 0.7, 'ears': 0.8, 'abase': 0.8, 'aball': 0.6, 'eyes': 0.6,
                   'pupils': 0.9, 'buckle': 0.7, 'trans': 0.8, 'ground': 0.03}.get(name, 0.3)
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    # rosto pintado no corpo
    tm = mat == 0
    front = z > 5
    my = (y < 71) & (((x / 11.5) ** 2 + ((y - 71) / 18.5) ** 2) < 1) & front
    col[tm & my] = C['mouth']; spec[tm & my] = 0.5
    tongue = my & (((x / 6.5) ** 2 + ((y - 57) / 4.5) ** 2) < 1)
    col[tm & tongue] = C['tongue']
    teeth = my & (y > 66.8)
    col[tm & teeth] = C['white']
    for sx in (-33, 33):
        ck = front & ((((x - sx) / 7) ** 2 + ((y - 70) / 4.2) ** 2) < 1) & ~my
        col[tm & ck] = col[tm & ck] * 0.25 + C['cheek'] * 0.75
    for sx, syy, r in [(-28, 112, 4.5), (-36, 100, 3), (-20, 118, 2.6), (30, 110, 3.6), (36, 100, 2.4)]:
        sp = (((x - sx) ** 2 + (y - syy) ** 2) < r * r) & (z > 0)
        col[tm & sp] = C['spot']
    # macacão: cinto e estrela
    sm = mat == 1
    belt = (y > 25) & (y < 32.5)
    col[sm & belt] = C['silver_d']; spec[sm & belt] = 0.4
    star = (sd_star5_2d(x, y - 43.5, 6.6, 0.45) < 0) & (z > 10)
    col[sm & star] = C['yellow']
    bm = mat == 12
    bstar = (sd_star5_2d(x, y - 28.3, 4.2, 0.45) < 0) & (z > 27)
    col[bm & bstar] = C['white']
    # brilhos
    emis[mat == 4] = C['glow'] * 0.9
    emis[mat == 7] = C['yellow'] * 0.25
    emis[mat == 10] = 1.0
    emis[mat == 8] = 0.06
    tg = (mat == 13) & (z > 23.5)
    col[tg] = C['glow']; emis[tg] = C['glow'] * 0.8
    return col, spec, emis

def normal(p):
    e = 0.05
    ex, ey, ez = V(e, 0, 0), V(0, e, 0), V(0, 0, e)
    n = np.stack([scene(p + ex) - scene(p - ex), scene(p + ey) - scene(p - ey), scene(p + ez) - scene(p - ez)], -1)
    return n / np.maximum(length(n)[:, None], 1e-6)

def soft_shadow(p, l, k=10.0):
    res = np.ones(len(p), np.float32); t = np.full(len(p), 0.6, np.float32)
    for _ in range(48):
        h = scene(p + l * t[:, None])
        res = np.minimum(res, k * h / t)
        t += np.clip(h, 0.3, 12.0)
    return np.clip(res, 0, 1)

def ao(p, n):
    occ = np.zeros(len(p), np.float32); sca = 1.0
    for i in range(5):
        h = 0.8 + 4.5 * i
        d = scene(p + n * h)
        occ += (h - d) * sca; sca *= 0.75
    return np.clip(1 - 0.045 * occ, 0, 1)

def sky(rd):
    t = np.clip(rd[:, 1] * 2.2 + 0.25, 0, 1)[:, None]
    top, hor = lin(hx('6EC6EE')), lin(hx('E9F7F2'))
    col = hor * (1 - t) + top * t
    # nuvens suaves
    u = np.arctan2(rd[:, 0], -rd[:, 2]); v = rd[:, 1]
    cl = np.zeros(len(rd), np.float32)
    for cu, cv, r in [(-0.30, 0.20, 0.07), (-0.23, 0.22, 0.055), (-0.36, 0.21, 0.05), (0.26, 0.26, 0.06), (0.32, 0.245, 0.05), (0.21, 0.24, 0.045)]:
        cl = np.maximum(cl, np.clip(1 - ((u - cu) ** 2 + ((v - cv) * 1.6) ** 2) / (r * r), 0, 1))
    col = col * (1 - cl[:, None] ** 0.5 * 0.9) + cl[:, None] ** 0.5 * 0.9
    return col

def render():
    ro = V(0, 82, 300)
    ta = V(0, 70, 0)
    fw = (ta - ro); fw /= np.linalg.norm(fw)
    rt = np.cross(fw, V(0, 1, 0)); rt /= np.linalg.norm(rt)
    up = np.cross(rt, fw)
    fov = math.tan(math.radians(20))
    img = np.zeros((RH, RW, 3), np.float32)
    L1 = V(-0.55, 0.75, 0.55); L1 /= np.linalg.norm(L1)
    L2 = V(0.7, 0.3, 0.4); L2 /= np.linalg.norm(L2)
    L3 = V(0.2, 0.4, -0.9); L3 /= np.linalg.norm(L3)
    rows = 60
    for r0 in range(0, RH, rows):
        r1 = min(RH, r0 + rows)
        yy, xx = np.mgrid[r0:r1, 0:RW]
        px = (2 * (xx + 0.5) / RW - 1) * fov * (RW / RH)
        py = (1 - 2 * (yy + 0.5) / RH) * fov
        rd = fw[None, :] + px.reshape(-1, 1) * rt[None, :] + py.reshape(-1, 1) * up[None, :]
        rd /= length(rd)[:, None]
        n = len(rd)
        t = np.full(n, 150.0, np.float32)
        alive = np.ones(n, bool); hit = np.zeros(n, bool)
        for _ in range(160):
            idx = np.nonzero(alive)[0]
            if len(idx) == 0: break
            pp = ro + rd[idx] * t[idx, None]
            d = scene(pp)
            t[idx] += d * 0.9
            h = d < 0.01 + 0.0006 * t[idx]
            hit[idx[h]] = True
            far = t[idx] > 900
            alive[idx[h | far]] = False
        col = sky(rd)
        hi = np.nonzero(hit)[0]
        if len(hi):
            p = ro + rd[hi] * t[hi, None]
            _, mat, q = scene(p, True)
            nrm = normal(p)
            alb, spec, emis = albedo(mat, q)
            pe = p + nrm * 0.25
            sh = soft_shadow(pe, L1)
            occ = ao(p, nrm)
            v = -rd[hi]
            isg = mat == 14
            wrap = np.where(isg, 0.0, 0.35)
            dif1 = np.clip((np.sum(nrm * L1, -1) + wrap) / (1 + wrap), 0, 1) * sh
            dif2 = np.clip(np.sum(nrm * L2, -1), 0, 1)
            rim = np.clip(np.sum(nrm * L3, -1), 0, 1)
            hemi = 0.5 + 0.5 * nrm[:, 1]
            hv = L1 + v; hv /= length(hv)[:, None]
            sp = np.clip(np.sum(nrm * hv, -1), 0, 1) ** 48 * sh
            fres = (1 - np.clip(np.sum(nrm * v, -1), 0, 1)) ** 3
            sun = lin(hx('FFF1D6')) * 1.25
            skyc = lin(hx('BFE6FF'))
            c = alb * (sun * dif1[:, None] + lin(hx('CFE8FF')) * 0.30 * dif2[:, None]
                       + (skyc * hemi[:, None] * 0.38 + lin(hx('A8D88A')) * (1 - hemi[:, None]) * 0.12) * occ[:, None])
            c += (sun * sp[:, None] * spec[:, None]) * 1.4
            c += (fres * rim * 0.55 + fres * 0.12)[:, None] * skyc * (~isg)[:, None]
            # sombra levemente quente na pele
            c += alb * lin(hx('FF9E80')) * 0.05 * (1 - sh)[:, None] * (mat == 0)[:, None]
            c += emis
            # chão: desvanece com a distância
            if isg.any():
                gd = np.clip((t[hi] - 300) / 500, 0, 1)
                c[isg] = c[isg] * (1 - gd[isg, None]) + lin(hx('CDEBB0')) * gd[isg, None]
            col[hi] = c
        img[r0:r1] = col.reshape(r1 - r0, RW, 3)
        print(f'{r1}/{RH}', flush=True)
    # tone map + gamma
    img = img * 1.05
    img = (img * (2.51 * img + 0.03)) / (img * (2.43 * img + 0.59) + 0.14)
    img = np.clip(img, 0, 1) ** (1 / 2.2)
    return Image.fromarray((img * 255).astype(np.uint8))

t0 = time.time()
im = render()
if SSF > 1:
    im = im.resize((W, H), Image.LANCZOS)
im.save(OUT)
print('ok', round(time.time() - t0, 1), 's')
