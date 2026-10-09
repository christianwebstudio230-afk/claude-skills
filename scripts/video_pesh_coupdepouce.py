#!/usr/bin/env python3
"""Reel PESH Neuro-Éveil — « Les ateliers Coup de pouce parental », animé à partir du visuel carré.

La photo des mains (texte du visuel effacé) entre dans le cadre, le titre rebondit mot à mot,
le cœur se dessine, la bulle prune pousse depuis le coin, puis la bulle envahit l'écran
et ouvre sur la carte de fin.

Usage :
    python3 scripts/video_pesh_coupdepouce.py --medias <dossier> --sortie <fichier.mp4>

Le dossier médias contient mains.png (visuel 1254x1254 sans texte) et logo_disque.png.
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from video_pesh import bande_son, clamp, coeur_plein, coller, ease_back, ease_in_out, ease_out, prog, rect_arrondi

W, H, FPS = 1080, 1920, 30
TRANSITION = 1.0
PRISE = (750, 1120)  # position à l'écran du point où les mains se tiennent

MARINE = (20, 27, 69)
ROSE = (234, 30, 102)
ROSE_PILULE = (204, 90, 120)
PRUNE = (162, 72, 96)
ROSE_PALE = (250, 228, 236)
BLANC = (255, 255, 255)

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def font(nom, taille):
    fichiers = {"chewy": "Chewy.ttf", "quicksand": "Quicksand-Bold.ttf"}
    return ImageFont.truetype(os.path.join(FONTS, fichiers[nom]), taille)


def largeur(txt, police, espacement=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    return d.textlength(txt, font=police) + espacement * max(len(txt) - 1, 0)


def sprite_texte(txt, police, couleur, espacement=0):
    asc, desc = police.getmetrics()
    w = int(largeur(txt, police, espacement)) + 16
    img = Image.new("RGBA", (w, asc + desc + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = 8
    for c in (txt if espacement else [txt]):
        d.text((x, asc + 8), c, font=police, fill=couleur + (255,), anchor="ls")
        x += d.textlength(c, font=police) + espacement
    return img


def mots_rebond(calque, t, mots, police, couleur, cy, debut, decalage=0.12):
    """Mots qui rebondissent l'un après l'autre (style bouncy de la police Chewy)."""
    sps = [sprite_texte(m, police, couleur) for m in mots]
    esp = largeur(" ", police)
    total = sum(s.width - 16 for s in sps) + esp * (len(sps) - 1)
    x = W / 2 - total / 2
    for i, sp in enumerate(sps):
        p = prog(t, debut + i * decalage, 0.55)
        if p > 0:
            e = ease_back(p)
            rot = (1 - ease_out(p)) * (-12 if i % 2 else 12)
            s = sp.rotate(rot, resample=Image.BICUBIC, expand=True)
            coller(calque, s, x + (sp.width - 16) / 2, cy - (1 - ease_out(p)) * 60,
                   echelle=max(e, 0.01), alpha=clamp(p * 2.5))
        x += sp.width - 16 + esp


def coeur_trait(taille, fraction, couleur=ROSE, epaisseur=6):
    k = 3
    s = taille * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    n = 120
    pts = []
    for i in range(int(n * fraction) + 1):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((s / 2 + x * s / 38, s / 2.1 - y * s / 38))
    if len(pts) > 1:
        ImageDraw.Draw(img).line(pts, fill=couleur + (255,), width=epaisseur * k, joint="curve")
    return img.resize((taille, taille), Image.LANCZOS)


def tache(cx, cy, rayon, t, couleur, alpha=255):
    pts = []
    for i in range(90):
        a = 2 * math.pi * i / 90
        r = rayon * (1 + 0.06 * math.sin(3 * a + t * 1.2) + 0.04 * math.sin(5 * a - t * 0.9))
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    k = 2
    img = Image.new("RGBA", (W // k, H // k), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon([(x / k, y / k) for x, y in pts], fill=couleur + (alpha,))
    return img.resize((W, H), Image.BICUBIC)


class Coeurs:
    """Petits cœurs qui montent en se balançant."""

    def __init__(self, graine, n, debut):
        rng = np.random.default_rng(graine)
        self.items = [dict(sp=coeur_plein(int(rng.uniform(26, 54)), [ROSE, ROSE_PILULE, PRUNE][i % 3]),
                           x=rng.uniform(80, W - 80), y0=H + rng.uniform(20, 300), v=rng.uniform(120, 220),
                           amp=rng.uniform(20, 50), f=rng.uniform(1.2, 2.2), ph=rng.uniform(0, 6),
                           retard=debut + rng.uniform(0, 3)) for i in range(n)]

    def dessiner(self, calque, t):
        for c in self.items:
            tt = t - c["retard"]
            if tt <= 0:
                continue
            y = c["y0"] - c["v"] * tt
            if y < -60:
                continue
            x = c["x"] + c["amp"] * math.sin(tt * c["f"] + c["ph"])
            a = clamp(tt / 0.4) * clamp((y + 60) / 400)
            coller(calque, c["sp"], x, y, alpha=a)


DEF = 1.35  # résolution de travail de la photo des mains (marge pour le zoom d'entrée)


def detourer(img):
    """Contour net des mains : masque lissé (sans crénelage), bord adouci, photo accentuée."""
    k = 2
    grand = img.resize((img.width * k, img.height * k), Image.LANCZOS)
    a = np.asarray(grand).astype(np.int16)
    peau = (a.min(axis=2) < 236).astype(np.uint8) * 255
    m = Image.fromarray(peau)
    m = m.filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.MinFilter(7))  # bouche les trous
    m = m.filter(ImageFilter.MinFilter(11)).filter(ImageFilter.MaxFilter(11))  # retire les miettes
    m = m.filter(ImageFilter.GaussianBlur(10)).point(lambda v: 255 if v > 128 else 0)  # lisse le contour
    m = m.filter(ImageFilter.GaussianBlur(1.6))  # bord antialiasé
    net = grand.filter(ImageFilter.UnsharpMask(radius=2.2, percent=90, threshold=2))
    fond = Image.new("RGB", grand.size, BLANC)
    fond.paste(net, (0, 0), m)
    return fond


class Hero:
    duree = 9.6

    def __init__(self, m):
        # Pivot de 65° : le bras de l'adulte entre par le bord gauche, celui de l'enfant sort
        # par le bord droit. Les mains forment une bande horizontale adaptée au format vertical.
        src = detourer(Image.open(os.path.join(m, "mains.png")).convert("RGB"))
        ech, angle = 1.12 * DEF, 65  # bande préparée en DEF x : jamais agrandie à l'écran
        cote = int(1254 * ech)
        src = src.resize((cote, cote), Image.LANCZOS)
        self.bande = src.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=BLANC)
        dx, dy = 520 * ech - cote / 2, 900 * ech - cote / 2  # point où les mains se tiennent
        ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
        marge = int(1200 * DEF)  # fond blanc autour, pour pouvoir cadrer sans sortir de l'image
        fond = Image.new("RGB", (self.bande.width + 2 * marge, self.bande.height + 2 * marge), BLANC)
        fond.paste(self.bande, (marge, marge))
        self.prise = (marge + self.bande.width / 2 + dx * ca + dy * sa,
                      marge + self.bande.height / 2 - dx * sa + dy * ca)
        self.bande = fond
        logo = Image.open(os.path.join(m, "logo_disque.png")).convert("RGBA")
        logo.thumbnail((300, 300), Image.LANCZOS)
        self.logo = logo
        f = font("chewy", 60)
        self.pilule = rect_arrondi(int(largeur("Les ateliers", f)) + 80, 100, 34, ROSE_PILULE + (255,))
        ImageDraw.Draw(self.pilule).text((self.pilule.width / 2, 50), "Les ateliers", font=f,
                                         fill=BLANC + (255,), anchor="mm")
        self.pilule = self.pilule.rotate(2, resample=Image.BICUBIC, expand=True)
        self.f_titre = font("chewy", 156)
        fq = font("quicksand", 40)
        self.sous = [sprite_texte(l, fq, ROSE, espacement=5) for l in
                     ("DES TEMPS D'ÉCHANGE", "ET DES OUTILS POUR UN", "QUOTIDIEN PLUS SEREIN")]
        fb = font("chewy", 58)
        bulle = Image.new("RGBA", (520, 260), (0, 0, 0, 0))
        d = ImageDraw.Draw(bulle)
        for i, l in enumerate(("Parce que chaque", "parent fait de", "son mieux")):
            d.text((260, 50 + i * 72), l, font=fb, fill=BLANC + (255,), anchor="mm")
        self.bulle_txt = bulle.rotate(4, resample=Image.BICUBIC, expand=True)
        self.coeurs = Coeurs(5, 10, 5.0)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), BLANC + (255,))
        # les mains arrivent en zoom arrière autour de leur point de rencontre, puis respirent
        a = ease_out(prog(t, 0.0, 1.4))
        z = 1.25 - 0.25 * a + 0.04 * ease_in_out(t / self.duree)
        px, py = self.prise
        k = DEF / z
        box = (px - PRISE[0] * k, py - PRISE[1] * k, px + (W - PRISE[0]) * k, py + (H - PRISE[1]) * k)
        bande = self.bande.resize((W, H), Image.LANCZOS, box=box)
        img = Image.blend(img.convert("RGB"), bande, a).convert("RGBA")

        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        b = ease_back(prog(t, 0.5, 0.5))
        coller(c, self.pilule, W / 2, 240, echelle=max(b, 0.01), alpha=clamp(b * 2))
        mots_rebond(c, t, ["Coup", "de", "pouce"], self.f_titre, MARINE, 400, 0.8)
        mots_rebond(c, t, ["parental", "?"], self.f_titre, MARINE, 555, 1.2)
        for i, sp in enumerate(self.sous):
            p = ease_out(prog(t, 1.9 + i * 0.18, 0.6))
            coller(c, sp, W / 2, 690 + i * 58 + (1 - p) * 25, alpha=p)
        if t > 2.8:
            f = ease_in_out(prog(t, 2.8, 0.9))
            bat = 1 + 0.12 * max(0, math.sin((t - 3.7) * 5)) if t > 3.7 else 1
            coller(c, coeur_trait(90, f), 560, 1480, echelle=bat)
        img.alpha_composite(c)

        self.coeurs.dessiner(img, t)
        g = ease_out(prog(t, 3.4, 1.0))
        if g > 0:
            img.alpha_composite(tache(W + 80, H + 80, 640 * g, t, PRUNE))
            p = ease_back(prog(t, 4.0, 0.6))
            coller(img, self.bulle_txt, 840, 1700, echelle=max(p, 0.01), alpha=clamp(p * 2))
        p = ease_back(prog(t, 4.4, 0.6))
        coller(img, self.logo, 210, 1650, echelle=max(p, 0.01), alpha=clamp(p * 2))
        return img.convert("RGB")


class Fin:
    duree = 5.6

    def __init__(self, m):
        logo = Image.open(os.path.join(m, "logo_disque.png")).convert("RGBA")
        logo.thumbnail((400, 400), Image.LANCZOS)
        self.logo = logo
        self.f_titre = font("chewy", 118)
        fq = font("quicksand", 34)
        self.tag = [sprite_texte(l, fq, ROSE, espacement=4) for l in
                    ("COMPRENDRE · ÉCHANGER", "EXPÉRIMENTER · AVANCER")]
        f_cta = font("chewy", 70)
        bw, bh = int(largeur("Rejoignez-nous", f_cta)) + 200, 140
        self.btn = rect_arrondi(bw, bh, bh // 2, ROSE + (255,))
        self.btn.alpha_composite(coeur_plein(54, BLANC), (56, (bh - 54) // 2))
        ImageDraw.Draw(self.btn).text((bw / 2 + 34, bh / 2), "Rejoignez-nous", font=f_cta,
                                      fill=BLANC + (255,), anchor="mm")
        self.adresse = sprite_texte("13 rue de l'Arbalète · 77100 Meaux", font("quicksand", 38), MARINE)
        self.mention = sprite_texte("Infos et inscriptions : lien en bio", font("quicksand", 34), PRUNE)
        self.coeurs = Coeurs(9, 12, 0.6)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), BLANC + (255,))
        img.alpha_composite(tache(-40, -40, 360, t, ROSE_PALE))
        img.alpha_composite(tache(W + 40, H + 40, 420, t + 2, ROSE_PALE))
        a = ease_back(prog(t, 0.1, 0.7))
        coller(img, self.logo, W / 2, 450, echelle=max(a * (1 + 0.012 * math.sin(t * 2.4)), 0.01),
               alpha=clamp(a * 2))
        mots_rebond(img, t, ["Coup", "de", "pouce"], self.f_titre, MARINE, 790, 0.5, 0.1)
        mots_rebond(img, t, ["parental"], self.f_titre, MARINE, 910, 0.8)
        for i, sp in enumerate(self.tag):
            p = ease_out(prog(t, 1.2 + i * 0.15, 0.6))
            coller(img, sp, W / 2, 1040 + i * 54 + (1 - p) * 25, alpha=p)
        b = ease_back(prog(t, 1.7, 0.6))
        pulse = 1 + 0.03 * math.sin(max(0, t - 2.3) * 4)
        coller(img, self.btn, W / 2, 1290, echelle=max(b * pulse, 0.01), alpha=clamp(b * 2))
        for i, sp in enumerate((self.adresse, self.mention)):
            p = ease_out(prog(t, 2.1 + i * 0.2, 0.6))
            coller(img, sp, W / 2, 1440 + i * 64 + (1 - p) * 25, alpha=p)
        self.coeurs.dessiner(img, t)
        return img.convert("RGB")


def transition(prec, suiv, p):
    """La bulle prune grandit depuis le coin jusqu'à couvrir l'écran, puis s'ouvre sur la fin."""
    rmax = math.hypot(W, H) * 1.1
    if p < 0.5:
        base, r, (cx, cy) = prec, 640 + ease_in_out(p * 2) * rmax, (W + 80, H + 80)
    else:
        base, r, (cx, cy) = suiv, (1 - ease_in_out((p - 0.5) * 2)) * rmax, (-60, -40)
    base = base.convert("RGBA")
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(c).ellipse((cx - r, cy - r, cx + r, cy + r), fill=PRUNE + (255,))
    base.alpha_composite(c)
    return base.convert("RGB")


def rendre(m, sortie):
    scenes = [Hero(m), Fin(m)]
    debuts = [0.0, scenes[0].duree - TRANSITION]
    total = debuts[1] + scenes[1].duree
    audio = sortie + ".wav"
    bande_son(audio, total, 5)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", sortie]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(total * FPS)):
        t = i / FPS
        if t < debuts[1]:
            img = scenes[0].frame(t)
        elif t < scenes[0].duree:
            img = transition(scenes[0].frame(t), scenes[1].frame(t - debuts[1]), (t - debuts[1]) / TRANSITION)
        else:
            img = scenes[1].frame(t - debuts[1])
        ff.stdin.write(img.tobytes())
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print(f"{sortie} · {total:.1f} s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--medias", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    rendre(a.medias, a.sortie)
