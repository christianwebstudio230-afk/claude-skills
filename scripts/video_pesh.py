#!/usr/bin/env python3
"""Vidéos promotionnelles PESH Neuro-Éveil — format Reel/Story 1080x1920, 30 i/s.

Charte : planche de marque Canva PESH (palette #21284A · #AA4879 · #F5367A · #FFDAE9 ·
#F7C3D4 · #8E7CAC) et composants de l'agenda mensuel : fond dégradé soyeux, carte blanche
à lignes, neurones roses, titres Montserrat ExtraBold, pied de page
« Comprendre · Échanger · Expérimenter · Avancer ».

Usage :
    python3 scripts/video_pesh.py <vocabulaire|corps|matinee> --medias <dossier> --sortie <fichier.mp4>

Le dossier médias contient logo_disque.png (logo officiel sur disque blanc) et les photos :
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

# Palette officielle (planche de marque Canva)
MARINE = (33, 40, 74)
MAUVE = (170, 72, 121)
ROSE_VIF = (245, 54, 122)
ROSE_PALE = (255, 218, 233)
ROSE = (247, 195, 212)
LAVANDE = (142, 124, 172)
SAUGE = (163, 179, 155)
BLANC = (255, 255, 255)
GRIS_LIGNE = (236, 222, 229)

ICI = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ICI, "assets", "fonts")
SIGNATURE = "Comprendre · Échanger · Expérimenter · Avancer"
SLOGAN = "ACCOMPAGNER · SOUTENIR · FAIRE GRANDIR"
ADRESSE = "13 rue de l'Arbalète · 77100 Meaux"


def font(nom, taille):
    fichiers = {"titre": "Montserrat-ExtraBold.ttf", "gras": "Montserrat-Bold.ttf",
                "texte": "Montserrat-Medium.ttf"}
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


# ---------------------------------------------------------------- primitives
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
    calque.alpha_composite(avec_alpha(sprite, alpha),
                           (int(cx - sprite.width / 2), int(cy - sprite.height / 2)))


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


def texte_riche(calque, segments, x, y, alpha):
    """Ligne composée de segments (texte, police, couleur) — mots clés en rose gras."""
    d = ImageDraw.Draw(calque)
    for contenu, police, couleur in segments:
        d.text((x, y), contenu, font=police, fill=couleur + (int(255 * alpha),), anchor="ls")
        x += d.textlength(contenu, font=police)


def rect_arrondi(w, h, r, couleur, k=2):
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w * k - 1, h * k - 1), r * k, fill=couleur)
    return img.resize((w, h), Image.LANCZOS)


def coeur_plein(taille, couleur=ROSE_VIF):
    k = 3
    s = taille * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = []
    for i in range(120):
        a = 2 * math.pi * i / 120
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((s / 2 + x * s / 36, s / 2.1 - y * s / 36))
    ImageDraw.Draw(img).polygon(pts, fill=couleur + (255,))
    return img.resize((taille, taille), Image.LANCZOS)


def pastille(contenu, police, fond=BLANC, encre=MARINE, bord=ROSE_VIF, pad=(40, 22)):
    d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    tw = d.textlength(contenu, font=police)
    asc, desc = police.getmetrics()
    w, h = int(tw + pad[0] * 2), int(asc + desc + pad[1] * 2)
    k = 2
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        (0, 0, w * k - 1, h * k - 1), h * k // 2, fill=fond + (255,),
        outline=bord + (255,) if bord else None, width=3 * k if bord else 0)
    img = img.resize((w, h), Image.LANCZOS)
    ImageDraw.Draw(img).text((w / 2, h / 2), contenu, font=police, fill=encre + (255,), anchor="mm")
    return img


def charger(chemin):
    return ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")


def cover(img, w, h, cx=0.5, cy=0.5):
    r = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
    x = int(clamp(cx * img.width - w / 2, 0, img.width - w))
    y = int(clamp(cy * img.height - h / 2, 0, img.height - h))
    return img.crop((x, y, x + w, y + h))


# ---------------------------------------------------------------- fond et décor
class Fond:
    """Dégradé rose poudré → blanc → gris perle, avec voiles soyeux qui ondulent (agenda)."""

    E = 4  # rendu des voiles en basse résolution puis agrandi : bords très doux

    def __init__(self, graine):
        rng = np.random.default_rng(graine)
        yy, xx = np.mgrid[0:H // self.E, 0:W // self.E].astype(float)
        u = (xx / (W / self.E) * 0.45 + yy / (H / self.E) * 0.55)
        haut = np.array([236, 205, 216], float)
        milieu = np.array([250, 243, 246], float)
        bas = np.array([232, 232, 237], float)
        u3 = u[..., None]
        grad = np.where(u3 < 0.5, haut + (milieu - haut) * (u3 / 0.5),
                        milieu + (bas - milieu) * ((u3 - 0.5) / 0.5))
        self.base = Image.fromarray(grad.astype(np.uint8), "RGB").convert("RGBA")
        self.voiles = [
            dict(cx=0.05, cy=0.18, rx=0.75, ry=0.32, c=(214, 160, 182, 120), ph=rng.uniform(0, 6)),
            dict(cx=0.55, cy=0.05, rx=0.55, ry=0.22, c=(255, 255, 255, 150), ph=rng.uniform(0, 6)),
            dict(cx=0.95, cy=0.80, rx=0.6, ry=0.28, c=(214, 214, 224, 140), ph=rng.uniform(0, 6)),
            dict(cx=0.1, cy=0.95, rx=0.5, ry=0.2, c=(247, 195, 212, 110), ph=rng.uniform(0, 6)),
        ]

    def image(self, t):
        e = self.E
        img = self.base.copy()
        c = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        for v in self.voiles:
            cx = (v["cx"] + 0.03 * math.sin(t * 0.5 + v["ph"])) * W / e
            cy = (v["cy"] + 0.02 * math.cos(t * 0.4 + v["ph"])) * H / e
            rx, ry = v["rx"] * W / e, v["ry"] * H / e
            ang = 0.5 + 0.06 * math.sin(t * 0.3 + v["ph"])
            pts = [(cx + rx * math.cos(a) * math.cos(ang) - ry * math.sin(a) * math.sin(ang),
                    cy + rx * math.cos(a) * math.sin(ang) + ry * math.sin(a) * math.cos(ang))
                   for a in np.linspace(0, 2 * math.pi, 60)]
            d.polygon(pts, fill=v["c"])
        c = c.filter(ImageFilter.GaussianBlur(14))
        img.alpha_composite(c)
        return img.resize((W, H), Image.BICUBIC)


class Neurone:
    """Neurone stylisé de l'agenda : corps marine, dendrites qui poussent, extrémités roses."""

    def __init__(self, taille, graine, halo=False):
        rng = np.random.default_rng(graine)
        self.taille, self.halo = taille, halo
        self.branches = []
        n = 7
        for i in range(n):
            ang = 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
            lg = rng.uniform(0.32, 0.45)
            fils = [(ang + rng.uniform(0.35, 0.6) * s, lg * rng.uniform(0.35, 0.55)) for s in (-1, 1)]
            self.branches.append((ang, lg, fils))
        self.cache = None

    def sprite(self, g):
        if g >= 1 and self.cache is not None:
            return self.cache
        k = 2
        s = self.taille * k
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        c = s / 2
        if self.halo:
            r = s * 0.42 * ease_out(g * 1.5)
            d.ellipse((c - r, c - r, c + r, c + r), fill=(242, 205, 220, 170))

        def goutte(x, y, ang, r):
            pts = []
            for j in range(24):
                a = 2 * math.pi * j / 24
                lx = r * math.cos(a) * (1.6 if math.cos(a) > 0 else 1.0)
                ly = r * 0.75 * math.sin(a)
                pts.append((x + lx * math.cos(ang) - ly * math.sin(ang),
                            y + lx * math.sin(ang) + ly * math.cos(ang)))
            d.polygon(pts, fill=ROSE_VIF + (255,))

        for ang, lg, fils in self.branches:
            p = clamp(g * 1.6)
            x1, y1 = c + math.cos(ang) * lg * s * p, c + math.sin(ang) * lg * s * p
            d.line((c, c, x1, y1), fill=(63, 74, 122, 255), width=3 * k)
            if g > 0.55:
                q = clamp((g - 0.55) / 0.45)
                for fa, fl in fils:
                    x2 = x1 + math.cos(fa) * fl * s * q
                    y2 = y1 + math.sin(fa) * fl * s * q
                    d.line((x1, y1, x2, y2), fill=(63, 74, 122, 255), width=2 * k)
                    if q > 0.7:
                        goutte(x2, y2, fa, 7 * k * clamp((q - 0.7) / 0.3))
            if p >= 1:
                goutte(x1 + math.cos(ang) * 6 * k, y1 + math.sin(ang) * 6 * k, ang, 8 * k)
        r = 13 * k * ease_out(g * 3)
        d.ellipse((c - r * 1.6, c - r * 1.6, c + r * 1.6, c + r * 1.6), fill=(142, 124, 172, 110))
        d.ellipse((c - r, c - r, c + r, c + r), fill=(63, 74, 122, 255))
        out = img.resize((self.taille, self.taille), Image.LANCZOS)
        if g >= 1:
            self.cache = out
        return out

    def dessiner(self, calque, t, cx, cy, debut=0.0):
        g = prog(t, debut, 1.2)
        if g <= 0:
            return
        sp = self.sprite(g).rotate(6 * math.sin(t * 0.8), resample=Image.BICUBIC)
        coller(calque, sp, cx, cy, echelle=1 + 0.03 * math.sin(t * 2))


def serpentin_sprite(couleur, longueur, graine):
    """Serpentin bouclé (ressort aplati), dessiné en 2x puis réduit pour l'antialias."""
    rng = np.random.default_rng(graine)
    k = 2
    R = rng.uniform(16, 24)
    pas = rng.uniform(10, 15)
    n = int(longueur / pas * 6)
    pts = []
    for i in range(n):
        th = i / 6 * 2 * math.pi
        pts.append((R * math.sin(th), i / 6 * pas + R * 0.45 * math.cos(th)))
    xs, ys = zip(*pts)
    w, h = int(max(xs) - min(xs) + 30), int(max(ys) - min(ys) + 30)
    img = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    pts = [((x - min(xs) + 15) * k, (y - min(ys) + 15) * k) for x, y in pts]
    ImageDraw.Draw(img).line(pts, fill=couleur + (255,), width=4 * k, joint="curve")
    return img.resize((w, h), Image.LANCZOS)


class Fete:
    """Confettis et serpentins tirés depuis les coins bas, puis qui retombent en voletant."""

    COULEURS = [ROSE_VIF, MAUVE, ROSE, LAVANDE, MARINE, SAUGE, (255, 196, 92)]

    def __init__(self, graine, n=110, n_serp=6, debut=0.2):
        rng = np.random.default_rng(graine)
        self.debut = debut
        self.conf = []
        for i in range(n):
            gauche = i % 2 == 0
            ang = math.radians(rng.uniform(55, 85))
            v = rng.uniform(1500, 2300)
            self.conf.append(dict(
                x=-20 if gauche else W + 20, y=H * rng.uniform(0.7, 0.85),
                vx=(1 if gauche else -1) * math.cos(ang) * v, vy=-math.sin(ang) * v,
                c=self.COULEURS[rng.integers(len(self.COULEURS))], w=rng.uniform(12, 22),
                h=rng.uniform(7, 12), rot=rng.uniform(0, 6.28), vrot=rng.uniform(-9, 9),
                fl=rng.uniform(2, 5), rond=rng.random() < 0.3, retard=rng.uniform(0, 0.25)))
        self.serp = []
        for i in range(n_serp):
            gauche = i % 2 == 0
            ang = math.radians(rng.uniform(60, 80))
            v = rng.uniform(1300, 1900)
            self.serp.append(dict(
                sp=serpentin_sprite(self.COULEURS[i % 4], rng.uniform(160, 260), i + graine),
                x=-20 if gauche else W + 20, y=H * rng.uniform(0.72, 0.85),
                vx=(1 if gauche else -1) * math.cos(ang) * v, vy=-math.sin(ang) * v,
                rot=rng.uniform(-40, 40), vrot=rng.uniform(-60, 60), retard=rng.uniform(0, 0.2)))

    @staticmethod
    def trajectoire(p, t):
        """Projection freinée puis chute lente avec flottement (terminal velocity)."""
        k, g, vterm = 2.2, 1400.0, 260.0
        e = math.exp(-k * t)
        x = p["x"] + p["vx"] / k * (1 - e)
        y = p["y"] + p["vy"] / k * (1 - e) + min(g * t * t / 2, vterm * t)
        return x, y

    def dessiner(self, calque, t):
        tt = t - self.debut
        if tt <= 0:
            return
        d = ImageDraw.Draw(calque)
        for p in self.conf:
            tp = tt - p["retard"]
            if tp <= 0:
                continue
            x, y = self.trajectoire(p, tp)
            x += math.sin(tp * p["fl"]) * 25
            if y > H + 40:
                continue
            if p["rond"]:
                r = p["h"] * 0.7
                d.ellipse((x - r, y - r, x + r, y + r), fill=p["c"] + (255,))
                continue
            a = p["rot"] + p["vrot"] * tp
            sc = abs(math.cos(tp * p["fl"] * 1.3))  # effet de rotation 3D
            w, h = p["w"] / 2, p["h"] / 2 * (0.25 + 0.75 * sc)
            ca, sa = math.cos(a), math.sin(a)
            pts = [(x + dx * ca - dy * sa, y + dx * sa + dy * ca)
                   for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
            d.polygon(pts, fill=p["c"] + (255,))
        for s in self.serp:
            tp = tt - s["retard"]
            if tp <= 0:
                continue
            x, y = self.trajectoire(s, tp)
            x += math.sin(tp * 2) * 30
            if y > H + 200:
                continue
            sp = s["sp"].rotate(s["rot"] + s["vrot"] * tp, resample=Image.BICUBIC, expand=True)
            coller(calque, sp, x, y)


class Habillage:
    """Badge logo, pied de page signature (gabarits agenda / Reel)."""

    def __init__(self, logo_disque):
        self.logo = logo_disque
        ombre = Image.new("RGBA", (logo_disque.width + 60, logo_disque.height + 60), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).ellipse((30, 40, 30 + logo_disque.width, 40 + logo_disque.height),
                                      fill=MARINE + (50,))
        self.ombre = ombre.filter(ImageFilter.GaussianBlur(18))
        self.f_pied = font("gras", 30)

    def badge(self, taille):
        b = self.ombre.copy()
        b.alpha_composite(self.logo, (30, 30))
        return b.resize((int(taille * b.width / self.logo.width),
                         int(taille * b.height / self.logo.height)), Image.LANCZOS)

    def dessiner(self, calque, t, badge=True):
        if badge:
            if not hasattr(self, "_badge"):
                self._badge = self.badge(210)
            a = ease_back(prog(t, 0.15, 0.6))
            coller(calque, self._badge, W - 155, 175, echelle=max(a, 0.01), alpha=clamp(a))
        d = ImageDraw.Draw(calque)
        d.text((W / 2, 1800), SIGNATURE, font=self.f_pied, fill=ROSE_VIF + (255,), anchor="mm")
        d.line((70, 1850, W - 70, 1850), fill=MAUVE + (90,), width=2)


# ---------------------------------------------------------------- scènes
class Scene:
    duree = 4.0

    def frame(self, t):
        raise NotImplementedError


class Ouverture(Scene):
    """Logo officiel qui éclot dans une pluie de confettis, titre et mots-clés."""

    def __init__(self, duree, hab, sur_titre, titre, mots, graine):
        self.duree = duree
        self.hab = hab
        self.fond = Fond(graine)
        self.logo = hab.badge(560)
        self.sur_titre, self.titre = sur_titre, titre
        self.f_sur = font("gras", 34)
        self.f_titre = font("titre", 108)
        self.pastilles = [pastille(m, font("gras", 40)) for m in mots]
        self.fete = Fete(graine, debut=0.35)
        self.neurone = Neurone(300, graine, halo=True)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.neurone.dessiner(c, t, 120, 1640, debut=1.0)
        self.fete.dessiner(c, t)
        a = ease_back(prog(t, 0.0, 0.9))
        coller(c, self.logo, W / 2, 500, echelle=max(a, 0.01), alpha=clamp(a * 1.4))
        texte(c, t, self.sur_titre, self.f_sur, W / 2, 870, ROSE_VIF, 0.6, ancre="mm", espacement=3)
        for i, ligne in enumerate(self.titre):
            texte(c, t, ligne, self.f_titre, W / 2, 990 + i * 120, MARINE, 0.75 + i * 0.15, ancre="mm")
        positions = [(300, 1330), (770, 1380), (430, 1500), (800, 1550)]
        for i, p in enumerate(self.pastilles):
            a = ease_back(prog(t, 1.4 + i * 0.22, 0.55))
            x, y = positions[i % len(positions)]
            coller(c, p, x, y + 8 * math.sin(t * 2 + i), echelle=max(a, 0.01), alpha=clamp(a * 1.5))
        self.hab.dessiner(c, t, badge=False)
        img.alpha_composite(c)
        return img.convert("RGB")


class Photo(Scene):
    """Sur-titre rose, titre capitales marine, sous-titre mauve, photo en carte blanche."""

    def __init__(self, duree, hab, chemin, sur_titre, titre, sous_titre, etiquette,
                 cx=0.5, cy=0.5, graine=1, zoom=(1.0, 1.1), ch=1080):
        self.duree = duree
        self.hab = hab
        self.fond = Fond(graine)
        self.sur_titre, self.titre, self.sous_titre = sur_titre, titre, sous_titre
        self.f_sur = font("gras", 32)
        taille = 100
        while ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(
                titre.upper(), font=font("titre", taille)) > 760:
            taille -= 4  # le titre ne doit pas toucher le badge logo
        self.f_titre = font("titre", taille)
        self.f_sous = font("gras", 40)
        self.cw, self.ch, self.cy0 = 900, ch, 590
        self.photo = cover(charger(chemin), int(self.cw * 1.12), int(self.ch * 1.12), cx, cy)
        self.centre = (cx, cy)
        self.zoom = zoom
        k = 2
        m = Image.new("L", (self.cw * k, self.ch * k), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, self.cw * k, self.ch * k), 34 * k, fill=255)
        self.masque = m.resize((self.cw, self.ch), Image.LANCZOS)
        b = 18  # cadre blanc, comme la carte de l'agenda
        cadre = Image.new("RGBA", (self.cw + 2 * b + 80, self.ch + 2 * b + 80), (0, 0, 0, 0))
        ImageDraw.Draw(cadre).rounded_rectangle((40, 54, 40 + self.cw + 2 * b, 54 + self.ch + 2 * b),
                                                48, fill=MARINE + (55,))
        cadre = cadre.filter(ImageFilter.GaussianBlur(22))
        cadre.alpha_composite(rect_arrondi(self.cw + 2 * b, self.ch + 2 * b, 48, BLANC + (255,)),
                              (40, 40))
        self.cadre, self.bord = cadre, b
        self.etiquette = pastille(etiquette, font("gras", 38), fond=ROSE_VIF, encre=BLANC, bord=None)
        self.coeur = coeur_plein(36, BLANC)
        self.neurone = Neurone(230, graine)

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
        texte(c, t, self.sur_titre.upper(), self.f_sur, 80, 160, ROSE_VIF, 0.1, espacement=3)
        texte(c, t, self.titre.upper(), self.f_titre, 74, 280, MARINE, 0.2, glisse=50)
        for i, ligne in enumerate(self.sous_titre):
            texte(c, t, ligne, self.f_sous, 80, 400 + i * 54, MAUVE, 0.45 + i * 0.12)
        self.hab.dessiner(c, t)
        img.alpha_composite(c)

        a = ease_out(prog(t, 0.25, 0.8))
        if a > 0:
            carte = self.cadre.copy()
            carte.alpha_composite(self.carte(t), (40 + self.bord, 40 + self.bord))
            cy = self.cy0 + self.ch / 2 + (1 - a) * 80
            coller(img, carte, W / 2, cy, echelle=0.9 + 0.1 * a, alpha=a)

        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.neurone.dessiner(c, t, W - 95, self.cy0 + 40, debut=0.7)
        b = ease_back(prog(t, 1.0, 0.6))
        if b > 0:
            ph = self.etiquette.height
            et = Image.new("RGBA", (self.etiquette.width + ph - 10, ph), (0, 0, 0, 0))
            et.alpha_composite(self.etiquette, (ph - 10, 0))
            rond = Image.new("RGBA", (ph, ph), (0, 0, 0, 0))
            ImageDraw.Draw(rond).ellipse((0, 0, ph - 1, ph - 1), fill=MAUVE + (255,))
            rond.alpha_composite(self.coeur, ((ph - 36) // 2, (ph - 34) // 2))
            et.alpha_composite(rond, (0, 0))
            et = et.rotate(3, resample=Image.BICUBIC, expand=True)
            coller(c, et, 110 + et.width / 2, self.cy0 + self.ch + 8,
                   echelle=max(b, 0.01), alpha=clamp(b * 1.5))
        img.alpha_composite(c)
        return img.convert("RGB")


class PhotoDecrire(Photo):
    """Décrire une vraie photo : des bulles pointent ce que l'on voit, puis la phrase se construit."""

    def __init__(self, duree, hab, chemin, reperes, phrase, sur_titre="Vocabulaire",
                 titre="Décrire", sous_titre=("Regarder, nommer,", "puis faire une phrase."),
                 etiquette="Je décris", **kw):
        super().__init__(duree, hab, chemin, sur_titre, titre, list(sous_titre), etiquette, **kw)
        src = charger(chemin)
        self.taille_src = src.size
        self.reperes = reperes  # (texte, (x, y) en pixels source, (bx, by) position de la bulle)
        self.bulles = [pastille(txt, font("gras", 38)) for txt, _, _ in reperes]
        self.phrase = phrase
        self.f_txt = font("titre", 50)

    def vers_ecran(self, x, y):
        """Pixel de la photo source → position à l'écran (même recadrage que cover())."""
        sw, sh = self.taille_src
        bw, bh = self.photo.size
        r = max(bw / sw, bh / sh)
        cx, cy = self.centre
        ox = clamp(cx * sw * r - bw / 2, 0, sw * r - bw)
        oy = clamp(cy * sh * r - bh / 2, 0, sh * r - bh)
        u, v = (x * r - ox) / bw, (y * r - oy) / bh
        u, v = (u - 0.5) * 1.12 + 0.5, (v - 0.5) * 1.12 + 0.5
        return W / 2 - self.cw / 2 + u * self.cw, self.cy0 + v * self.ch

    def frame(self, t):
        img = super().frame(t).convert("RGBA")
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(c)
        for i, ((_, (x, y), (bx, by)), bulle) in enumerate(zip(self.reperes, self.bulles)):
            debut = 1.2 + i * 0.55
            px, py = self.vers_ecran(x, y)
            g = ease_out(prog(t, debut, 0.35))
            if g <= 0:
                continue
            by = self.cy0 + by
            d.line((px, py, px + (bx - px) * g, py + (by - py) * g), fill=BLANC + (255,), width=4)
            r = 13 * ease_back(prog(t, debut, 0.3))
            d.ellipse((px - r - 5, py - r - 5, px + r + 5, py + r + 5), fill=BLANC + (255,))
            d.ellipse((px - r, py - r, px + r, py + r), fill=ROSE_VIF + (255,))
            b = ease_back(prog(t, debut + 0.25, 0.45))
            coller(c, bulle, bx, by, echelle=max(b, 0.01), alpha=clamp(b * 1.5))
        y = self.cy0 + self.ch + 110
        debut = 1.2 + len(self.reperes) * 0.55 + 0.2
        for j, ligne in enumerate(self.phrase):
            a = ease_out(prog(t, debut + j * 0.25, 0.6))
            if a <= 0:
                continue
            segs = [(s, self.f_txt, ROSE_VIF if cle else MARINE) for s, cle in ligne]
            larg = sum(d.textlength(s, font=self.f_txt) for s, _, _ in segs)
            texte_riche(c, segs, W / 2 - larg / 2, y + j * 68 + (1 - a) * 30, a)
        img.alpha_composite(c)
        return img.convert("RGB")


class CarteLignes(Scene):
    """Composant agenda : carte blanche à lignes — étiquette mauve, phrase avec mot clé rose."""

    def __init__(self, duree, hab, sur_titre, titre, sous_titre, lignes, consigne, graine):
        self.duree = duree
        self.hab = hab
        self.fond = Fond(graine)
        self.sur_titre, self.titre, self.sous_titre = sur_titre, titre, sous_titre
        self.lignes, self.consigne = lignes, consigne
        self.f_sur = font("gras", 32)
        self.f_titre = font("titre", 110)
        self.f_sous = font("gras", 40)
        self.f_label = font("titre", 40)
        self.f_txt = font("texte", 38)
        self.f_cle = font("gras", 38)
        self.f_consigne = font("gras", 36)
        self.y0, self.hl = 560, 210
        self.carte = Image.new("RGBA", (980, self.hl * len(lignes) + 140), (0, 0, 0, 0))
        ombre = Image.new("RGBA", self.carte.size, (0, 0, 0, 0))
        ImageDraw.Draw(ombre).rounded_rectangle((20, 34, 960, self.carte.height - 26), 44,
                                                fill=MARINE + (40,))
        self.carte.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(18)))
        self.carte.alpha_composite(rect_arrondi(940, self.carte.height - 60, 44, BLANC + (255,)),
                                   (20, 20))
        self.neurone = Neurone(250, graine + 3)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        texte(c, t, self.sur_titre.upper(), self.f_sur, 80, 160, ROSE_VIF, 0.0, espacement=3)
        texte(c, t, self.titre.upper(), self.f_titre, 74, 285, MARINE, 0.1, glisse=50)
        texte(c, t, self.sous_titre, self.f_sous, 80, 410, MAUVE, 0.35)
        self.hab.dessiner(c, t)
        a = ease_out(prog(t, 0.3, 0.7))
        coller(c, self.carte, W / 2, self.y0 + self.carte.height / 2 - 20 + (1 - a) * 60, alpha=a)
        d = ImageDraw.Draw(c)
        for i, (label, phrase) in enumerate(self.lignes):
            p = ease_out(prog(t, 0.8 + i * 0.45, 0.6))
            if p <= 0:
                continue
            y = self.y0 + 70 + i * self.hl
            d.text((110 - (1 - p) * 30, y + 40), label, font=self.f_label,
                   fill=MAUVE + (int(255 * p),), anchor="lm")
            for j, ligne in enumerate(phrase):
                segs = [(s, self.f_cle if cle else self.f_txt, ROSE_VIF if cle else MARINE)
                        for s, cle in ligne]
                texte_riche(c, segs, 420 + (1 - p) * 40, y + 30 + j * 50, p)
            if i < len(self.lignes) - 1:
                d.line((100, y + self.hl - 40, 100 + 880 * p, y + self.hl - 40),
                       fill=GRIS_LIGNE + (255,), width=3)
        yc = self.y0 + self.carte.height + 30
        texte(c, t, self.consigne, self.f_consigne, W / 2, yc, MARINE,
              0.9 + len(self.lignes) * 0.45, ancre="mm")
        self.neurone.dessiner(c, t, W - 80, self.y0 + 10, debut=0.6)
        img.alpha_composite(c)
        return img.convert("RGB")


class Cloture(Scene):
    """Carte de fin : logo, promesse, lieu, bouton « Rejoignez-nous », confettis."""

    def __init__(self, duree, hab, phrase, graine):
        self.duree = duree
        self.hab = hab
        self.fond = Fond(graine)
        self.logo = hab.badge(480)
        self.phrase = phrase
        self.f_slogan = font("gras", 30)
        self.f_phrase = font("titre", 76)
        self.f_info = font("texte", 36)
        self.f_cta = font("titre", 54)
        self.f_tags = font("gras", 30)
        self.coeur = coeur_plein(50, BLANC)
        self.fete = Fete(graine + 50, n=90, n_serp=6, debut=1.5)
        self.neurone = Neurone(280, graine, halo=True)

    def frame(self, t):
        img = self.fond.image(t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.neurone.dessiner(c, t, 120, 1560, debut=0.6)
        self.fete.dessiner(c, t)
        a = ease_back(prog(t, 0.0, 0.8))
        coller(c, self.logo, W / 2, 420, echelle=max(a * (1 + 0.012 * math.sin(t * 2.5)), 0.01),
               alpha=clamp(a * 1.4))
        texte(c, t, SLOGAN, self.f_slogan, W / 2, 710, MARINE, 0.4, ancre="mm", espacement=3)
        for i, ligne in enumerate(self.phrase):
            texte(c, t, ligne.upper(), self.f_phrase, W / 2, 840 + i * 92, MARINE, 0.6 + i * 0.15,
                  ancre="mm")
        y = 840 + len(self.phrase) * 92 + 40
        texte(c, t, "Association · enfants, adultes et familles", self.f_info, W / 2, y, MAUVE, 1.0,
              ancre="mm")
        texte(c, t, ADRESSE, self.f_info, W / 2, y + 56, MAUVE, 1.1, ancre="mm")
        b = ease_back(prog(t, 1.4, 0.6))
        if b > 0:
            pulse = 1 + 0.025 * math.sin(max(0, t - 2.0) * 4)
            tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength("REJOIGNEZ-NOUS", font=self.f_cta)
            bw, bh = int(tw + 200), 136
            btn = rect_arrondi(bw, bh, bh // 2, ROSE_VIF + (255,))
            btn.alpha_composite(self.coeur, (56, (bh - 50) // 2))
            ImageDraw.Draw(btn).text((bw / 2 + 34, bh / 2), "REJOIGNEZ-NOUS", font=self.f_cta,
                                     fill=BLANC + (255,), anchor="mm")
            coller(c, btn, W / 2, y + 220, echelle=max(b * pulse, 0.01), alpha=clamp(b * 1.5))
        texte(c, t, "Adhésion et inscriptions sur HelloAsso", self.f_info, W / 2, y + 350, MARINE,
              1.9, ancre="mm")
        texte(c, t, "#PESHNeuroEveil  #Meaux", self.f_tags, W / 2, y + 415, ROSE_VIF, 2.1, ancre="mm")
        self.hab.dessiner(c, t, badge=False)
        img.alpha_composite(c)
        return img.convert("RGB")


# ---------------------------------------------------------------- montages
# Repères (texte, point sur la photo source en pixels, position de la bulle à l'écran
# relative au haut de la carte photo).
REPERES_CARTES = [
    ("é · clair", (560, 1060), (330, 70)),
    ("a · no · rak", (700, 1330), (250, 470)),
    ("trom · pette", (1280, 1650), (790, 370)),
    ("che · val", (980, 1870), (560, 780)),
]
REPERES_NOMBRES = [
    ("le nombre avant", (860, 1160), (300, 250)),
    ("le nombre après", (1045, 1150), (780, 580)),
]
def montage(nom, m):
    p = lambda n: os.path.join(m, n)  # noqa: E731
    hab = Habillage(Image.open(p("logo_disque.png")).convert("RGBA"))
    if nom == "vocabulaire":
        return [
            Ouverture(3.8, hab, "APPRENDRE EN JOUANT", ["VOCABULAIRE", "& OBSERVATION"],
                      ["Il a des lunettes ?", "Elle sourit ?", "Cheveux bouclés ?"], 1),
            Photo(4.3, hab, p("quiestce.jpg"), "Observation", "Observer",
                  ["Poser des questions,", "repérer les détails."], "Qui est-ce ?", cy=0.45, graine=2),
            Photo(4.3, hab, p("sherlock.jpg"), "Lecture", "Enquêter",
                  ["Lire, chercher les indices,", "raconter avec ses mots."], "P'tit Sherlock",
                  cy=0.45, graine=3),
            PhotoDecrire(5.6, hab, p("enfant_joyeux.jpg"), [
                ("des cheveux bouclés", (250, 250), (330, 70)),
                ("les yeux fermés", (500, 455), (760, 300)),
                ("un grand sourire", (640, 640), (330, 760)),
            ], [[("Il a les ", False), ("cheveux bouclés", True)],
                [("et un ", False), ("grand sourire", True), (".", False)]],
                graine=4, zoom=(1.0, 1.04), ch=880),
            Photo(4.3, hab, p("coloriage.jpg"), "Motricité fine", "Nommer",
                  ["Choisir ses couleurs,", "les nommer, soigner son geste."], "Atelier créatif",
                  cy=0.5, graine=5),
            Photo(4.0, hab, p("materiel.jpg"), "Outils adaptés", "Manipuler",
                  ["Jeux, puzzles, laçages", "et minuteur visuel."], "Matériel adapté", cy=0.55,
                  graine=6),
            Cloture(5.8, hab, ["Révéler le potentiel", "de chaque enfant"], 7),
        ]
    if nom == "matinee":
        return [
            Ouverture(3.8, hab, "SYLLABES · LECTURE · NUMÉRATION", ["MATINÉE", "STUDIEUSE"], [], 21),
            PhotoDecrire(5.6, hab, p("cartes.jpg"), REPERES_CARTES,
                         [[("che", True), (" · ", False), ("val", True), (" : 2 syllabes,", False)],
                          [("2 frappes dans les mains.", False)]],
                         sur_titre="Syllabes", titre="Découper",
                         sous_titre=("Une image, un mot,", "puis on frappe les syllabes."),
                         etiquette="Jeu de cartes", cy=0.38, graine=22, zoom=(1.0, 1.04), ch=900),
            Photo(4.4, hab, p("lecture2_flou.jpg"), "Lecture", "Lire",
                  ["Suivre la ligne du doigt,", "à son rythme, même allongé."], "Coin lecture",
                  cy=0.42, graine=23),
            PhotoDecrire(5.6, hab, p("numeration.jpg"), REPERES_NOMBRES,
                         [[("Avant ", False), ("4", True), (", il y a ", False), ("3", True), (".", False)],
                          [("Après ", False), ("4", True), (", il y a ", False), ("5", True), (".", False)]],
                         sur_titre="Numération", titre="Compter",
                         sous_titre=("Le nombre avant,", "le nombre après."),
                         etiquette="Fiche numération", cy=0.3, graine=24, zoom=(1.0, 1.04), ch=900),
            Photo(4.4, hab, p("accompagner.jpg"), "Pas à pas", "Accompagner",
                  ["Une Technicienne en Remédiation", "Éducative, pour guider", "sans faire à la place."],
                  "Accompagnement", cy=0.45, graine=25),
            Cloture(5.8, hab, ["Apprendre", "à son rythme"], 26),
        ]
    return [
        Ouverture(3.8, hab, "SE REPÉRER · BOUGER · S'AJUSTER", ["APPRIVOISER", "SON CORPS"],
                  ["droite", "gauche", "devant", "derrière"], 11),
        Photo(4.4, hab, p("twister.jpg"), "Schéma corporel", "Se repérer",
              ["Main droite sur le rouge !", "Latéralité, équilibre, coordination."], "Twister",
              cy=0.5, graine=12),
        CarteLignes(5.6, hab, "Vocabulaire du corps", "Nommer", "Le mot juste, puis le geste.", [
            ("La tête", [[("Je ", False), ("tourne", True), (" la tête", False)],
                         [("vers la ", False), ("droite", True), (".", False)]]),
            ("Les épaules", [[("Je ", False), ("hausse", True), (" les épaules.", False)]]),
            ("Les genoux", [[("Je ", False), ("plie", True), (" les genoux.", False)]]),
            ("Les pieds", [[("Je ", False), ("pose", True), (" les pieds", False)],
                           [("bien ", False), ("à plat", True), (".", False)]]),
        ], "Nommer, puis faire : le corps se repère.", 13),
        Photo(4.4, hab, p("assise.jpg"), "Appréhension du corps", "S'ajuster",
              ["Coussin d'assise, élastique aux pieds :", "le corps trouve sa place."],
              "Assise dynamique", cy=0.4, graine=14),
        Photo(4.4, hab, p("salle.jpg"), "Notre espace à Meaux", "Un lieu",
              ["pensé pour travailler,", "bouger et se poser."], "Accueil adapté", cx=0.6, cy=0.5,
              graine=15, zoom=(1.0, 1.06)),
        Cloture(5.8, hab, ["Chaque enfant", "a son potentiel"], 16),
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
        if debut >= duree:
            break
        fin = min(duree, debut + seg + 1.2)
        a, b = int(debut * sr), int(fin * sr)
        tt = t[a:b] - debut
        env = np.minimum(1, tt / 0.9) * np.minimum(1, (fin - debut - tt) / 1.2)
        for f in acc:
            out[a:b] += 0.5 * np.sin(2 * math.pi * f * tt) * env
            out[a:b] += 0.2 * np.sin(2 * math.pi * f / 2 * tt) * env
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
        base, r, (cx, cy) = prec, ease_in_out(p * 2) * rmax, (0, H)
    else:
        base, r, (cx, cy) = suiv, (1 - ease_in_out((p - 0.5) * 2)) * rmax, (W, 0)
    base = base.convert("RGBA")
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.ellipse((cx - r * 1.08, cy - r * 1.08, cx + r * 1.08, cy + r * 1.08), fill=ROSE + (255,))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=ROSE_PALE + (255,))
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
    ap.add_argument("theme", choices=["vocabulaire", "corps", "matinee"])
    ap.add_argument("--medias", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    rendre(montage(a.theme, a.medias), a.sortie, {"vocabulaire": 1, "corps": 2, "matinee": 3}[a.theme])
