"""Illustrations vectorielles (Pillow) pour les articles. Chaque motif dessine une scène 1000x560."""
from PIL import Image, ImageDraw, ImageFont
import math, random

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SS = 2  # suréchantillonnage
W, H = 1000, 560

def _mix(c, k):  # k>0 éclaircit vers blanc, k<0 assombrit
    r, g, b = [int(c[i:i+2], 16) for i in (1, 3, 5)]
    if k >= 0: r, g, b = [int(v + (255 - v) * k) for v in (r, g, b)]
    else: r, g, b = [int(v * (1 + k)) for v in (r, g, b)]
    return (r, g, b)

class P:
    def __init__(s, base):
        s.im = Image.new("RGBA", (W*SS, H*SS), (0, 0, 0, 0)); s.d = ImageDraw.Draw(s.im)
        s.c = base
        s.white = (255, 255, 255, 255); s.soft = (255, 255, 255, 120); s.light = _mix(base, .75) + (255,)
        s.mid = _mix(base, .45) + (255,); s.dark = _mix(base, -.55) + (255,)
    def _s(s, v): return [x*SS for x in v]
    def rect(s, x0, y0, x1, y1, f, r=0):
        if r: s.d.rounded_rectangle(s._s([x0, y0, x1, y1]), radius=r*SS, fill=f)
        else: s.d.rectangle(s._s([x0, y0, x1, y1]), fill=f)
    def ell(s, x0, y0, x1, y1, f): s.d.ellipse(s._s([x0, y0, x1, y1]), fill=f)
    def poly(s, pts, f): s.d.polygon([(x*SS, y*SS) for x, y in pts], fill=f)
    def line(s, pts, f, w=4): s.d.line([(x*SS, y*SS) for x, y in pts], fill=f, width=w*SS, joint="curve")
    def text(s, xy, t, size, f, anchor="mm"):
        s.d.text((xy[0]*SS, xy[1]*SS), t, font=ImageFont.truetype(FONT_B, size*SS), fill=f, anchor=anchor)
    def out(s): return s.im.resize((W, H), Image.LANCZOS)

def person(p, x, ground, h, body, head=None, sign=None, arm_up=False):
    head = head or p.white
    hr = h*0.13
    p.rect(x-h*0.14, ground-h*0.62, x+h*0.14, ground, body, r=h*0.08)
    p.ell(x-hr, ground-h*0.62-hr*2.1, x+hr, ground-h*0.62-hr*0.1, head)
    if arm_up: p.line([(x+h*0.12, ground-h*0.55), (x+h*0.28, ground-h*0.95)], head, 5)
    if sign:
        p.line([(x+h*0.28, ground-h*0.95), (x+h*0.28, ground-h*0.62)], p.white, 4)
        p.rect(x+h*0.28-h*0.3, ground-h*1.25, x+h*0.28+h*0.3, ground-h*0.92, p.white, r=3)
        p.rect(x+h*0.28-h*0.22, ground-h*1.17, x+h*0.28+h*0.22, ground-h*1.12, p.mid)
        p.rect(x+h*0.28-h*0.22, ground-h*1.07, x+h*0.28+h*0.1, ground-h*1.02, p.mid)

def building(p, x, ground, w, h, f, windows=True, wf=None):
    p.rect(x, ground-h, x+w, ground, f)
    if windows:
        wf = wf or p.mid
        cols = max(2, int(w//34)); rows = max(2, int(h//46))
        for i in range(cols):
            for j in range(rows):
                wx = x + 12 + i*(w-24)/cols; wy = ground-h+14+j*(h-28)/rows
                p.rect(wx, wy, wx+(w-24)/cols-10, wy+(h-28)/rows-14, wf)

def scene(motif, color):
    p = P(color)
    g = 500
    p.rect(0, g, W, H, p.dark)
    if motif == "crowd":
        building(p, 120, g, 190, 300, p.mid, wf=p.light)
        p.poly([(70, g-300), (215, g-380), (360, g-300)], p.mid)
        building(p, 640, g, 240, 240, p.mid, wf=p.light)
        p.rect(470, g-420, 500, g, p.soft)  # tour
        p.poly([(455, g-420), (485, g-480), (515, g-420)], p.soft)
        xs = [90, 170, 250, 330, 410, 490, 570, 650, 730, 810, 890]
        random.seed(3)
        for i, x in enumerate(xs):
            person(p, x, g+30, random.randint(150, 190), [p.white, p.light, p.mid][i % 3] , sign=(i % 3 == 1), arm_up=(i % 4 == 0))
    elif motif == "tram":
        for x in range(0, W, 170):
            building(p, x, g-40, 150, 150 + (x*7 % 120), p.mid, wf=p.light)
        p.rect(0, g-40, W, g, p.dark)
        p.line([(0, g+12), (W, g+12)], p.white, 5); p.line([(0, g+30), (W, g+30)], p.soft, 3)
        p.line([(0, 130), (W, 130)], p.white, 3)
        for x in (180, 520, 860): p.line([(x, 130), (x, g-30)], p.white, 6)
        p.rect(110, 215, 900, 440, p.white, r=40)
        p.rect(110, 380, 900, 410, _mix(color, -.15)+(255,))
        for i in range(8): p.rect(150+i*92, 250, 150+i*92+66, 340, p.dark, r=10)
        p.rect(820, 250, 880, 340, p.dark, r=10)
        p.poly([(480, 215), (520, 150), (560, 215)], p.white); p.line([(520, 150), (520, 130)], p.white, 4)
        p.ell(170, 425, 230, 485, p.dark); p.ell(780, 425, 840, 485, p.dark)
    elif motif == "chart":
        p.line([(120, 90), (120, 470), (900, 470)], p.white, 6)
        vals = [330, 300, 305, 270, 255, 235, 215]
        for i, v in enumerate(vals):
            x = 170 + i*105
            p.rect(x, 470-v, x+70, 470, p.light if i < len(vals)-1 else p.white, r=6)
        pts = [(205+i*105, 470-v-30) for i, v in enumerate(vals)]
        p.line(pts, p.white, 6)
        for x, y in pts: p.ell(x-9, y-9, x+9, y+9, p.white)
        ax, ay = pts[-1]
        p.poly([(ax+30, ay+24), (ax+10, ay-6), (ax+50, ay-2)], p.white)
        p.text((690, 110), "4,8 %", 96, p.white)
    elif motif == "parliament":
        p.rect(130, g-30, 870, g, p.mid)
        p.rect(170, g-60, 830, g-30, p.light)
        p.rect(210, g-90, 790, g-60, p.mid)
        p.rect(240, g-330, 760, g-90, p.white)
        for i in range(8):
            x = 270 + i*66; p.rect(x, g-320, x+34, g-100, p.light)
        p.poly([(210, g-330), (500, g-460), (790, g-330)], p.white)
        p.ell(470, g-400, 530, g-340, p.mid)
        p.line([(500, g-460), (500, g-535)], p.white, 5); p.rect(502, g-535, 565, g-505, p.light)
    elif motif == "car":
        p.rect(90, g-30, 910, g, p.mid)
        p.poly([(250, 300), (340, 215), (610, 215), (730, 300)], p.white)
        p.poly([(300, 295), (360, 235), (470, 235), (470, 295)], p.dark); p.poly([(490, 295), (490, 235), (600, 235), (670, 295)], p.dark)
        p.rect(150, 295, 850, 400, p.white, r=40)
        p.rect(150, 340, 850, 372, p.light)
        p.ell(240, 360, 360, 480, p.dark); p.ell(640, 360, 760, 480, p.dark)
        p.ell(275, 395, 325, 445, p.light); p.ell(675, 395, 725, 445, p.light)
        p.ell(780, 110, 900, 230, p.white); p.text((840, 170), "CHF", 36, p.dark)
    elif motif == "halloween":
        p.ell(250, 170, 750, 500, _mix("#f59e0b", 0)+(255,))
        p.ell(330, 150, 470, 500, _mix("#f59e0b", -.12)+(255,)); p.ell(530, 150, 670, 500, _mix("#f59e0b", -.12)+(255,))
        p.rect(480, 110, 520, 180, _mix("#166534", 0)+(255,), r=8)
        p.poly([(330, 270), (400, 270), (365, 215)], p.dark); p.poly([(600, 270), (670, 270), (635, 215)], p.dark)
        p.poly([(480, 330), (520, 330), (500, 305)], p.dark)
        p.poly([(340, 380), (400, 420), (450, 395), (500, 430), (550, 395), (600, 420), (660, 380), (640, 450), (500, 470), (360, 450)], p.dark)
        # téléphone / réseaux
        p.rect(820, 120, 940, 360, p.white, r=18); p.rect(832, 145, 928, 330, p.dark, r=6); p.ell(868, 340, 892, 356, p.mid)
        for r_ in (30, 55, 80): p.d.arc(s_ := [ (880-r_)*SS, (80-r_)*SS, (880+r_)*SS, (80+r_)*SS ], 210, 330, fill=p.white, width=5*SS)
    elif motif == "press":
        p.rect(170, 120, 640, 470, p.white, r=10)
        p.rect(200, 150, 610, 200, p.dark, r=4)
        for i in range(7): p.rect(200, 225+i*32, 400 if i % 2 else 420, 243+i*32, p.mid)
        p.rect(430, 225, 610, 345, p.light); p.rect(430, 360, 610, 378, p.mid); p.rect(430, 392, 580, 410, p.mid)
        p.rect(660, 200, 880, 470, p.light, r=10); p.rect(685, 230, 855, 262, p.dark, r=3)
        for i in range(5): p.rect(685, 285+i*32, 855 if i % 2 else 800, 303+i*32, p.mid)
        p.ell(730, 60, 910, 240, p.white); p.d.ellipse(s_ if False else [750*SS, 80*SS, 890*SS, 220*SS], fill=p.dark)
        p.line([(820, 150), (820, 105)], p.white, 7); p.line([(820, 150), (855, 170)], p.white, 7)
        p.text((820, 275), "1 h", 0, p.white) if False else None
    elif motif == "communes":
        building(p, 130, g, 300, 220, p.white, windows=False)
        p.poly([(110, g-220), (280, g-320), (450, g-220)], p.light)
        for i in range(4): p.rect(160+i*66, g-200, 190+i*66, g-20, p.mid)
        p.rect(255, g-120, 305, g, p.dark)
        p.rect(268, g-400, 292, g-320, p.light); p.rect(292, g-400, 340, g-375, p.white)
        for i, v in enumerate([120, 180, 250, 330]):
            p.rect(540+i*85, g-v, 540+i*85+60, g, p.light if i < 3 else p.white, r=5)
        for k in range(3):
            p.ell(780, 120+k*0, 900, 150, p.soft) if False else None
        for k in range(4): p.ell(760, 110+k*0, 760, 110, p.white) if False else None
        for k in range(4):
            p.ell(790, 120-k*0, 910, 160, p.white) if False else None
        # pièces
        for k in range(4):
            y = 150 - k*0
        for k, (cx, cy) in enumerate([(840, 130), (840, 100), (840, 70), (790, 130)]):
            p.ell(cx-45, cy-18, cx+45, cy+18, p.white); p.ell(cx-45, cy-10, cx+45, cy+26, p.light) if False else None
    elif motif == "village":
        for x, hh in ((60, 150), (850, 190)):
            p.rect(x+40, g-hh, x+55, g, p.mid); p.ell(x, g-hh-90, x+95, g-hh+20, p.light)
        p.rect(300, g-260, 700, g, p.white)
        p.poly([(270, g-260), (500, g-350), (730, g-260)], p.light)
        p.rect(470, g-470, 530, g-350, p.white); p.poly([(460, g-470), (500, g-520), (540, g-470)], p.light)
        p.ell(480, g-440, 520, g-400, p.dark)
        for i in range(3): p.rect(330+i*75, g-210, 380+i*75, g-120, p.dark, r=4)
        p.rect(560, g-200, 660, g, p.mid); p.rect(575, g-185, 645, g-60, p.dark)
        p.rect(540, g-215, 680, g-190, p.light)
        p.rect(150, g-8, 850, g, p.light)
        for x in (180, 260, 740, 820): person(p, x, g+30, 110, p.light)
    elif motif == "museum":
        p.rect(130, g-30, 870, g, p.mid)
        p.rect(160, g-290, 840, g-30, p.white)
        p.poly([(130, g-290), (500, g-440), (870, g-290)], p.white)
        p.ell(465, g-380, 535, g-310, p.mid)
        for i in range(7): p.rect(200+i*90, g-270, 240+i*90, g-50, p.light)
        p.rect(100, 60, 220, 180, p.white); p.rect(112, 72, 208, 168, p.mid)
        p.ell(740, 60, 900, 160, p.white); p.ell(780, 85, 800, 105, p.dark); p.ell(820, 75, 840, 95, p.dark); p.ell(850, 100, 870, 120, p.dark)
    return p.out()
