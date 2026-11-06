#!/usr/bin/env python3
"""Générateur de site journal : articles.json -> site/ (HTML + visuels sociaux)."""
import json, html, textwrap, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- RÉGLAGES ----------
SITE_NAME = "15 minutes"
TAGLINE = "L'essentiel de l'actualité romande en 15 minutes"
BASE_URL = "https://bookingdcevents-collab.github.io/15minutes-journal"                            # ex: https://vaudquotidien.ch (sert aux balises Facebook)
ADSENSE_CLIENT = ""                      # ex: ca-pub-1234567890123456 (après validation Google)
# Codes d'un autre réseau (ex. Adsterra) : coller le code HTML fourni dans l'emplacement voulu.
# Ne pas mélanger avec AdSense sur la même page.
def _adsterra(key, w, h, minw=0, maxw=99999):
    # Charge la pub uniquement si l'écran est assez large (évite de charger une pub cachée)
    return ("<script>(function(){if(window.innerWidth<%d||window.innerWidth>%d)return;"
            "window.atOptions={'key':'%s','format':'iframe','height':%d,'width':%d,'params':{}};"
            "document.write('<scr'+'ipt src=\"https://bauval.org/22/%s\"></scr'+'ipt>');})();</script>") % (minw, maxw, key, h, w, key)

AD_CUSTOM = {
    "top": _adsterra("81f0f1093be39cfd364923e057257562", 728, 90, 768) + _adsterra("5083ba51c137481c711eaa6d0fabb937", 320, 50, 0, 767),  # 728x90 ordinateur/tablette, 320x50 mobile
    "inline": _adsterra("f4bffaebe314ea08e3a2cdb7e970e9d6", 300, 250, 0),    # 300x250 partout
    "side": _adsterra("ffe5be9075f8ba72055da2924ee871c4", 160, 600, 861),    # 160x600 colonne latérale (visible desktop)
}
HEAD_SNIPPET = ""                        # code à placer dans <head>, si le réseau le demande
SHOW_AD_PLACEHOLDERS = False   # True = affiche des cadres "Espace publicitaire" (maquette uniquement)
EDITEUR = {"nom": "À compléter (nom / raison sociale)", "adresse": "À compléter", "email": "contact@exemple.ch"}
AD_SLOTS = {"top": "", "inline": "", "side": ""}   # identifiants de blocs AdSense
CATS = {"Mobilité": "#1f6feb", "Région": "#c2410c", "Sport": "#15803d",
        "Économie": "#7c3aed", "Société": "#be123c", "Culture": "#0e7490"}
# ------------------------------

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_S = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
esc = html.escape

def fr_date(iso):
    m = ["janvier","février","mars","avril","mai","juin","juillet","août","septembre","octobre","novembre","décembre"]
    y, mo, d = iso.split("-")
    return f"{int(d)} {m[int(mo)-1]} {y}"

def ad(slot):
    if AD_CUSTOM.get(slot):
        return f'<div class="ad ad-{slot}" style="background:none;border:0;min-height:0">{AD_CUSTOM[slot]}</div>'
    if ADSENSE_CLIENT and AD_SLOTS.get(slot):
        return (f'<div class="ad ad-{slot}"><ins class="adsbygoogle" style="display:block" '
                f'data-ad-client="{ADSENSE_CLIENT}" data-ad-slot="{AD_SLOTS[slot]}" '
                f'data-ad-format="auto" data-full-width-responsive="true"></ins>'
                f'<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});</script></div>')
    if not SHOW_AD_PLACEHOLDERS:
        return ""
    return f'<div class="ad ad-{slot}"><span>Espace publicitaire</span></div>'

def head(title, desc, rel, og_img=None, url=None):
    adsense = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>'
               if ADSENSE_CLIENT else "")
    og = ""
    if og_img:
        full = f"{BASE_URL}/{og_img}" if BASE_URL else og_img
        og = (f'<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}">'
              f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{esc(full)}">'
              f'<meta property="og:site_name" content="{esc(SITE_NAME)}"><meta name="twitter:card" content="summary_large_image">')
    return (f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'{HEAD_SNIPPET}<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">{og}'
            f'<link rel="icon" type="image/svg+xml" href="{rel}logo.svg"><link rel="stylesheet" href="{rel}style.css">{adsense}</head><body>')

RED = "#d7261e"
def logo_svg(size=44, ink="#16181d"):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" aria-hidden="true">'
            f'<circle cx="50" cy="50" r="44" fill="none" stroke="{ink}" stroke-width="9"/>'
            f'<path d="M50 50 L50 16 A34 34 0 0 1 84 50 Z" fill="{RED}"/>'
            f'<circle cx="50" cy="50" r="5" fill="{ink}"/></svg>')

def logo_png(path, size=1024):
    """Photo de profil carrée pour Facebook/Instagram."""
    img = Image.new("RGB", (size, size), "white"); d = ImageDraw.Draw(img)
    draw_clock(d, size*0.5, size*0.40, size*0.30, "#16181d")
    f = ImageFont.truetype(FONT_B, int(size*0.15))
    t = "15 minutes"; w = d.textlength(t, font=f)
    d.text(((size-w)/2, size*0.70), t, font=f, fill="#16181d")
    img.save(path)

def draw_clock(d, cx, cy, r, ink, ring=None):
    ring = ring or max(4, int(r*0.2))
    d.ellipse([cx-r, cy-r, cx+r, cy+r], outline=ink, width=ring)
    ir = r*0.76
    d.pieslice([cx-ir, cy-ir, cx+ir, cy+ir], start=-90, end=0, fill=RED)
    c = r*0.1; d.ellipse([cx-c, cy-c, cx+c, cy+c], fill=ink)

def header(rel):
    return (f'<header class="top"><a class="logo" href="{rel}index.html">{logo_svg(40)}<span>{esc(SITE_NAME)}</span></a>'
            f'<span class="tag">{esc(TAGLINE)}</span></header>')

CONSENT = """<div id="cb" style="display:none;position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#111;color:#fff;padding:14px 16px;font:14px/1.4 system-ui,sans-serif;box-shadow:0 -2px 12px rgba(0,0,0,.3)"><div style="max-width:900px;margin:auto;display:flex;gap:12px;flex-wrap:wrap;align-items:center"><span style="flex:1 1 300px">Nous utilisons des cookies publicitaires (réseau Adsterra) pour financer ce site gratuit. Vous pouvez les accepter ou les refuser. <a href="/15minutes-journal/confidentialite.html" style="color:#9cf">En savoir plus</a></span><button id="cr" style="padding:8px 16px;border:1px solid #fff;background:none;color:#fff;border-radius:6px;cursor:pointer">Refuser</button><button id="ca" style="padding:8px 16px;border:0;background:#fff;color:#111;border-radius:6px;cursor:pointer;font-weight:600">Accepter</button></div></div><script>function rc15(){try{localStorage.removeItem('c15')}catch(e){}location.reload();return false}(function(){var v=null;try{v=localStorage.getItem('c15')}catch(e){}if(v===null){var b=document.getElementById('cb');b.style.display='block';document.getElementById('ca').onclick=function(){try{localStorage.setItem('c15','1')}catch(e){}location.reload()};document.getElementById('cr').onclick=function(){try{localStorage.setItem('c15','0')}catch(e){}b.style.display='none'}}})();</script>"""

def footer(rel=""):
    return (f'<footer><p>© {esc(SITE_NAME)}. Contenus rédigés de façon originale à partir de sources citées.</p>'
            f'<p><a href="{rel}a-propos.html">À propos</a> · <a href="{rel}contact.html">Contact</a> · <a href="{rel}mentions-legales.html">Mentions légales</a> · <a href="{rel}confidentialite.html">Confidentialité et cookies</a></p></footer></body></html>')

def wrap(text, font, width, draw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= width: cur = t
        else: lines.append(cur); cur = w
    return lines + [cur]

def social_image(a, path):
    W, H = 1080, 1350
    c = CATS.get(a["category"], "#334155")
    img = Image.new("RGB", (W, H), c)
    d = ImageDraw.Draw(img)
    r, g, b = [int(c[i:i+2], 16) for i in (1, 3, 5)]
    for y in range(H):  # dégradé vers le sombre
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(r*(1-.65*k)), int(g*(1-.65*k)), int(b*(1-.65*k))))
    d.ellipse([60, 60, 140, 140], fill="white"); draw_clock(d, 100, 100, 36, "#16181d", ring=8)
    d.text((160, 78), SITE_NAME, font=ImageFont.truetype(FONT_B, 52), fill="white")
    tag = ImageFont.truetype(FONT_S, 34)
    tw = d.textlength(a["category"].upper(), font=tag)
    d.rounded_rectangle([60, 430, 60 + tw + 50, 495], radius=8, fill="white")
    d.text((85, 441), a["category"].upper(), font=tag, fill=c)
    size = 76
    while True:
        f = ImageFont.truetype(FONT_B, size)
        lines = wrap(a["title"], f, W - 120, d)
        if len(lines) * (size + 14) <= 640 or size <= 48: break
        size -= 4
    y = 540
    for ln in lines:
        d.text((60, y), ln, font=f, fill="white"); y += size + 14
    d.text((60, H - 110), "Lire l'article  →  lien en bio / en commentaire", font=ImageFont.truetype(FONT_S, 32), fill="white")
    img.save(path, optimize=True)

CSS = """
*{box-sizing:border-box}body{margin:0;font:18px/1.65 Georgia,'Times New Roman',serif;color:#16181d;background:#f6f5f1}
a{color:inherit}.top{background:#fff;border-bottom:3px solid #16181d;padding:18px 24px;display:flex;gap:18px;align-items:baseline;flex-wrap:wrap}
.logo{font:800 32px/1 'DejaVu Serif',Georgia,serif;text-decoration:none;letter-spacing:-.5px;display:flex;align-items:center;gap:10px}.tag{font:14px system-ui,sans-serif;color:#667}
main{max-width:1060px;margin:0 auto;padding:24px;display:grid;grid-template-columns:1fr 300px;gap:32px}
@media(max-width:860px){main{grid-template-columns:1fr}}
.cat{font:700 12px system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#fff;padding:3px 8px;border-radius:3px;display:inline-block}
.card{background:#fff;border:1px solid #e3e1da;border-radius:8px;overflow:hidden;margin-bottom:20px;display:block;text-decoration:none}
.card img{width:100%;display:block;aspect-ratio:16/9;object-fit:cover;object-position:top}
.card div{padding:16px 18px}.card h2{margin:8px 0 6px;font-size:23px;line-height:1.25}.card p{margin:0;color:#555;font-size:16px}
.meta{font:13px system-ui,sans-serif;color:#778}article h1{font-size:36px;line-height:1.2;margin:10px 0}
.lead{font-size:21px;color:#333}.hero{width:100%;border-radius:8px;margin:14px 0}
.sources{border-top:1px solid #ddd;margin-top:28px;padding-top:12px;font:14px system-ui,sans-serif}
.demo{background:#fff3cd;border:1px solid #e6cf7a;padding:8px 12px;border-radius:6px;font:14px system-ui,sans-serif;margin-bottom:12px}
.ad{background:repeating-linear-gradient(45deg,#f0eee8,#f0eee8 10px,#e9e6de 10px,#e9e6de 20px);border:1px dashed #b9b4a6;color:#8a8473;font:12px system-ui,sans-serif;display:flex;align-items:center;justify-content:center;margin:22px 0;text-transform:uppercase;letter-spacing:.1em}
.ad-top{min-height:90px}.ad-inline{min-height:250px}.ad-side{min-height:600px}@media(max-width:860px){.ad-side{display:none}}@media(max-width:767px){.ad-top{min-height:50px}}
aside .box{background:#fff;border:1px solid #e3e1da;border-radius:8px;padding:14px 16px;font:15px system-ui,sans-serif}
footer{text-align:center;font:13px system-ui,sans-serif;color:#667;padding:30px 20px}
"""

def legal_pages(arts):
    e = EDITEUR
    pages = {
     "a-propos": ("À propos", f"<p><strong>{esc(SITE_NAME)}</strong> propose chaque jour l'essentiel de l'actualité romande, présenté en lecture courte.</p>"
        "<p>Nos articles sont rédigés de façon originale. Lorsque nous nous appuyons sur d'autres médias ou sur des communiqués officiels, nous citons toujours nos sources en bas de page.</p>"
        f"<p>Contact : {esc(e['email'])}</p>"),
     "contact": ("Contact", f"<p>Pour toute question, correction ou information à nous transmettre :</p><p><strong>{esc(e['email'])}</strong></p>"
        f"<p>Éditeur : {esc(e['nom'])}, {esc(e['adresse'])}</p>"
        "<p>Nous corrigeons toute erreur signalée dans les meilleurs délais.</p>"),
     "mentions-legales": ("Mentions légales", f"<p><strong>Éditeur :</strong> {esc(e['nom'])}<br>{esc(e['adresse'])}<br>{esc(e['email'])}</p>"
        "<p><strong>Hébergement :</strong> à compléter (ex. Netlify, Inc.).</p>"
        "<p><strong>Propriété intellectuelle :</strong> les textes et visuels de ce site sont protégés. Toute reproduction sans autorisation est interdite.</p>"
        "<p><strong>Responsabilité :</strong> nous veillons à l'exactitude des informations publiées et corrigeons toute erreur signalée.</p>"),
     "confidentialite": ("Confidentialité et cookies", "<p>Ce site est financé par la publicité. Le réseau publicitaire Adsterra peut déposer des cookies et collecter des données techniques (adresse IP, appareil, pages consultées) afin d'afficher des annonces.</p>"
        "<p>Vous pouvez refuser ou supprimer ces cookies dans les paramètres de votre navigateur. Pour plus d'informations, consultez la politique de confidentialité d'Adsterra sur adsterra.com.</p>"
        f"<p>Responsable du traitement : {esc(e['nom'])} — {esc(e['email'])}.</p>"
        "<p>Vous disposez d'un droit d'accès, de rectification et de suppression de vos données (LPD suisse, RGPD pour les visiteurs de l'UE).</p>"),
    }
    for slug, (t, body) in pages.items():
        (OUT / f"{slug}.html").write_text(head(f"{t} – {SITE_NAME}", t, "") + header("") +
            f'<main style="display:block;max-width:760px"><h1>{t}</h1>{body}</main>' + footer(""), encoding="utf-8")
    if ADSENSE_CLIENT:
        (OUT / "ads.txt").write_text(f"google.com, {ADSENSE_CLIENT.replace('ca-','')}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")

def seo_files(arts):
    base = BASE_URL.rstrip("/")
    urls = [""] + [f"article/{a['slug']}.html" for a in arts] + [f"{x}.html" for x in ("a-propos", "contact", "mentions-legales", "confidentialite")]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + \
         "".join(f"<url><loc>{base}/{u}</loc></url>" for u in urls) + "</urlset>"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")

def main():
    arts = json.loads((ROOT / "articles.json").read_text(encoding="utf-8"))
    arts.sort(key=lambda a: a["date"], reverse=True)
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "article").mkdir(parents=True); (OUT / "social").mkdir()
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "logo.svg").write_text(logo_svg(256), encoding="utf-8")
    logo_png(OUT / "logo-profil.png")

    for a in arts:
        social_image(a, OUT / "social" / f"{a['slug']}.png")
        col = CATS.get(a["category"], "#334155")
        body = ""
        for i, p in enumerate(a["body"]):
            body += f"<p>{esc(p)}</p>"
            if i == 0: body += ad("inline")
        srcs = "".join(f'<li><a href="{esc(s["url"])}" rel="noopener nofollow" target="_blank">{esc(s["name"])}</a></li>' for s in a["sources"])
        demo = '<div class="demo">Article d\'exemple — à remplacer par un contenu réel.</div>' if a.get("demo") else ""
        page = (head(f'{a["title"]} – {SITE_NAME}', a["summary"], "../", f'social/{a["slug"]}.png') + header("../") +
                f'<main><article>{demo}{ad("top")}<span class="cat" style="background:{col}">{esc(a["category"])}</span>'
                f'<h1>{esc(a["title"])}</h1><div class="meta">{fr_date(a["date"])}</div>'
                f'<img class="hero" src="../social/{a["slug"]}.png" alt="{esc(a["title"])}">'
                f'<p class="lead">{esc(a["summary"])}</p>{body}{ad("inline")}'
                f'<div class="sources"><strong>Sources :</strong><ul>{srcs}</ul></div></article>'
                f'<aside>{ad("side")}<div class="box"><strong>À lire aussi</strong><br>' +
                "".join(f'<p><a href="{o["slug"]}.html">{esc(o["title"])}</a></p>' for o in arts if o is not a) +
                f'</div></aside></main>' + footer("../"))
        (OUT / "article" / f"{a['slug']}.html").write_text(page, encoding="utf-8")

    cards = ""
    for a in arts:
        col = CATS.get(a["category"], "#334155")
        cards += (f'<a class="card" href="article/{a["slug"]}.html"><img src="social/{a["slug"]}.png" alt="">'
                  f'<div><span class="cat" style="background:{col}">{esc(a["category"])}</span>'
                  f'<h2>{esc(a["title"])}</h2><p>{esc(a["summary"])}</p><span class="meta">{fr_date(a["date"])}</span></div></a>')
    idx = (head(f"{SITE_NAME} – {TAGLINE}", TAGLINE, "") + header("") +
           f'<main><section>{ad("top")}{cards}</section><aside>{ad("side")}</aside></main>' + footer(""))
    (OUT / "index.html").write_text(idx, encoding="utf-8")
    legal_pages(arts)
    seo_files(arts)
    print(f"{len(arts)} articles générés dans {OUT}")

if __name__ == "__main__":
    main()
