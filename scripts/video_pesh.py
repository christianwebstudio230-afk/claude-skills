#!/usr/bin/env python3
"""Vidéos promotionnelles PESH' Neuro Éveil — format Reel/Story 1080x1920, 30 i/s.

Branding : kit Canva « PESH NEUROEVEIL » (logo arbre-cœur, marine + framboise,
fonds rose pâle et lavande à formes organiques, titres Fredoka, textes Montserrat).

Usage :
    python3 scripts/video_pesh.py <vocabulaire|corps> --medias <dossier> --sortie <fichier.mp4>

Le dossier médias contient logo.png (logo détouré) et les photos :
quiestce.jpg, sherlock.jpg, coloriage.jpg, materiel.jpg, twister.jpg, assise.jpg, salle.jpg.
"""
import argparse
import math
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
TRANSITION = 0.8

# Palette relevée sur le logo et les gabarits Canva PESH
MARINE = (11, 27, 77)
FRAMBOISE = (232, 8, 110)
PRUNE = (142, 20, 80)
ROSE_PALE = (252, 230, 238)
ROSE = (246, 195, 214)
LAVANDE = (234, 221, 242)
VIOLET = (156, 111, 181)
BLANC = (255, 255, 255)

ICI = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ICI, "assets", "fonts")
SLOGAN = "Comprendre · Soutenir · Faire grandir"


def font(nom, taille):
    fichiers = {
        "titre": "Fredoka-SemiBold.ttf",
        "fort": "Montserrat-ExtraBold.ttf",
        "gras": "Montserrat-Bold.ttf",
        "texte": "Montserrat-Medium.ttf",
    }
    return ImageFont.truetype(os.path.join(FONTS, fichiers[nom]), taille)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_back(x):
    x = clamp(x)
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def prog(t, debut, duree=0.7):
    return clamp((t - debut) / duree)


# ---------------------------------------------------------------- éléments graphiques
def avec_alpha(img, a):
    if a >= 1:
        return img
    img = img.copy()
    img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
    return img


def coller(calque, sprite, cx, cy, echelle=1.0, alpha=1.0):
    if echelle <= 0.01 or alpha <= 0:
        return
    if abs(echelle - 1) > 1e-3:
        sprite = sprite.resize((max(1, int(sprite.width * echelle)),
                                max(1, int(sprite.height * echelle))), Image.BICUBIC)
    sprite = avec_alpha(sprite, alpha)
    calque.alpha_composite(sprite, (int(cx - sprite.width / 2), int(cy - sprite.height / 2)))


def texte(calque, t, contenu, police, x, y, couleur, debut, ancre="lm", glisse=36,
          duree=0.7, espacement=0):
    """Texte qui apparaît en fondu + glissement vers le haut."""
    a = ease_out(prog(t, debut, duree))
    if a <= 0:
        return
    d = ImageDraw.Draw(calque)
    yy = y + (1 - a) * glisse
    fill = couleur + (int(255 * a),)
    if not espacement:
        d.text((x, yy), contenu, font=police, fill=fill, anchor=ancre)
        return
    largeur = sum(d.textlength(c, font=police) + espacement for c in contenu) - espacement
    xx = x - largeur / 2 if ancre[0] == "m" else x
    for c in contenu:
        d.text((xx, yy), c, font=police, fill=fill, anchor="l" + ancre[1])
        xx += d.textlength(c, font=police) + espacement


def coeur_points(cx, cy, s, n=120, fraction=1.0):
    pts = []
    for i in range(int(n * fraction) + 1):
        a = 2 * math.pi * i / n
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * s / 34, cy - y * s / 34))
    return pts


def coeur_trace(taille, fraction, couleur=FRAMBOISE, epaisseur=7):
    """Cœur dessiné au trait (comme les doodles des gabarits PESH), tracé progressif."""
    k = 3
    s = taille * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    if fraction > 0:
        pts = coeur_points(s / 2, s / 2, s * 0.85, fraction=fraction)
        if len(pts) > 1:
            ImageDraw.Draw(img).line(pts, fill=couleur + (255,), width=epaisseur * k, joint="curve")
    return img.resize((taille, taille), Image.LANCZOS)


def coeur_plein(taille, couleur=FRAMBOISE):
    k = 3
    s = taille * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(img).polygon(coeur_points(s / 2, s / 2, s * 0.9), fill=couleur + (255,))
    return img.resize((taille, taille), Image.LANCZOS)


def rameau(longueur=300, couleur=VIOLET):
    """Rameau de feuilles violettes (motif récurrent des visuels PESH)."""
    k = 2
    w, h = int(longueur * 0.62) * k, longueur * k
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    tige = [(w / 2 + math.sin(u * 2.4) * w * 0.08, h - u * h * 0.95) for u in np.linspace(0, 1, 40)]
    d.line(tige, fill=couleur + (255,), width=5 * k)
    for i, u in enumerate(np.linspace(0.18, 0.92, 6)):
        bx, by = tige[int(u * 39)]
        cote = 1 if i % 2 else -1
        lg, la = w * 0.38 * (1.1 - u * 0.4), w * 0.15 * (1.1 - u * 0.4)
        ang = math.radians(-40 * cote - 90)
        pts = []
        for j in range(41):
            v = j / 40
            px, py = v * lg, math.sin(math.pi * v) * la
            pts.append((px, py))
        for j in range(41):
            v = 1 - j / 40
            pts.append((v * lg, -math.sin(math.pi * v) * la))
        rot = [(bx + px * math.cos(ang) * -cote - py * math.sin(ang),
                by + px * math.sin(ang) + py * math.cos(ang)) for px, py in pts]
        d.polygon(rot, fill=couleur + (255,))
    return img.resize((w // k, h // k), Image.LANCZOS)


def pastille(contenu, police, fond=BLANC, encre=MARINE, bord=FRAMBOISE, pad=(40, 22)):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = d.textlength(contenu, font=police)
    asc, desc = police.getmetrics()
    w, h = int(tw + pad[0] * 2), int(asc + desc + pad[1] * 2)
    k = 2
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    dd = ImageDraw.Draw(img)
    dd.rounded_rectangle((0, 0, w * k - 1, h * k - 1), h * k // 2, fill=fond + (255,),
                         outline=bord + (255,) if bord else None, width=3 * k if bord else 0)
    img = img.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(img).text((w / 2, h / 2), contenu, font=police, fill=encre + (255,), anchor="mm")
    return img


class Fond:
    """Fond rose pâle avec deux formes organiques qui respirent (gabarits PESH)."""

    def __init__(self, graine):
        rng = np.random.default_rng(graine)
        self.blobs = [
            dict(cx=W * 0.92, cy=H * 0.08, r=340, c=ROSE, ph=rng.uniform(0, 6)),
            dict(cx=W * 0.04, cy=H * 0.86, r=300, c=LAVANDE, ph=rng.uniform(0, 6)),
            dict(cx=W * 1.02, cy=H * 0.62, r=170, c=LAVANDE, ph=rng.uniform(0, 6)),
        ]

    def image(self, t):
        e = 2
        img = Image.new("RGBA", (W // e, H // e), ROSE_PALE + (255,))
        d = ImageDraw.Draw(img)
        for b in self.blobs:
            pts = []
            for i in range(90):
                a = 2 * math.pi * i / 90
                r = b["r"] * (1 + 0.07 * math.sin(3 * a + t * 0.9 + b["ph"])
                              + 0.05 * math.sin(5 * a - t * 0.6 + b["ph"]))
                pts.append(((b["cx"] + r * math.cos(a)) / e,
                            (b["cy"] + r * math.sin(a) + 18 * math.sin(t * 0.7 + b["ph"])) / e))
            d.polygon(pts, fill=b["c"] + (255,))
        return img.resize((W, H), Image.BICUBIC)


def charger(chemin):
    return ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")


def cover(img, w, h, cx=0.5, cy=0.5):
    r = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
    x = int(clamp(cx * img.width - w / 2, 0, img.width - w))
    y = int(clamp(cy * img.height - h / 2, 0, img.height - h))
    return img.crop((x, y, x + w, y + h))


class Habillage:
    """Éléments communs : badge logo, pied de page (comme le gabarit Reel Canva)."""

    def __init__(self, logo):
        self.badge = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
        k = 3
        rond = Image.new("RGBA", (220 * k, 220 * k), (0, 0, 0, 0))
        ImageDraw.Draw(rond).ellipse((6 * k, 6 * k, 214 * k, 214 * k), fill=BLANC + (255,))
        self.badge.alpha_composite(rond.resize((220, 220), Image.LANCZOS))
        petit = logo.copy()
        petit.thumbnail((170, 170), Image.LANCZOS)
        self.badge.alpha_composite(petit, ((220 - petit.width) // 2, (220 - petit.height) // 2))
        self.f_pied = font("gras", 26)
        self.f_pied2 = font("texte", 26)

    def dessiner(self, calque, t, badge=True):
        if badge:
            a = ease_back(prog(t, 0.15, 0.6))
            coller(calque, self.badge, W - 150, 170, echelle=0.65 * max(a, 0.01), alpha=clamp(a))
        d = ImageDraw.Draw(calque)
        d.line((70, 1812, W - 70, 1812), fill=MARINE + (60,), width=2)
        d.text((70, 1856), "PESH NEURO-ÉVEIL", font=self.f_pied, fill=MARINE + (255,), anchor="lm")
        d.text((W - 70, 1856), SLOGAN, font=self.f_pied2, fill=MARINE + (255,), anchor="rm")


# ---------------------------------------------------------------- scènes
class Scene:
    duree = 4.0

    def frame(self, t):
        raise NotImplementedError


class Ouverture(Scene):
    """Logo qui éclot, titre du thème, pastilles de mots qui surgissent."""

    def __init__(self, duree, logo, titre, sous_titre, mots, graine):
        self.duree = duree
        self.fond = Fond(graine)
        self.logo = logo.copy()
        self.logo.thumbnail((600, 600), Image.LANCZOS)
        self.titre, self.sous_titre = titre, sous_titre
        self.f_titre = font("titre", 112)
        self.f_sous = font("gras", 34)
        self.pastilles = [pastille(m, font("gras", 40)) for m in mots]
        self.rameau = rameau(280)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        coller(c, self.rameau.rotate(18 + 4 * math.sin(t * 1.3), resample=Image.BICUBIC, expand=True),
               150, 1470, alpha=ease_out(prog(t, 0.4, 0.8)))
        a = ease_back(prog(t, 0.0, 0.9))
        coller(c, self.logo, W / 2, 520, echelle=max(a, 0.01), alpha=clamp(a * 1.4))
        for i, ligne in enumerate(self.titre):
            texte(c, t, ligne, self.f_titre, W / 2, 940 + i * 125, MARINE, 0.7 + i * 0.15, ancre="mm")
        y = 940 + len(self.titre) * 125 + 10
        texte(c, t, self.sous_titre, self.f_sous, W / 2, y, FRAMBOISE, 1.1, ancre="mm", espacement=3)
        positions = [(300, 1420), (760, 1470), (430, 1590), (800, 1640), (330, 1720)]
        for i, p in enumerate(self.pastilles):
            a = ease_back(prog(t, 1.4 + i * 0.22, 0.55))
            x, y = positions[i % len(positions)]
            y += 8 * math.sin(t * 2 + i)
            coller(c, p, x, y, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
        img.alpha_composite(c)
        return img.convert("RGB")


class Photo(Scene):
    """Gabarit Reel PESH : sur-titre, titre, sous-titre, photo en carte arrondie, étiquette."""

    def __init__(self, duree, habillage, chemin, sur_titre, titre, sous_titre, etiquette,
                 cx=0.5, cy=0.5, graine=1, zoom=(1.0, 1.1)):
        self.duree = duree
        self.hab = habillage
        self.fond = Fond(graine)
        self.sur_titre, self.titre, self.sous_titre = sur_titre, titre, sous_titre
        self.f_sur = font("gras", 30)
        self.f_titre = font("titre", 116)
        self.f_sous = font("texte", 42)
        self.cw, self.ch, self.cy0 = 940, 1110, 560
        self.photo = cover(charger(chemin), int(self.cw * 1.12), int(self.ch * 1.12), cx, cy)
        self.zoom = zoom
        k = 2
        m = Image.new("L", (self.cw * k, self.ch * k), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, self.cw * k, self.ch * k), 60 * k, fill=255)
        self.masque = m.resize((self.cw, self.ch), Image.LANCZOS)
        cadre = Image.new("RGBA", (self.cw + 80, self.ch + 80), (0, 0, 0, 0))
        ImageDraw.Draw(cadre).rounded_rectangle((40, 52, 40 + self.cw, 52 + self.ch), 60,
                                                fill=MARINE + (70,))
        self.ombre = cadre.filter(ImageFilter.GaussianBlur(22))
        self.etiquette = pastille(etiquette, font("gras", 40), fond=FRAMBOISE, encre=BLANC, bord=None)
        self.coeur = coeur_plein(40, BLANC)

    def carte(self, t):
        p = ease_in_out(t / self.duree)
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * p
        bw, bh = self.photo.size
        cw, ch = bw / 1.12 / z, bh / 1.12 / z
        box = (bw / 2 - cw / 2, bh / 2 - ch / 2, bw / 2 + cw / 2, bh / 2 + ch / 2)
        img = self.photo.resize((self.cw, self.ch), Image.BICUBIC, box=box).convert("RGBA")
        img.putalpha(self.masque)
        return img

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        texte(c, t, self.sur_titre.upper(), self.f_sur, 70, 190, FRAMBOISE, 0.1, espacement=4)
        texte(c, t, self.titre, self.f_titre, 66, 296, MARINE, 0.2, glisse=50)
        tw = ImageDraw.Draw(c).textlength(self.titre, font=self.f_titre)
        if t > 0.6:
            coller(c, coeur_trace(76, ease_in_out(prog(t, 0.6, 0.9))), 66 + tw + 60, 300)
        for i, ligne in enumerate(self.sous_titre):
            texte(c, t, ligne, self.f_sous, 70, 410 + i * 54, MARINE, 0.45 + i * 0.12)
        self.hab.dessiner(c, t)
        img.alpha_composite(c)

        a = ease_out(prog(t, 0.25, 0.8))
        if a > 0:
            s = 0.9 + 0.1 * a
            carte = Image.new("RGBA", self.ombre.size, (0, 0, 0, 0))
            carte.alpha_composite(self.ombre)
            carte.alpha_composite(self.carte(t), (40, 40))
            cy = self.cy0 + self.ch / 2 + (1 - a) * 80
            coller(img, carte, W / 2, cy, echelle=s, alpha=a)

        b = ease_back(prog(t, 1.0, 0.6))
        if b > 0:
            et = Image.new("RGBA", (self.etiquette.width + 70, self.etiquette.height), (0, 0, 0, 0))
            et.alpha_composite(self.etiquette, (70, 0))
            pill_h = self.etiquette.height
            rond = Image.new("RGBA", (pill_h, pill_h), (0, 0, 0, 0))
            ImageDraw.Draw(rond).ellipse((0, 0, pill_h - 1, pill_h - 1), fill=PRUNE + (255,))
            rond.alpha_composite(self.coeur, ((pill_h - 40) // 2, (pill_h - 38) // 2))
            et.alpha_composite(rond, (0, 0))
            et = et.rotate(4, resample=Image.BICUBIC, expand=True)
            coller(img, et, 110 + et.width / 2, self.cy0 + self.ch - 10,
                   echelle=max(b, 0.01), alpha=clamp(b * 1.5))
        return img.convert("RGB")


class Mots(Scene):
    """Typographie cinétique : un verbe, puis le vocabulaire qui s'empile en pastilles."""

    def __init__(self, duree, habillage, sur_titre, titre, mots, phrase, graine):
        self.duree = duree
        self.hab = habillage
        self.fond = Fond(graine)
        self.sur_titre, self.titre, self.phrase = sur_titre, titre, phrase
        self.f_sur = font("gras", 30)
        self.f_titre = font("titre", 150)
        self.f_phrase = font("titre", 56)
        self.mots = [pastille(m, font("gras", 50), pad=(48, 26)) for m in mots]
        self.rameau = rameau(300)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        coller(c, self.rameau.rotate(-20 + 4 * math.sin(t * 1.2), resample=Image.BICUBIC,
                                     expand=True), W - 140, 1450, alpha=ease_out(prog(t, 0.3, 0.8)))
        texte(c, t, self.sur_titre.upper(), self.f_sur, W / 2, 360, FRAMBOISE, 0.0, ancre="mm",
              espacement=4)
        a = ease_back(prog(t, 0.1, 0.6))
        if a > 0:
            sp = Image.new("RGBA", (W, 220), (0, 0, 0, 0))
            ImageDraw.Draw(sp).text((W / 2, 110), self.titre, font=self.f_titre, fill=MARINE + (255,),
                                    anchor="mm")
            coller(c, sp, W / 2, 500, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
        for i, m in enumerate(self.mots):
            a = ease_back(prog(t, 0.6 + i * 0.28, 0.5))
            dx = (-1) ** i * 110
            y = 720 + i * 135 + 6 * math.sin(t * 2.2 + i)
            coller(c, m, W / 2 + dx, y, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
        y = 720 + len(self.mots) * 135 + 40
        for i, ligne in enumerate(self.phrase):
            texte(c, t, ligne, self.f_phrase, W / 2, y + i * 72, PRUNE,
                  0.8 + len(self.mots) * 0.28 + i * 0.15, ancre="mm")
        self.hab.dessiner(c, t)
        img.alpha_composite(c)
        return img.convert("RGB")


class Cloture(Scene):
    """Carte de fin : logo, promesse, lieu, bouton « Rejoignez-nous »."""

    def __init__(self, duree, logo, phrase, graine):
        self.duree = duree
        self.fond = Fond(graine)
        self.logo = logo.copy()
        self.logo.thumbnail((520, 520), Image.LANCZOS)
        self.phrase = phrase
        self.f_phrase = font("titre", 74)
        self.f_slogan = font("gras", 32)
        self.f_info = font("texte", 36)
        self.f_cta = font("titre", 60)
        self.f_tags = font("gras", 30)
        self.coeur = coeur_plein(54, BLANC)
        self.rameau = rameau(260)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        coller(c, self.rameau.rotate(15 + 4 * math.sin(t * 1.3), resample=Image.BICUBIC, expand=True),
               130, 560, alpha=ease_out(prog(t, 0.4, 0.8)))
        a = ease_back(prog(t, 0.0, 0.8))
        coller(c, self.logo, W / 2, 470, echelle=max(a * (1 + 0.015 * math.sin(t * 2.5)), 0.01),
               alpha=clamp(a * 1.4))
        texte(c, t, SLOGAN.upper(), self.f_slogan, W / 2, 790, FRAMBOISE, 0.5, ancre="mm", espacement=2)
        for i, ligne in enumerate(self.phrase):
            texte(c, t, ligne, self.f_phrase, W / 2, 920 + i * 92, MARINE, 0.7 + i * 0.15, ancre="mm")
        y = 920 + len(self.phrase) * 92 + 50
        texte(c, t, "Association · enfants, adultes et familles", self.f_info, W / 2, y, MARINE, 1.1,
              ancre="mm")
        texte(c, t, "11 rue de l'Arbalète · 77100 Meaux", self.f_info, W / 2, y + 56, MARINE, 1.2,
              ancre="mm")
        b = ease_back(prog(t, 1.6, 0.6))
        if b > 0:
            pulse = 1 + 0.025 * math.sin(max(0, t - 2.2) * 4)
            d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
            tw = d.textlength("Rejoignez-nous", font=self.f_cta)
            bw, bh = int(tw + 200), 140
            k = 2
            btn = Image.new("RGBA", (bw * k, bh * k), (0, 0, 0, 0))
            ImageDraw.Draw(btn).rounded_rectangle((0, 0, bw * k, bh * k), bh * k // 2,
                                                  fill=FRAMBOISE + (255,))
            btn = btn.resize((bw, bh), Image.LANCZOS)
            btn.alpha_composite(self.coeur, (52, (bh - 52) // 2))
            ImageDraw.Draw(btn).text((bw / 2 + 36, bh / 2), "Rejoignez-nous", font=self.f_cta,
                                     fill=BLANC + (255,), anchor="mm")
            coller(c, btn, W / 2, y + 230, echelle=max(b * pulse, 0.01), alpha=clamp(b * 1.5))
        texte(c, t, "Adhésion et inscriptions sur HelloAsso", self.f_info, W / 2, y + 360, PRUNE, 2.1,
              ancre="mm")
        texte(c, t, "#PESHNeuroEveil  #Meaux", self.f_tags, W / 2, y + 430, FRAMBOISE, 2.3, ancre="mm")
        img.alpha_composite(c)
        return img.convert("RGB")


# ---------------------------------------------------------------- montages
def montage(nom, m):
    p = lambda n: os.path.join(m, n)  # noqa: E731
    logo = Image.open(p("logo.png")).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    hab = Habillage(logo)
    if nom == "vocabulaire":
        return [
            Ouverture(3.8, logo, ["Vocabulaire", "& observation"], "APPRENDRE EN JOUANT",
                      ["Il a des lunettes ?", "Elle sourit ?", "Cheveux bouclés ?"], 1),
            Photo(4.3, hab, p("quiestce.jpg"), "Observation", "Observer",
                  ["Poser des questions,", "repérer les détails."], "Qui est-ce ?", cy=0.45, graine=2),
            Photo(4.3, hab, p("sherlock.jpg"), "Lecture", "Enquêter",
                  ["Lire, chercher les indices,", "raconter avec ses mots."], "P'tit Sherlock",
                  cy=0.45, graine=3),
            Mots(4.0, hab, "Vocabulaire", "Décrire", ["rouge", "plus long que", "à côté de", "lisse"],
                 ["Mettre des mots", "sur ce que l'on voit."], 4),
            Photo(4.3, hab, p("coloriage.jpg"), "Motricité fine", "Nommer",
                  ["Choisir ses couleurs,", "les nommer, soigner son geste."], "Atelier créatif",
                  cy=0.5, graine=5),
            Photo(4.0, hab, p("materiel.jpg"), "Outils adaptés", "Manipuler",
                  ["Jeux, puzzles, laçages", "et minuteur visuel."], "Matériel adapté", cy=0.55,
                  graine=6),
            Cloture(5.8, logo, ["Révéler le potentiel", "de chaque enfant"], 7),
        ]
    return [
        Ouverture(3.8, logo, ["Apprivoiser", "son corps"], "SE REPÉRER · BOUGER · S'AJUSTER",
                  ["droite", "gauche", "devant", "derrière"], 11),
        Photo(4.4, hab, p("twister.jpg"), "Schéma corporel", "Se repérer",
              ["Main droite sur le rouge !", "Latéralité, équilibre, coordination."], "Twister",
              cy=0.5, graine=12),
        Mots(4.2, hab, "Vocabulaire du corps", "Nommer",
             ["la tête", "les épaules", "les genoux", "les pieds"],
             ["Mettre des mots", "sur son propre corps."], 13),
        Photo(4.4, hab, p("assise.jpg"), "Appréhension du corps", "S'ajuster",
              ["Coussin d'assise, élastique aux pieds :", "le corps trouve sa place."],
              "Assise dynamique", cy=0.4, graine=14),
        Photo(4.4, hab, p("salle.jpg"), "Notre espace à Meaux", "Un lieu",
              ["pensé pour travailler,", "bouger et se poser."], "Accueil adapté", cx=0.6, cy=0.5,
              graine=15, zoom=(1.0, 1.06)),
        Cloture(5.8, logo, ["Chaque enfant", "a son potentiel"], 16),
    ]


# ---------------------------------------------------------------- audio
def bande_son(chemin, duree, graine):
    """Nappe douce + petites notes pincées, générées (aucun droit musical)."""
    sr = 44100
    n = int(duree * sr)
    t = np.arange(n) / sr
    accords = [[261.63, 329.63, 392.00], [220.00, 261.63, 329.63],
               [174.61, 220.00, 261.63], [196.00, 246.94, 293.66]]
    if graine % 2 == 0:
        accords = accords[2:] + accords[:2]
    out = np.zeros(n)
    seg = duree / 6
    for i in range(7):
        acc = accords[i % 4]
        debut = i * seg
        fin = min(duree, debut + seg + 1.2)
        if debut >= duree:
            break
        a, b = int(debut * sr), int(fin * sr)
        tt = t[a:b] - debut
        env = np.minimum(1, tt / 0.9) * np.minimum(1, (fin - debut - tt) / 1.2)
        for f in acc:
            out[a:b] += 0.5 * np.sin(2 * math.pi * f * tt) * env
            out[a:b] += 0.2 * np.sin(2 * math.pi * f / 2 * tt) * env
        # arpège pincé, 2 notes par temps à ~96 bpm
        pas = 60 / 96 / 2
        for j in range(int(seg / pas) + 1):
            f = acc[j % 3] * (2 if j % 4 < 2 else 4)
            d0 = debut + j * pas
            if d0 >= duree - 0.5:
                break
            a2 = int(d0 * sr)
            tn = np.arange(int(0.6 * sr)) / sr
            note = np.sin(2 * math.pi * f * tn) * np.exp(-tn * 7) * 0.22
            out[a2:a2 + len(tn)] += note[: max(0, min(len(tn), n - a2))]
    out *= np.minimum(1, t / 1.0) * np.minimum(1, (duree - t) / 1.8)
    out = out / np.max(np.abs(out)) * 0.5
    st = np.stack([out, np.roll(out, 400)], axis=1)
    with wave.open(chemin, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- rendu
def transition(prec, suiv, p):
    """Volet circulaire rose : un disque couvre l'image puis se retire sur la suivante."""
    rmax = math.hypot(W, H)
    if p < 0.5:
        base, r, centre = prec, ease_in_out(p * 2) * rmax, (0, H)
    else:
        base, r, centre = suiv, (1 - ease_in_out((p - 0.5) * 2)) * rmax, (W, 0)
    base = base.convert("RGBA")
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    cx, cy = centre
    d.ellipse((cx - r * 1.08, cy - r * 1.08, cx + r * 1.08, cy + r * 1.08), fill=LAVANDE + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ROSE + (255,))
    base.alpha_composite(c)
    return base.convert("RGB")


def rendre(scenes, sortie, graine):
    debuts, t0 = [], 0.0
    for s in scenes:
        debuts.append(t0)
        t0 += s.duree - TRANSITION
    total = t0 + TRANSITION
    audio = sortie + ".wav"
    bande_son(audio, total, graine)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", sortie]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nb = int(total * FPS)
    for i in range(nb):
        t = i / FPS
        actives = [(k, t - debuts[k]) for k, s in enumerate(scenes)
                   if debuts[k] <= t < debuts[k] + s.duree]
        k, tl = actives[-1]
        if len(actives) > 1 and tl < TRANSITION:
            kp, tlp = actives[-2]
            img = transition(scenes[kp].frame(tlp), scenes[k].frame(tl), tl / TRANSITION)
        else:
            img = scenes[k].frame(tl)
        ff.stdin.write(img.tobytes())
        if i % 90 == 0:
            print(f"  {i}/{nb}", file=sys.stderr, flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print(f"{sortie} · {total:.1f} s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("theme", choices=["vocabulaire", "corps"])
    ap.add_argument("--medias", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    rendre(montage(a.theme, a.medias), a.sortie, 1 if a.theme == "vocabulaire" else 2)
