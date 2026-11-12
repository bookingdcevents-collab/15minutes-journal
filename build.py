#!/usr/bin/env python3
"""Générateur de site journal : articles.json -> site/ (HTML + visuels sociaux)."""
import json, html, textwrap, shutil, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- RÉGLAGES ----------
SITE_NAME = "15 minutes"
TAGLINE = "L'essentiel de l'actualité romande en 15 minutes"
BASE_URL = "https://15minutes.ch"                            # ex: https://vaudquotidien.ch (sert aux balises Facebook)
ADSENSE_CLIENT = "ca-pub-6969360272814757"                      # ex: ca-pub-1234567890123456 (après validation Google)
# Codes d'un autre réseau (ex. Adsterra) : coller le code HTML fourni dans l'emplacement voulu.
# Ne pas mélanger avec AdSense sur la même page.
ADPAGES = {}   # pages d'isolation des pubs (écrites dans docs/ads/ par main())
def _sandbox(inner, w, h, minw=0, maxw=99999, auto=False):
    # Isole la pub dans un cadre sandbox chargé depuis /ads/ (même domaine : Adsterra voit bien 15minutes.ch).
    # Pas de allow-top-navigation : la pub ne peut jamais rediriger la page entière, ses clics s'ouvrent dans un nouvel onglet.
    import hashlib
    name = hashlib.md5(inner.encode()).hexdigest()[:10]
    ADPAGES[name] = ('<!doctype html><html><head><meta charset="utf-8"><meta name="robots" content="noindex,nofollow">'
                     '<base target="_blank"><meta name="viewport" content="width=device-width,initial-scale=1"></head>'
                     '<body style="margin:0;background:transparent">' + inner + '</body></html>')
    grow = ("var r=function(){try{var d=f.contentDocument;var h=Math.max(d.body.scrollHeight,d.documentElement.scrollHeight);if(h>20)f.height=h}catch(e){}};"
            "f.onload=function(){r();setTimeout(r,1500);setTimeout(r,4000)};") if auto else ""
    return ("<script>(function(){var x=window.innerWidth;if(x<%d||x>%d)return;"
            "var f=document.createElement('iframe');"
            "f.setAttribute('sandbox','allow-scripts allow-popups allow-popups-to-escape-sandbox allow-same-origin');"
            "f.setAttribute('scrolling','no');f.setAttribute('title','Publicité');f.setAttribute('loading','lazy');f.width=%d;f.height=%d;"
            "f.style.cssText='border:0;display:block;margin:0 auto;max-width:100%%;width:'+(%s?'100%%':'%dpx');"
            "%sf.src='/ads/%s.html';var s=document.currentScript;s.parentNode.insertBefore(f,s);})();</script>") % (
            minw, maxw, w, h, 'true' if auto else 'false', w, grow, name)

def _adsterra(key, w, h, minw=0, maxw=99999):
    inner = ("<script>atOptions={'key':'%s','format':'iframe','height':%d,'width':%d,'params':{}};</script>"
             "<script src=\"https://bauval.org/22/%s\"></script>") % (key, h, w, key)
    return _sandbox(inner, w, h, minw, maxw)

GOAT = '<script data-goatcounter="https://15minutes.goatcounter.com/count" async src="//gc.zgo.at/count.js"></script>'
AD_CUSTOM = {
    "top": _adsterra("ad70c441f5e90255a8a63dfef45554bc", 728, 90, 768) + _adsterra("6030a2053a67c69f23be411862d595a0", 320, 50, 0, 767),  # 728x90 ordinateur/tablette, 320x50 mobile
    "inline": '<a href="https://restaurantlaforet.ch/?utm_source=15minutes&utm_medium=banniere&utm_campaign=pub-article" target="_blank" rel="noopener sponsored" onclick="try{goatcounter.count({path:&quot;clic-pub-laforet&quot;,title:&quot;Clic pub La Forêt&quot;,event:true})}catch(e){}" style="display:block;width:300px;max-width:100%;margin:0 auto"><img src="/photos/pub-laforet.jpg" width="300" height="250" alt="Restaurant La Forêt, pizzas au feu de bois, tous les mardis soir pizzas à CHF 13.90" style="display:block;width:100%;height:auto;border-radius:6px" loading="lazy"></a>',    # pub maison La Forêt 300x250
    "inline2": _adsterra("a3e64e45b98fd4792cf1a0693e36525d", 300, 250, 0),    # 300x250 Adsterra en fin d'article
    "side": _adsterra("e0d68e3d2a6e086240916f91bf50df95", 160, 600, 861),    # 160x600 colonne latérale (visible desktop)
}
_NATIVE_INNER = ('<script async="async" data-cfasync="false" src="https://bauval.org/21/44bc81f191dcd8fbf2267d2a001ad71f"></script>'
                 '<div id="container-44bc81f191dcd8fbf2267d2a001ad71f"></div>')
NATIVE = ('<div class="ad-native" style="margin:24px 0"><div style="font:600 11px system-ui,sans-serif;letter-spacing:.08em;text-transform:uppercase;color:#64748b;margin-bottom:6px">Contenus sponsorisés</div>'
          + _sandbox(_NATIVE_INNER, 700, 360, auto=True) + '</div>')
HEAD_SNIPPET = ""                        # code à placer dans <head>, si le réseau le demande
SHOW_AD_PLACEHOLDERS = False   # True = affiche des cadres "Espace publicitaire" (maquette uniquement)
EDITEUR = {"nom": "GG Distribution Alimentaire Ltd", "adresse": "71-75 Shelton Street, Covent Garden, London, United Kingdom, WC2H 9JQ", "email": "bookingdcevents@gmail.com"}
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

def head(title, desc, rel, og_img=None, url=None, ld=None, art=None):
    adsense = (f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>'
               if ADSENSE_CLIENT else "")
    og = ""
    if og_img:
        full = f"{BASE_URL}/{og_img}" if BASE_URL else og_img
        og = (f'<meta property="og:type" content="article"><meta property="og:title" content="{esc(title)}">'
              f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{esc(full)}"><meta property="og:image:secure_url" content="{esc(full)}"><meta property="og:image:type" content="image/jpeg"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="675">'
              f'<meta property="og:site_name" content="{esc(SITE_NAME)}"><meta name="twitter:card" content="summary_large_image">')
    base = BASE_URL.rstrip("/")
    canon = f'<link rel="canonical" href="{base}/{url or ""}"><meta property="og:url" content="{base}/{url or ""}"><meta property="og:locale" content="fr_CH">'
    if not og_img:
        og = (f'<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">'
              f'<meta property="og:description" content="{esc(desc)}"><meta property="og:image" content="{base}/logo-profil.png">'
              f'<meta property="og:site_name" content="{esc(SITE_NAME)}"><meta name="twitter:card" content="summary">')
    if art:
        og += (f'<meta property="article:published_time" content="{art["date"]}T07:00:00+01:00"><meta property="article:section" content="{esc(art["category"])}">'
               f'<meta property="article:author" content="{esc(art.get("author","La rédaction"))}">')
    ldj = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ""
    return (f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'{HEAD_SNIPPET}<title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta name="robots" content="index,follow,max-image-preview:large">{canon}{og}{ldj}'
            f'<link rel="icon" href="/favicon.ico" sizes="48x48"><link rel="icon" type="image/png" sizes="48x48" href="/favicon-48.png"><link rel="icon" type="image/png" sizes="192x192" href="/favicon-192.png"><link rel="icon" type="image/svg+xml" href="/logo.svg"><link rel="apple-touch-icon" href="/apple-touch-icon.png"><link rel="stylesheet" href="{rel}style.css">{adsense}{GOAT}</head><body>')

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
    nav = "".join(f'<a href="{rel}index.html?cat={esc(c)}" data-cat="{esc(c)}" style="--c:{col}">{esc(c)}</a>' for c, col in CATS.items())
    return (f'<div class="hd"><header class="top"><a class="logo" href="{rel}index.html">{logo_svg(40)}<span>{esc(SITE_NAME)}</span></a>'
            f'<span class="tag">{esc(TAGLINE)}</span>'
            f'<button class="lens" type="button" aria-label="Rechercher" onclick="var f=document.getElementById(\'sf\');f.classList.toggle(\'open\');if(f.classList.contains(\'open\'))document.getElementById(\'q\').focus()">'
            f'<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5L21 21"/></svg></button></header>'
            f'<form id="sf" class="sf" action="{rel}index.html" method="get" role="search"><input id="q" name="q" type="search" placeholder="Rechercher un article…" autocomplete="off"></form>'
            f'<nav class="cats"><a href="{rel}index.html" data-cat="">À la une</a>{nav}</nav></div>')

CONSENT = """<div id="cb" style="display:none;position:fixed;left:0;right:0;bottom:0;z-index:9999;background:#111;color:#fff;padding:14px 16px;font:14px/1.4 system-ui,sans-serif;box-shadow:0 -2px 12px rgba(0,0,0,.3)"><div style="max-width:900px;margin:auto;display:flex;gap:12px;flex-wrap:wrap;align-items:center"><span style="flex:1 1 300px">Nous utilisons des cookies publicitaires (réseau Adsterra) pour financer ce site gratuit. Vous pouvez les accepter ou les refuser. <a href="/confidentialite.html" style="color:#9cf">En savoir plus</a></span><button id="cr" style="padding:8px 16px;border:1px solid #fff;background:none;color:#fff;border-radius:6px;cursor:pointer">Refuser</button><button id="ca" style="padding:8px 16px;border:0;background:#fff;color:#111;border-radius:6px;cursor:pointer;font-weight:600">Accepter</button></div></div><script>function rc15(){try{localStorage.removeItem('c15')}catch(e){}location.reload();return false}(function(){var v=null;try{v=localStorage.getItem('c15')}catch(e){}if(v===null){var b=document.getElementById('cb');b.style.display='block';document.getElementById('ca').onclick=function(){try{localStorage.setItem('c15','1')}catch(e){}location.reload()};document.getElementById('cr').onclick=function(){try{localStorage.setItem('c15','0')}catch(e){}b.style.display='none'}}})();</script>"""

INDEX_JS = '''<script>(function(){var p=new URLSearchParams(location.search),q=(p.get('q')||'').trim().toLowerCase(),c=p.get('cat')||'';
var cs=document.querySelectorAll('.card'),n=0;
function norm(x){return x.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'')}
var nq=norm(q).split(/\\s+/).filter(Boolean);
cs.forEach(function(e){var ok=(!c||e.dataset.cat===c);if(ok&&nq.length){var t=norm(e.dataset.t);ok=nq.every(function(w){return t.indexOf(w)>-1})}e.style.display=ok?'':'none';if(ok)n++});
document.querySelectorAll('.cats a').forEach(function(a){if((a.dataset.cat||'')===c)a.classList.add('on')});
var qi=document.getElementById('q');if(q){qi.value=p.get('q');document.getElementById('sf').classList.add('open')}
var cn=document.querySelector('.cats');if(c&&cn)cn.classList.add('has-on');var fv=document.querySelector('.card:not([style*="display: none"])');if(fv&&!q&&!c)fv.classList.add('big');else if(fv&&n>0)fv.classList.add('big');
var m=document.getElementById('nores');if(m&&(q||c)&&n===0)m.style.display='block';
var h=document.getElementById('hl');if(h&&(q||c))h.textContent=q?('Résultats pour « '+p.get('q')+' » ('+n+')'):c;
})();</script>'''

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

import sys; sys.path.insert(0, str(Path(__file__).parent))
import illus

def photo(a, w, h):
    """Photo fournie (docs/photos/<fichier>) recadrée au format voulu, ou None."""
    f = a.get("image")
    if not f or not (OUT / "photos" / f).exists(): return None
    from PIL import ImageOps
    return ImageOps.fit(Image.open(OUT / "photos" / f).convert("RGB"), (w, h), Image.LANCZOS)

def hero_image(a, path):
    W, H = 1200, 675
    c = CATS.get(a["category"], "#334155")
    r, g, bl = [int(c[i:i+2], 16) for i in (1, 3, 5)]
    img = Image.new("RGB", (W, H)); d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=(int(r*(1-.6*k)), int(g*(1-.6*k)), int(bl*(1-.6*k))))
    ph = photo(a, 1200, 675)
    if ph: img = ph
    else:
        sc = illus.scene(a.get("motif", "press"), c).resize((1100, 616))
        img.paste(sc, (50, 30), sc)
    img.save(path, optimize=True)

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
    ph = photo(a, 1040, 582)
    if ph: img.paste(ph, (20, 170))
    else:
        sc = illus.scene(a.get("motif", "press"), c).resize((1040, 582))
        img.paste(sc, (20, 170), sc)
    d.rounded_rectangle([60, 770, 60 + tw + 50, 835], radius=8, fill="white")
    d.text((85, 781), a["category"].upper(), font=tag, fill=c)
    size = 76
    while True:
        f = ImageFont.truetype(FONT_B, size)
        lines = wrap(a["title"], f, W - 120, d)
        if len(lines) * (size + 12) <= 380 or size <= 44: break
        size -= 4
    y = 860
    for ln in lines:
        d.text((60, y), ln, font=f, fill="white"); y += size + 12
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
.ad-top{min-height:90px}.ad-inline,.ad-inline2{min-height:250px}.ad-side{min-height:600px}@media(max-width:860px){.ad-side{display:none}}@media(max-width:767px){.ad-top{min-height:50px}}
aside .box{background:#fff;border:1px solid #e3e1da;border-radius:8px;padding:14px 16px;font:15px system-ui,sans-serif}
.nores{display:none;font:16px system-ui,sans-serif;color:#667;padding:20px 0}
/* ---- Design moderne ---- */
body{background:#f3f4f7}
.hd{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.94);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);box-shadow:0 1px 0 #e6e8ee,0 6px 20px -12px rgba(15,23,42,.25)}
.top{background:none;border:0;padding:12px 20px;display:flex;align-items:center;gap:14px;max-width:1100px;margin:0 auto;flex-wrap:nowrap}
.logo{font:800 26px/1 system-ui,-apple-system,'Segoe UI',sans-serif;letter-spacing:-.8px}.logo svg{width:34px;height:34px}
.tag{font:500 13px system-ui,sans-serif;color:#8a90a0;white-space:nowrap}
@media(max-width:760px){.logo{font-size:22px}.logo svg{width:28px;height:28px}.tag{font-size:11px;line-height:1.25;white-space:normal;max-width:130px}}
.lens{margin-left:auto;width:42px;height:42px;border-radius:50%;background:#f0f1f5;border:0;cursor:pointer;color:#16181d;display:flex;align-items:center;justify-content:center;transition:background .15s,transform .15s;padding:0;flex:none}
.lens:hover{background:#e4e6ee}.lens:active{transform:scale(.94)}
.sf{display:block;max-height:0;overflow:hidden;opacity:0;padding:0 20px;transition:max-height .25s ease,opacity .2s ease,padding .25s ease;max-width:1100px;margin:0 auto}
.sf.open{max-height:80px;opacity:1;padding:0 20px 12px}
.sf input{width:100%;display:block;padding:12px 16px;font:16px system-ui,sans-serif;border:2px solid #e1e4ec;border-radius:14px;background:#f8f9fb;outline:none;transition:border-color .15s,background .15s}
.sf input:focus{border-color:#16181d;background:#fff}
.cats{max-width:1100px;margin:0 auto;padding:2px 20px 12px;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.cats::-webkit-scrollbar{display:none}
.cats a{flex:none;font:700 13px system-ui,sans-serif;letter-spacing:.03em;text-decoration:none;color:#fff;background:var(--c,#16181d);padding:9px 16px;border-radius:12px;transition:transform .12s,box-shadow .15s,opacity .15s}
.cats a:hover{transform:translateY(-2px);box-shadow:0 6px 14px -6px var(--c,#16181d)}
.cats.has-on a:not(.on){opacity:.45}.cats a.on{box-shadow:0 0 0 3px #fff,0 0 0 5px var(--c,#16181d)}
main{max-width:1100px}
.feed{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.feed .card{margin:0;display:flex;flex-direction:column;border:0;border-radius:18px;box-shadow:0 2px 4px rgba(15,23,42,.04),0 10px 30px -16px rgba(15,23,42,.25);transition:transform .18s,box-shadow .18s}
.feed .card:hover{transform:translateY(-4px);box-shadow:0 4px 8px rgba(15,23,42,.05),0 18px 40px -16px rgba(15,23,42,.35)}
.feed .card div{padding:16px 18px 18px;flex:1}
.feed .card h2{font:800 20px/1.25 system-ui,-apple-system,'Segoe UI',sans-serif;letter-spacing:-.3px}
.feed .card p{font:15px/1.5 system-ui,sans-serif;color:#5b6272;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}
.feed .card.big{grid-column:1/-1}.feed .card.big h2{font-size:28px}.feed .card.big img{aspect-ratio:2/1}
.cat{border-radius:8px;padding:4px 10px}
.card .meta{display:block;margin-top:10px}
@media(max-width:700px){.feed{grid-template-columns:1fr}.feed .card.big h2{font-size:23px}.top{padding:10px 16px}.cats,.sf{padding-left:16px;padding-right:16px}}
#hl{letter-spacing:-.3px}
footer{text-align:center;font:13px system-ui,sans-serif;color:#667;padding:30px 20px}
"""

def legal_pages(arts):
    e = EDITEUR
    pages = {
     "a-propos": ("À propos", f"<p><strong>{esc(SITE_NAME)}</strong> propose chaque jour l'essentiel de l'actualité romande, présenté en lecture courte.</p>"
        "<p>Nos articles sont rédigés de façon originale. Lorsque nous nous appuyons sur d'autres médias ou sur des communiqués officiels, nous citons toujours nos sources en bas de page.</p>"
        "<p><strong>Notre démarche.</strong> Nous nous en tenons aux faits vérifiables, nous attribuons à leur source les informations non confirmées et nous respectons la présomption d'innocence. Nous ne publions pas le nom des personnes privées ni des mineurs.</p>"
        "<p><strong>Illustrations.</strong> Les images générées par intelligence artificielle sont signalées par la mention « Illustration générée par IA ». Les autres images sont créditées lorsque leur origine est connue.</p>"
        "<p><strong>Corrections.</strong> Une erreur ? Écrivez-nous : nous corrigeons rapidement et nous signalons la correction dans l'article.</p>"
        f"<p>Contact : {esc(e['email'])}</p>"),
     "contact": ("Contact", f"<p>Pour toute question, correction ou information à nous transmettre :</p><p><strong>{esc(e['email'])}</strong></p>"
        f"<p>Éditeur : {esc(e['nom'])}, {esc(e['adresse'])}</p>"
        "<p>Nous corrigeons toute erreur signalée dans les meilleurs délais.</p>"),
     "mentions-legales": ("Mentions légales", f"<p><strong>Éditeur :</strong> {esc(e['nom'])}<br>{esc(e['adresse'])}<br>{esc(e['email'])}</p>"
        "<p><strong>Hébergement :</strong> GitHub Pages (GitHub, Inc., 88 Colin P. Kelly Jr. Street, San Francisco, CA 94107, États-Unis).</p>"
        "<p><strong>Propriété intellectuelle :</strong> les textes et visuels de ce site sont protégés. Toute reproduction sans autorisation est interdite.</p>"
        "<p><strong>Responsabilité :</strong> nous veillons à l'exactitude des informations publiées et corrigeons toute erreur signalée.</p>"),
     "confidentialite": ("Confidentialité et cookies", "<p>Ce site est financé par la publicité. Des réseaux publicitaires tiers, dont Adsterra et Google (AdSense), peuvent déposer ou lire des cookies et collecter des données techniques (adresse IP, appareil, pages consultées) afin d'afficher et de mesurer des annonces, y compris personnalisées.</p>"
        "<p>Les annonces Google utilisent des cookies, notamment pour afficher des annonces en fonction de vos visites sur ce site et sur d'autres sites. Vous pouvez gérer la personnalisation des annonces Google sur adssettings.google.com et consulter les règles de Google sur policies.google.com/technologies/ads.</p>"
        "<p><strong>Mesure d'audience.</strong> Nous utilisons GoatCounter, un outil de statistiques qui ne dépose pas de cookie et ne collecte pas de données permettant de vous identifier. Il compte les pages vues, le navigateur, le pays et les clics sur certaines annonces.</p>"
        "<p><strong>Votre choix.</strong> Vous pouvez refuser ou supprimer les cookies à tout moment dans les paramètres de votre navigateur.</p>"
        "<p>Vous pouvez refuser ou supprimer ces cookies dans les paramètres de votre navigateur. Pour plus d'informations, consultez la politique de confidentialité d'Adsterra sur adsterra.com.</p>"
        f"<p>Responsable du traitement : {esc(e['nom'])} — {esc(e['email'])}.</p>"
        "<p>Vous disposez d'un droit d'accès, de rectification et de suppression de vos données (LPD suisse, RGPD pour les visiteurs de l'UE).</p>"),
    }
    for slug, (t, body) in pages.items():
        (OUT / f"{slug}.html").write_text(head(f"{t} – {SITE_NAME}", t, "", url=f"{slug}.html") + header("") +
            f'<main style="display:block;max-width:760px"><h1>{t}</h1>{body}</main>' + footer(""), encoding="utf-8")
    if ADSENSE_CLIENT:
        (OUT / "ads.txt").write_text(f"google.com, {ADSENSE_CLIENT.replace('ca-','')}, DIRECT, f08c47fec0942fa0\n", encoding="utf-8")

def seo_files(arts):
    base = BASE_URL.rstrip("/")
    import datetime
    today = datetime.date.today().isoformat()
    ents = [f"<url><loc>{base}/</loc><lastmod>{arts[0]['date']}</lastmod><changefreq>hourly</changefreq><priority>1.0</priority></url>"]
    ents += [f"<url><loc>{base}/article/{a['slug']}.html</loc><lastmod>{a['date']}</lastmod><priority>0.8</priority></url>" for a in arts]
    ents += [f"<url><loc>{base}/{x}.html</loc><priority>0.3</priority></url>" for x in ("a-propos", "contact", "mentions-legales", "confidentialite")]
    sm = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(ents) + "</urlset>"
    (OUT / "sitemap.xml").write_text(sm, encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}/sitemap.xml\n", encoding="utf-8")

def main():
    arts = json.loads((ROOT / "articles.json").read_text(encoding="utf-8"))
    arts.sort(key=lambda a: a["date"], reverse=True)
    if OUT.exists(): shutil.rmtree(OUT)
    (OUT / "article").mkdir(parents=True); (OUT / "social").mkdir()
    if (ROOT / "photos").exists(): shutil.copytree(ROOT / "photos", OUT / "photos")
    (OUT / "ads").mkdir()
    for _n, _h in ADPAGES.items(): (OUT / "ads" / f"{_n}.html").write_text(_h, encoding="utf-8")
    (OUT / "CNAME").write_text("15minutes.ch\n")
    (OUT / "google328dac0fa93f198c.html").write_text("google-site-verification: google328dac0fa93f198c.html")
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "logo.svg").write_text(logo_svg(256), encoding="utf-8")
    logo_png(OUT / "logo-profil.png")
    # favicons (horloge seule, fond blanc) : ico + PNG 48/192 + apple-touch
    from PIL import Image as _I
    _base = _I.open(OUT / "logo-profil.png").convert("RGB").crop((184, 82, 840, 738))
    for _n, _sz in (("favicon-48.png", 48), ("favicon-192.png", 192), ("apple-touch-icon.png", 180)):
        _base.resize((_sz, _sz), _I.LANCZOS).save(OUT / _n)
    _base.resize((256, 256), _I.LANCZOS).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])

    for a in arts:
        social_image(a, OUT / "social" / f"{a['slug']}.png")
        (OUT / "img").mkdir(exist_ok=True); hero_image(a, OUT / "img" / f"{a['slug']}.jpg")
        import hashlib; a["_v"] = hashlib.md5((OUT / "img" / f"{a['slug']}.jpg").read_bytes()).hexdigest()[:8]
        col = CATS.get(a["category"], "#334155")
        body = ""
        for i, p in enumerate(a["body"]):
            body += f"<p>{esc(p)}</p>"
            if i == 0: body += ad("inline")
        srcs = "".join((f'<li><a href="{esc(s["url"])}" rel="noopener nofollow" target="_blank">{esc(s["name"])}</a></li>' if s.get("url") else f'<li>{esc(s["name"])}</li>') for s in a["sources"])
        credit = f'<div class="meta" style="margin:-8px 0 14px">{esc(a["image_credit"])}</div>' if a.get("image") and a.get("image_credit") else ""
        demo = '<div class="demo">Article d\'exemple — à remplacer par un contenu réel.</div>' if a.get("demo") else ""
        base_ = BASE_URL.rstrip("/")
        ld = {"@context": "https://schema.org", "@type": "NewsArticle", "mainEntityOfPage": f"{base_}/article/{a['slug']}.html",
              "headline": a["title"][:110], "description": a["summary"], "image": [f"{base_}/img/{a['slug']}.jpg"],
              "datePublished": f"{a['date']}T07:00:00+01:00", "dateModified": f"{a['date']}T07:00:00+01:00", "articleSection": a["category"],
              "inLanguage": "fr-CH", "author": {"@type": "Person", "name": a.get("author", "La rédaction")},
              "publisher": {"@type": "Organization", "name": SITE_NAME, "logo": {"@type": "ImageObject", "url": f"{base_}/logo-profil.png"}}}
        page = (head(f'{a["title"]} – {SITE_NAME}', a["summary"], "../", f'img/{a["slug"]}.jpg?v={a["_v"]}', url=f"article/{a['slug']}.html", ld=ld, art=a) + header("../") +
                f'<main><article>{demo}{ad("top")}<span class="cat" style="background:{col}">{esc(a["category"])}</span>'
                f'<h1>{esc(a["title"])}</h1><div class="meta">Par <strong>{esc(a.get("author","La rédaction"))}</strong> · {fr_date(a["date"])}</div>'
                f'<img class="hero" src="../img/{a["slug"]}.jpg?v={a["_v"]}" alt="{esc(a["title"])}">{credit}'
                f'<p class="lead">{esc(a["summary"])}</p>{body}{ad("inline2")}'
                f'<div class="sources"><strong>Sources :</strong><ul>{srcs}</ul></div>{NATIVE}</article>'
                f'<aside>{ad("side")}<div class="box"><strong>À lire aussi</strong><br>' +
                "".join(f'<p><a href="{o["slug"]}.html">{esc(o["title"])}</a></p>' for o in arts if o is not a) +
                f'</div></aside></main>' + footer("../"))
        (OUT / "article" / f"{a['slug']}.html").write_text(page, encoding="utf-8")

    cards = ""
    for a in arts:
        col = CATS.get(a["category"], "#334155")
        cards += (f'<a class="card" data-cat="{esc(a["category"])}" data-t="{esc((a["title"]+" "+a["summary"]+" "+a["category"]).lower())}" href="article/{a["slug"]}.html"><img src="img/{a["slug"]}.jpg?v={a["_v"]}" alt="">'
                  f'<div><span class="cat" style="background:{col}">{esc(a["category"])}</span>'
                  f'<h2>{esc(a["title"])}</h2><p>{esc(a["summary"])}</p><span class="meta">Par {esc(a.get("author","La rédaction"))} · {fr_date(a["date"])}</span></div></a>')
    idx = (head(f"{SITE_NAME} – {TAGLINE}", TAGLINE, "", url="", ld={"@context": "https://schema.org", "@type": "NewsMediaOrganization", "name": SITE_NAME, "url": BASE_URL.rstrip("/") + "/", "logo": BASE_URL.rstrip("/") + "/logo-profil.png", "inLanguage": "fr-CH"}) + header("") +
           f'<main><section>{ad("top")}<h1 id="hl" style="font:700 20px system-ui,sans-serif;margin:0 0 14px"></h1><div id="nores" class="nores">Aucun article ne correspond. <a href="index.html">Voir les derniers articles</a></div><div class="feed">{cards}</div></section><aside>{ad("side")}</aside></main>' + INDEX_JS + footer(""))
    (OUT / "index.html").write_text(idx, encoding="utf-8")
    legal_pages(arts)
    seo_files(arts)
    print(f"{len(arts)} articles générés dans {OUT}")

if __name__ == "__main__":
    main()
