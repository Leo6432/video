#!/usr/bin/env python3
"""
DALEP 2100 — Générateur de vidéo publicitaire
Usage  : python3 generate_video.py
Output : dalep2100_pub.mp4  (~36 secondes, 1920×1080, 24 fps)
"""

import os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from moviepy import VideoClip, concatenate_videoclips

# ─── Configuration ────────────────────────────────────────────────────────────
W, H = 1920, 1080
FPS  = 24
PRODUCT_PATH = os.path.join(os.path.dirname(__file__), "images (3).jpg")
OUTPUT_PATH  = os.path.join(os.path.dirname(__file__), "dalep2100_pub.mp4")

# ─── Palette ──────────────────────────────────────────────────────────────────
C_BLACK      = (  5,   5,   5)
C_DARK       = ( 12,  18,  12)
C_DARK_GREEN = ( 27,  68,  27)
C_GREEN      = ( 46, 125,  50)
C_MID_GREEN  = ( 56, 142,  60)
C_LIGHT_GRN  = ( 76, 175,  80)
C_ACCENT     = (129, 199, 132)
C_WHITE      = (255, 255, 255)
C_GRAY       = (180, 180, 180)
C_GOLD       = (255, 213,  79)

# ─── Fonts ────────────────────────────────────────────────────────────────────
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
]

def _load(size):
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

print("Chargement des fontes...")
F180 = _load(180); F140 = _load(140); F100 = _load(100)
F80  = _load(80);  F65  = _load(65);  F50  = _load(50)
F38  = _load(38);  F30  = _load(30)

# ─── Utilitaires ──────────────────────────────────────────────────────────────
def ease_out(t): return 1 - (1 - max(0.0, min(1.0, t))) ** 3
def lerp(a, b, t): return a + (b - a) * max(0.0, min(1.0, t))
def lerp_c(c1, c2, t): return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))
def fade_c(c, a):  return tuple(int(v * max(0.0, min(1.0, a))) for v in c)

def scene_fade(t, dur, fi=0.55, fo=0.55):
    """Multiplicateur fade-in/out pour toute la scène."""
    a = 1.0
    if t < fi:      a = min(a, t / fi)
    if t > dur - fo: a = min(a, (dur - t) / fo)
    return max(0.0, a)

def vgrad(c1, c2):
    """Dégradé vertical NumPy → uint8 (H×W×3)."""
    arr = np.zeros((H, W, 3), dtype=np.float32)
    ts  = np.linspace(0, 1, H, dtype=np.float32)
    for i in range(3):
        arr[:, :, i] = (c1[i] + (c2[i] - c1[i]) * ts)[:, np.newaxis]
    return arr.astype(np.uint8)

def draw_text_c(draw, text, font, y, color, alpha=1.0):
    """Centre horizontalement et dessine le texte."""
    c = fade_c(color, alpha)
    bb = draw.textbbox((0, 0), text, font=font)
    x  = (W - (bb[2] - bb[0])) // 2
    draw.text((x, y), text, font=font, fill=c)

def draw_text_shadow(draw, text, font, x, y, color, alpha=1.0, sh=5):
    draw.text((x + sh, y + sh), text, font=font, fill=fade_c(C_BLACK, alpha * 0.55))
    draw.text((x,      y     ), text, font=font, fill=fade_c(color,   alpha))

def draw_text_cs(draw, text, font, y, color, alpha=1.0, sh=5):
    """Centre + ombre."""
    bb = draw.textbbox((0, 0), text, font=font)
    x  = (W - (bb[2] - bb[0])) // 2
    draw_text_shadow(draw, text, font, x, y, color, alpha, sh)

def apply_fade(arr, alpha):
    if alpha >= 1.0: return arr
    return (arr * max(0.0, min(1.0, alpha))).astype(np.uint8)

# ─── Fonds pré-calculés ───────────────────────────────────────────────────────
print("Génération des arrière-plans...")
BG1 = vgrad(C_DARK,       C_BLACK)
BG2 = vgrad((28, 18,  8), ( 8,  5,  2))
BG3 = vgrad(C_DARK_GREEN, ( 8, 28,  8))
BG4 = vgrad(( 8, 28,  8), C_DARK_GREEN)
BG5 = vgrad(C_DARK,       ( 5, 14,  5))
BG6 = vgrad(C_GREEN,      C_MID_GREEN)

# ─── Image produit ────────────────────────────────────────────────────────────
print("Chargement de l'image produit...")
_prod_orig = Image.open(PRODUCT_PATH).convert("RGBA")
_prod_arr  = np.array(_prod_orig)
# Rendre le fond blanc transparent
r, g, b = _prod_arr[:,:,0], _prod_arr[:,:,1], _prod_arr[:,:,2]
_prod_arr[:,:,3] = np.where((r > 228) & (g > 228) & (b > 228), 0, 255)
PRODUCT_IMG = Image.fromarray(_prod_arr)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 1 — Intro marque (5 s)
# ══════════════════════════════════════════════════════════════════════════════
def scene1(t):
    DUR = 5.0; sa = scene_fade(t, DUR)
    img  = Image.fromarray(BG1.copy()); draw = ImageDraw.Draw(img)

    # Ligne verte animée (sweep horizontal)
    lp = ease_out(min(1.0, t / 1.2))
    x1 = int(W * (0.5 - lp * 0.5)); x2 = int(W * (0.5 + lp * 0.5))
    draw.rectangle([x1, H//2 - 5, x2, H//2 + 5], fill=C_GREEN)

    # "DALEP" — slide-up + fade-in
    if t > 0.3:
        a = ease_out((t - 0.3) / 1.0) * sa
        dy = int((1 - ease_out(min(1.0, (t - 0.3) / 0.8))) * 70)
        bb = draw.textbbox((0, 0), "DALEP", font=F180)
        tw, th = bb[2]-bb[0], bb[3]-bb[1]
        x = (W - tw) // 2; y = H//2 - th - 65 + dy
        # Halo vert
        for dx in (-5, -2, 2, 5):
            draw.text((x+dx, y+5), "DALEP", font=F180, fill=fade_c(C_DARK_GREEN, a*0.45))
        draw_text_shadow(draw, "DALEP", F180, x, y, C_WHITE, a, sh=6)

    # Barre accent
    if t > 1.6:
        a = ease_out((t - 1.6) / 0.5) * sa
        bw = int(640 * a)
        draw.rectangle([(W-bw)//2, H//2+16, (W+bw)//2, H//2+22], fill=C_ACCENT)

    # Sous-titre
    if t > 1.9:
        a = ease_out((t - 1.9) / 0.7) * sa
        draw_text_c(draw, "SOLUTIONS PROFESSIONNELLES", F50, H//2+36, C_ACCENT, a)

    # Badge PRO doré
    if t > 2.7:
        a = ease_out((t - 2.7) / 0.5) * sa
        bw2 = 170; bh2 = 64
        bx = (W - bw2)//2; by = H//2 + 136
        draw.rounded_rectangle([bx, by, bx+bw2, by+bh2], radius=12, fill=fade_c(C_GOLD, a))
        bb = draw.textbbox((0,0), "PRO", font=F65); tw2 = bb[2]-bb[0]
        draw.text((bx+(bw2-tw2)//2, by+7), "PRO", font=F65, fill=fade_c(C_BLACK, a))

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 2 — Le problème (6 s)
# ══════════════════════════════════════════════════════════════════════════════
PROBLEMS = [
    ("MOUSSES.", (110, 150,  80)),
    ("ALGUES.",  ( 60, 120,  60)),
    ("LICHENS.", (150, 138,  72)),
]

def scene2(t):
    DUR = 6.0; sa = scene_fade(t, DUR)
    img  = Image.fromarray(BG2.copy()); draw = ImageDraw.Draw(img)

    if t > 0.3:
        draw_text_c(draw, "LE PROBLEME", F38, 80, C_GRAY, ease_out((t-0.3)/0.5)*sa)

    for i, (word, col) in enumerate(PROBLEMS):
        start = 0.9 + i * 1.3
        if t > start:
            a   = ease_out((t - start) / 0.7) * sa
            xo  = int((1 - ease_out(min(1.0,(t-start)/0.65))) * -130)
            bb  = draw.textbbox((0,0), word, font=F140)
            tw, th = bb[2]-bb[0], bb[3]-bb[1]
            x = (W - tw)//2 + xo; y = 230 + i * 220
            # Fond pill coloré
            pad = 26
            draw.rounded_rectangle([x-pad, y-pad//2, x+tw+pad, y+th+pad//2],
                                    radius=16, fill=lerp_c(C_BLACK, col, a*0.35))
            draw_text_shadow(draw, word, F140, x, y, lerp_c(col, C_WHITE, 0.5), a, sh=6)

    if t > 4.8:
        a = ease_out((t-4.8)/0.7) * sa
        draw_text_c(draw, "Il existe une solution.", F65, H-170, C_ACCENT, a)

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 3 — Révélation produit (7 s)
# ══════════════════════════════════════════════════════════════════════════════
def scene3(t):
    DUR = 7.0; sa = scene_fade(t, DUR)
    img  = Image.fromarray(BG3.copy()); draw = ImageDraw.Draw(img)

    # Halos lumineux concentriques
    if t > 0.5:
        ga = ease_out((t-0.5)/1.5) * sa * 0.4
        cx, cy = W//2, H//2 + 30
        for r, col in ((340, C_LIGHT_GRN), (270, C_ACCENT), (200, C_WHITE)):
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=None,
                         outline=fade_c(col, ga*0.6), width=3)

    # Carte blanche derrière le produit
    CW, CH2 = 720, 810
    CX = (W - CW)//2; CY = (H - CH2)//2 - 30
    if t > 0.2:
        a = ease_out((t-0.2)/0.9) * sa
        draw.rounded_rectangle([CX, CY, CX+CW, CY+CH2], radius=28,
                                fill=fade_c(C_WHITE, a*0.94))

    # Image produit avec zoom Ken Burns
    if t > 0.5:
        a_prod = ease_out((t-0.5)/1.1) * sa
        zoom   = 1.0 + 0.09 * (t / DUR)
        th     = int(730 * zoom)
        tw_p   = int(PRODUCT_IMG.width * th / PRODUCT_IMG.height)
        prod_r = PRODUCT_IMG.resize((tw_p, th), Image.LANCZOS)

        # Ajuster opacité via canal alpha
        pa = np.array(prod_r)
        pa[:,:,3] = (pa[:,:,3] * a_prod).astype(np.uint8)
        prod_faded = Image.fromarray(pa)

        px = (W - tw_p)//2; py = CY + (CH2 - th)//2 + 20
        # Clamp
        px0 = max(0, px); py0 = max(0, py)
        ex  = min(W, px + tw_p); ey = min(H, py + th)
        cx0 = max(0, -px); cy0 = max(0, -py)
        if ex > px0 and ey > py0:
            crop = prod_faded.crop((cx0, cy0, cx0+(ex-px0), cy0+(ey-py0)))
            img_rgba = img.convert("RGBA")
            img_rgba.paste(crop, (px0, py0), crop)
            img = img_rgba.convert("RGB")
            draw = ImageDraw.Draw(img)

    # Textes
    if t > 1.9:
        a = ease_out((t-1.9)/0.7) * sa
        draw_text_cs(draw, "DALEP 2100", F100, 68, C_WHITE, a)
    if t > 2.7:
        a = ease_out((t-2.7)/0.7) * sa
        draw_text_c(draw, "Traitement Anti-Vegetaux", F65, 188, C_GOLD, a)
    if t > 4.0:
        a = ease_out((t-4.0)/0.5) * sa
        draw_text_c(draw, "* * * * *", F65, H-195, C_GOLD, a)
        draw_text_c(draw, "Efficacite prouvee  |  Resultats durables", F38, H-112, C_ACCENT, a)

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 4 — Les atouts (8 s)
# ══════════════════════════════════════════════════════════════════════════════
BENEFITS = [
    ("DESINFECTE",  "Elimine bacteries et germes en profondeur",  C_ACCENT    ),
    ("ASSAINIT",    "Nettoie et assainit toutes les surfaces",     C_LIGHT_GRN ),
    ("ELIMINE",     "Mousses, algues et lichens durablement",      C_GOLD      ),
]

def scene4(t):
    DUR = 8.0; sa = scene_fade(t, DUR)
    img  = Image.fromarray(BG4.copy()); draw = ImageDraw.Draw(img)

    if t > 0.3:
        a = ease_out((t-0.3)/0.6) * sa
        draw_text_cs(draw, "SES ATOUTS", F80, 68, C_WHITE, a)
        uw = int(560 * a)
        draw.rectangle([(W-uw)//2, 164, (W+uw)//2, 170], fill=fade_c(C_ACCENT, a))

    M = 130  # marge horizontale
    for i, (title, subtitle, col) in enumerate(BENEFITS):
        st = 0.9 + i * 2.0
        if t > st:
            a  = ease_out((t-st)/0.8) * sa
            xo = int((1 - ease_out(min(1.0,(t-st)/0.65))) * 110)
            y  = 240 + i * 240

            # Carte
            card_c = lerp_c(C_DARK_GREEN, col, a*0.22)
            draw.rounded_rectangle([M+xo, y-20, W-M+xo, y+178],
                                    radius=20, fill=card_c)
            draw.rounded_rectangle([M+xo, y-20, W-M+xo, y+178],
                                    radius=20, fill=None,
                                    outline=fade_c(col, a*0.55), width=2)

            # Cercle icône
            ico_cx = M + 72 + xo; ico_cy = y + 79
            draw.ellipse([ico_cx-44, ico_cy-44, ico_cx+44, ico_cy+44],
                         fill=fade_c(col, a))
            bb = draw.textbbox((0,0), "+", font=F80)
            draw.text((ico_cx-(bb[2]-bb[0])//2, ico_cy-(bb[3]-bb[1])//2),
                      "+", font=F80, fill=fade_c(C_BLACK, a))

            # Textes
            draw.text((M+148+xo, y+14),  title,    font=F80, fill=fade_c(col,    a))
            draw.text((M+148+xo, y+108), subtitle, font=F38, fill=fade_c(C_GRAY, a))

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 5 — Surfaces d'application (5 s)
# ══════════════════════════════════════════════════════════════════════════════
APPS = [
    ("TOITS",     C_ACCENT    ),
    ("FACADES",   C_LIGHT_GRN ),
    ("TERRASSES", C_GOLD      ),
    ("ALLEES",    C_ACCENT    ),
]

def scene5(t):
    DUR = 5.0; sa = scene_fade(t, DUR)
    img  = Image.fromarray(BG5.copy()); draw = ImageDraw.Draw(img)

    if t > 0.2:
        a = ease_out((t-0.2)/0.5)*sa
        draw_text_cs(draw, "OU L'UTILISER ?", F80, 68, C_WHITE, a)
        uw = int(640*a)
        draw.rectangle([(W-uw)//2, 162, (W+uw)//2, 168], fill=fade_c(C_GREEN, a))

    BW, BH = 350, 320; GAP = 36
    total_w = 4*BW + 3*GAP
    sx = (W - total_w)//2

    for i, (label, col) in enumerate(APPS):
        st = 0.6 + i*0.55
        if t > st:
            a  = ease_out((t-st)/0.6)*sa
            yo = int((1-ease_out(min(1.0,(t-st)/0.5)))*80)
            bx = sx + i*(BW+GAP); by = 260+yo

            box_c = lerp_c(C_DARK_GREEN, col, a*0.3)
            draw.rounded_rectangle([bx, by, bx+BW, by+BH], radius=22, fill=box_c)
            draw.rounded_rectangle([bx, by, bx+BW, by+BH], radius=22,
                                    fill=None, outline=fade_c(col, a*0.65), width=3)

            # Cercle décoratif avec initiale
            ccx = bx+BW//2; ccy = by+125
            draw.ellipse([ccx-56, ccy-56, ccx+56, ccy+56], fill=fade_c(col, a*0.85))
            init = label[0]
            bb = draw.textbbox((0,0), init, font=F80)
            draw.text((ccx-(bb[2]-bb[0])//2, ccy-(bb[3]-bb[1])//2),
                      init, font=F80, fill=fade_c(C_BLACK, a))

            bb2 = draw.textbbox((0,0), label, font=F50)
            draw.text((bx+(BW-(bb2[2]-bb2[0]))//2, by+216),
                      label, font=F50, fill=fade_c(C_WHITE, a))

    if t > 3.3:
        a = ease_out((t-3.3)/0.6)*sa
        draw_text_c(draw, "Pour toutes les surfaces dures exterieures", F50, H-140, C_ACCENT, a)

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  SCÈNE 6 — Call to action (5 s)
# ══════════════════════════════════════════════════════════════════════════════
def scene6(t):
    DUR = 5.0; sa = scene_fade(t, DUR, fi=0.55, fo=1.1)
    img  = Image.fromarray(BG6.copy()); draw = ImageDraw.Draw(img)

    # Carte centrale blanche
    CARD_H = 350; cy0 = (H - CARD_H)//2 - 25
    if t > 0.3:
        a = ease_out((t-0.3)/0.7)*sa
        draw.rounded_rectangle([145, cy0, W-145, cy0+CARD_H],
                                radius=30, fill=fade_c(C_WHITE, a*0.95))

    # Nom produit
    if t > 0.9:
        a = ease_out((t-0.9)/0.6)*sa
        draw_text_cs(draw, "DALEP 2100", F140, cy0+28, C_GREEN, a, sh=5)

    # Slogan
    if t > 1.6:
        a = ease_out((t-1.6)/0.65)*sa
        draw_text_c(draw, "La nature sous controle.", F65, cy0+183, C_DARK_GREEN, a)

    # Ligne séparatrice
    if t > 2.1:
        a = ease_out((t-2.1)/0.45)*sa
        dw = int(520*a); yline = cy0+CARD_H//2 + 80
        draw.rectangle([(W-dw)//2, yline, (W+dw)//2, yline+4], fill=fade_c(C_GREEN, a))

    # Site web
    if t > 2.5:
        a = ease_out((t-2.5)/0.6)*sa
        draw_text_c(draw, "www.dalep.com", F50, cy0+270, C_GREEN, a)

    # Pied de page
    if t > 3.1:
        a = ease_out((t-3.1)/0.7)*sa
        draw_text_c(draw, "Disponible chez votre distributeur PRO", F38, H-130, C_WHITE, a)
        draw_text_c(draw, "Bidon 5L  |  Gamme PRO  |  Made in France", F30, H-80, C_ACCENT, a)

    return apply_fade(np.array(img), sa)


# ══════════════════════════════════════════════════════════════════════════════
#  Assemblage et export
# ══════════════════════════════════════════════════════════════════════════════
SCENES = [
    (scene1, 5),
    (scene2, 6),
    (scene3, 7),
    (scene4, 8),
    (scene5, 5),
    (scene6, 5),
]

print("\nCréation des clips...")
clips = [VideoClip(fn, duration=dur) for fn, dur in SCENES]

print("Concaténation des scènes...")
final = concatenate_videoclips(clips, method="chain")

total = sum(d for _, d in SCENES)
print(f"\n{'─'*50}")
print(f"  Durée     : {total} secondes")
print(f"  Résolution: {W} × {H}")
print(f"  FPS       : {FPS}")
print(f"  Sortie    : {OUTPUT_PATH}")
print(f"{'─'*50}\n")

final.write_videofile(
    OUTPUT_PATH,
    fps=FPS,
    codec="libx264",
    audio=False,
    preset="fast",
    ffmpeg_params=["-crf", "20"],
    logger="bar",
)

print(f"\n✅  Vidéo générée : {OUTPUT_PATH}")
