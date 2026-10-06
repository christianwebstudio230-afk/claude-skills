#!/usr/bin/env python3
"""Vidéos promotionnelles PESH' Neuro Éveil — format Reel/Story 1080x1920, 30 i/s.

Usage :
    python3 scripts/video_pesh.py <1|2> --medias <dossier_photos> --sortie <fichier.mp4>

Le dossier médias doit contenir : lecture.jpg, monnaie.jpg, boucles.jpg,
ecouter.png, soutenir.png, apaiser.png.
Charte : fiche marque Nat'H IA « pesh-neuro-eveil » (palette institutionnelle teal / corail).
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
XFADE = 0.6

# Palette institutionnelle PESH (fiche marque)
TEAL = (31, 92, 82)
CORAIL = (232, 115, 74)
SABLE = (242, 193, 78)
TEAL_CLAIR = (228, 238, 236)
ENCRE = (34, 48, 44)
CREME = (250, 246, 239)
ROSE = (236, 64, 122)  # rappel des visuels existants de l'association

ICI = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(ICI, "assets", "fonts")
INTER = "/usr/share/fonts/opentype/inter"


def font(nom, taille):
    chemins = {
        "titre": os.path.join(FONTS, "Playfair.ttf"),
        "script": os.path.join(FONTS, "GreatVibes.ttf"),
        "texte": os.path.join(INTER, "Inter-Medium.otf"),
        "texte_gras": os.path.join(INTER, "Inter-SemiBold.otf"),
        "texte_leger": os.path.join(INTER, "Inter-Light.otf"),
    }
    return ImageFont.truetype(chemins[nom], taille)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def apparition(t, debut, duree=0.8):
    return ease_out((t - debut) / duree)


# ---------------------------------------------------------------- dessin
def texte(calque, t, contenu, police, y, couleur, debut, centre_x=W // 2,
          glisse=40, ombre=False, duree=0.8):
    """Texte centré qui apparaît en fondu + glissement vers le haut."""
    a = apparition(t, debut, duree)
    if a <= 0:
        return
    d = ImageDraw.Draw(calque)
    yy = y + (1 - a) * glisse
    alpha = int(255 * a)
    if ombre:
        couche = Image.new("RGBA", calque.size, (0, 0, 0, 0))
        ImageDraw.Draw(couche).text((centre_x, yy + 4), contenu, font=police,
                                    fill=(0, 0, 0, int(140 * a)), anchor="mm")
        couche = couche.filter(ImageFilter.GaussianBlur(8))
        calque.alpha_composite(couche)
    d.text((centre_x, yy), contenu, font=police, fill=couleur + (alpha,), anchor="mm")


def feuille_sprite(couleur, longueur=120):
    """Feuille stylisée antialiasée (dessinée en 3x puis réduite)."""
    k = 3
    w, h = longueur * k, int(longueur * 0.42) * k
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pts = []
    for i in range(61):
        u = i / 60
        pts.append((u * w, h / 2 - math.sin(math.pi * u) ** 0.9 * h / 2))
    for i in range(61):
        u = 1 - i / 60
        pts.append((u * w, h / 2 + math.sin(math.pi * u) ** 0.9 * h / 2))
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=couleur + (255,))
    d.line([(w * 0.05, h / 2), (w * 0.9, h / 2)], fill=(255, 255, 255, 90), width=k * 2)
    return img.resize((longueur, int(longueur * 0.42)), Image.LANCZOS)


def coeur_sprite(couleur, taille=80):
    k = 3
    s = taille * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pts = []
    for i in range(200):
        a = 2 * math.pi * i / 200
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((s / 2 + x * s / 36, s / 2.1 - y * s / 36))
    ImageDraw.Draw(img).polygon(pts, fill=couleur + (255,))
    return img.resize((taille, taille), Image.LANCZOS)


class Feuilles:
    """Feuilles qui flottent doucement (motif repris des visuels PESH)."""

    def __init__(self, graine, n, couleurs, zone=(0, 0, W, H), bords=True):
        rng = np.random.default_rng(graine)
        self.items = []
        for _ in range(n):
            c = couleurs[rng.integers(len(couleurs))]
            self.items.append(dict(
                sprite=feuille_sprite(c, int(rng.uniform(70, 150))),
                x=(rng.uniform(zone[0], zone[0] + 200) if rng.random() < 0.5
                   else rng.uniform(zone[2] - 200, zone[2])) if bords
                else rng.uniform(zone[0], zone[2]),
                y=rng.uniform(zone[1], zone[3]),
                rot=rng.uniform(0, 360), vrot=rng.uniform(-25, 25),
                vy=rng.uniform(18, 45), amp=rng.uniform(15, 40),
                ph=rng.uniform(0, 6.28), alpha=rng.uniform(0.55, 0.95)))

    def dessiner(self, calque, t, opacite=1.0):
        for f in self.items:
            sp = f["sprite"].rotate(f["rot"] + f["vrot"] * t, resample=Image.BICUBIC, expand=True)
            if opacite * f["alpha"] < 1:
                a = sp.getchannel("A").point(lambda v: int(v * opacite * f["alpha"]))
                sp.putalpha(a)
            x = f["x"] + math.sin(t * 0.8 + f["ph"]) * f["amp"]
            y = (f["y"] + f["vy"] * t) % (H + 200) - 100
            calque.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))


def degrade_bas(hauteur, couleur, alpha_max=235):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    col = np.zeros((H, 1, 4), dtype=np.uint8)
    col[..., :3] = couleur
    y0 = H - hauteur
    ys = np.arange(H)
    a = np.clip((ys - y0) / hauteur, 0, 1) ** 1.4 * alpha_max
    col[:, 0, 3] = a.astype(np.uint8)
    return Image.fromarray(np.repeat(col, W, axis=1), "RGBA")


def cover(img, w, h, cx=0.5, cy=0.5):
    """Recadre img pour remplir w x h, centré sur (cx, cy) en proportion."""
    r = max(w / img.width, h / img.height)
    img = img.resize((math.ceil(img.width * r), math.ceil(img.height * r)), Image.LANCZOS)
    x = int(clamp(cx * img.width - w / 2, 0, img.width - w))
    y = int(clamp(cy * img.height - h / 2, 0, img.height - h))
    return img.crop((x, y, x + w, y + h))


def charger(chemin):
    return ImageOps.exif_transpose(Image.open(chemin)).convert("RGB")


# ---------------------------------------------------------------- scènes
class Scene:
    duree = 4.0

    def frame(self, t):  # -> Image RGB W x H
        raise NotImplementedError


class KenBurns(Scene):
    """Photo plein cadre avec zoom lent + légende manuscrite et sous-titre."""

    def __init__(self, chemin, duree, mot, sous_titre, cx=0.5, cy=0.5,
                 zoom=(1.0, 1.12), derive=(0, -0.02), legende=True):
        self.duree = duree
        marge = 1.18
        self.base = cover(charger(chemin), int(W * marge), int(H * marge), cx, cy)
        self.zoom, self.derive = zoom, derive
        self.mot, self.sous_titre, self.legende = mot, sous_titre, legende
        self.grad = degrade_bas(900, ENCRE, 225)
        self.f_mot = font("script", 190)
        self.f_sous = font("texte", 54)

    def fond(self, t):
        p = ease_in_out(t / self.duree)
        z = self.zoom[0] + (self.zoom[1] - self.zoom[0]) * p
        cw, ch = W * (self.base.width / W) / z, H * (self.base.height / H) / z
        cx = self.base.width / 2 + self.derive[0] * self.base.width * p
        cy = self.base.height / 2 + self.derive[1] * self.base.height * p
        box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
        return self.base.resize((W, H), Image.BICUBIC, box=box).convert("RGBA")

    def frame(self, t):
        img = self.fond(t)
        if self.legende:
            img.alpha_composite(self.grad)
            calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            texte(calque, t, self.mot, self.f_mot, 1330, (255, 255, 255), 0.35, ombre=True)
            barre = apparition(t, 0.8, 0.7)
            if barre > 0:
                lw = int(140 * barre)
                ImageDraw.Draw(calque).rounded_rectangle(
                    (W // 2 - lw // 2, 1452, W // 2 + lw // 2, 1460), 4, fill=CORAIL + (255,))
            for i, ligne in enumerate(self.sous_titre):
                texte(calque, t, ligne, self.f_sous, 1530 + i * 72, (255, 255, 255), 0.9 + i * 0.15)
            img.alpha_composite(calque)
        return img.convert("RGB")


class CartePhoto(KenBurns):
    """Photo paysage : fond flouté + carte arrondie (évite un recadrage trop serré)."""

    def __init__(self, chemin, duree, mot, sous_titre, **kw):
        super().__init__(chemin, duree, mot, sous_titre, **kw)
        src = charger(chemin)
        self.flou = cover(src, W, H).filter(ImageFilter.GaussianBlur(40)).convert("RGBA")
        self.flou.alpha_composite(Image.new("RGBA", (W, H), TEAL + (120,)))
        cw = W - 120
        ch = int(cw * 1.08)
        self.carte = cover(src, int(cw * 1.12), int(ch * 1.12), 0.42, 0.55)
        self.cw, self.ch = cw, ch
        m = Image.new("L", (cw, ch), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, cw, ch), 48, fill=255)
        self.masque = m
        ombre = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ombre).rounded_rectangle((60, 230, 60 + cw, 230 + ch + 20), 48,
                                                fill=(0, 0, 0, 110))
        self.ombre = ombre.filter(ImageFilter.GaussianBlur(30))

    def fond(self, t):
        p = ease_in_out(t / self.duree)
        z = 1.0 + 0.1 * p
        bw, bh = self.carte.size
        cw, ch = bw / 1.12 / z, bh / 1.12 / z
        cx, cy = bw / 2 + 0.03 * bw * p, bh / 2
        photo = self.carte.resize((self.cw, self.ch), Image.BICUBIC,
                                  box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        img = self.flou.copy()
        a = apparition(t, 0.0, 0.9)
        y = 200 + int((1 - a) * 60)
        img.alpha_composite(self.ombre)
        img.paste(photo, (60, y), self.masque)
        return img


class Visuel(Scene):
    """Visuel existant de l'association (texte déjà intégré) : zoom doux seulement."""

    def __init__(self, chemin, duree):
        self.duree = duree
        self.img = cover(charger(chemin), W, H)

    def frame(self, t):
        z = 1.0 + 0.07 * ease_in_out(t / self.duree)
        cw, ch = W / z, H / z
        box = ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2)
        return self.img.resize((W, H), Image.BICUBIC, box=box)


class Ouverture(Scene):
    """Carte d'ouverture : cercle teal qui s'ouvre, nom de l'association."""

    def __init__(self, duree, sur_titre, accroche):
        self.duree = duree
        self.sur_titre, self.accroche = sur_titre, accroche
        self.feuilles = Feuilles(3, 9, [CORAIL, ROSE, SABLE])
        self.f_petit = font("texte_gras", 40)
        self.f_nom = font("titre", 112)
        self.f_nom2 = font("titre", 84)
        self.f_acc = font("script", 120)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), CREME + (255,))
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        r = int(1150 * ease_out(t / 1.4))
        ImageDraw.Draw(calque).ellipse((W // 2 - r, 900 - r, W // 2 + r, 900 + r), fill=TEAL + (255,))
        img.alpha_composite(calque)
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.feuilles.dessiner(calque, t, opacite=apparition(t, 0.5, 1.0) * 0.85)
        img.alpha_composite(calque)
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        texte(calque, t, self.sur_titre, self.f_petit, 640, SABLE, 0.6)
        texte(calque, t, "PESH'", self.f_nom, 790, (255, 255, 255), 0.8)
        texte(calque, t, "Neuro Éveil", self.f_nom2, 920, (255, 255, 255), 1.0)
        a = apparition(t, 1.3, 0.6)
        if a > 0:
            lw = int(220 * a)
            ImageDraw.Draw(calque).rounded_rectangle(
                (W // 2 - lw // 2, 1010, W // 2 + lw // 2, 1018), 4, fill=CORAIL + (255,))
        texte(calque, t, self.accroche, self.f_acc, 1150, TEAL_CLAIR, 1.5, duree=1.0)
        img.alpha_composite(calque)
        return img.convert("RGB")


class Question(Scene):
    """Plein écran texte sur fond teal profond, lignes successives."""

    def __init__(self, duree, lignes):
        self.duree = duree
        self.lignes = lignes  # (texte, police, y, couleur, debut)
        self.feuilles = Feuilles(11, 6, [CORAIL, ROSE])

    def frame(self, t):
        img = Image.new("RGBA", (W, H), TEAL + (255,))
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.feuilles.dessiner(calque, t, opacite=0.6)
        for contenu, police, y, couleur, debut in self.lignes:
            texte(calque, t, contenu, police, y, couleur, debut)
        img.alpha_composite(calque)
        return img.convert("RGB")


class CarteOffre(Scene):
    """Présentation d'une offre : titre, cadre, puces de réassurance."""

    def __init__(self, duree, etiquette, titre, cadre, puces, couleur=TEAL):
        self.duree = duree
        self.etiquette, self.titre, self.cadre, self.puces = etiquette, titre, cadre, puces
        self.couleur = couleur
        self.feuilles = Feuilles(7, 5, [CORAIL, SABLE], zone=(0, 0, W, 500))
        self.coeur = coeur_sprite(CORAIL, 46)
        self.f_eti = font("texte_gras", 36)
        self.f_titre = font("titre", 86)
        self.f_cadre = font("texte", 42)
        self.f_puce = font("texte", 46)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), CREME + (255,))
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.feuilles.dessiner(calque, t, opacite=0.7)
        img.alpha_composite(calque)
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(calque)
        a = apparition(t, 0.1, 0.6)
        if a > 0:
            bw = d.textlength(self.etiquette, font=self.f_eti) + 70
            d.rounded_rectangle((W / 2 - bw / 2, 520 - 38, W / 2 + bw / 2, 520 + 38), 38,
                                fill=self.couleur + (int(255 * a),))
            d.text((W / 2, 520), self.etiquette, font=self.f_eti,
                   fill=(255, 255, 255, int(255 * a)), anchor="mm")
        y = 680
        for i, ligne in enumerate(self.titre):
            texte(calque, t, ligne, self.f_titre, y + i * 105, ENCRE, 0.35 + i * 0.12)
        y += len(self.titre) * 105 + 20
        texte(calque, t, self.cadre, self.f_cadre, y, CORAIL, 0.8)
        y += 140
        for i, puce in enumerate(self.puces):
            debut = 1.3 + i * 0.45
            a = apparition(t, debut, 0.7)
            if a <= 0:
                continue
            yy = y + i * 125
            d.rounded_rectangle((90, yy - 50, W - 90, yy + 50), 50,
                                fill=TEAL_CLAIR + (int(255 * a),))
            c = self.coeur.copy()
            c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
            calque.alpha_composite(c, (130, int(yy - 23)))
            d.text((205 - (1 - a) * 30, yy), puce, font=self.f_puce,
                   fill=ENCRE + (int(255 * a),), anchor="lm")
        img.alpha_composite(calque)
        return img.convert("RGB")


class Cloture(Scene):
    """Carte de fin : signature, lieu, appel à l'action."""

    def __init__(self, duree, phrase, cta):
        self.duree = duree
        self.phrase, self.cta = phrase, cta
        self.feuilles = Feuilles(5, 8, [CORAIL, ROSE, SABLE])
        self.coeur = coeur_sprite(ROSE, 70)
        self.f_phrase = font("script", 104)
        self.f_nom = font("titre", 92)
        self.f_info = font("texte", 40)
        self.f_info_l = font("texte_leger", 38)
        self.f_cta = font("texte_gras", 44)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), TEAL + (255,))
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.feuilles.dessiner(calque, t, opacite=0.75)
        img.alpha_composite(calque)
        calque = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(calque)
        for i, ligne in enumerate(self.phrase):
            texte(calque, t, ligne, self.f_phrase, 470 + i * 125, (255, 255, 255), 0.2 + i * 0.25)
        a = apparition(t, 0.9, 0.7)
        if a > 0:
            battement = 1 + 0.08 * max(0, math.sin((t - 0.9) * 4.0))
            s = int(70 * a * battement)
            c = self.coeur.resize((max(s, 1), max(s, 1)), Image.LANCZOS)
            calque.alpha_composite(c, (W // 2 - s // 2, 800 - s // 2))
        texte(calque, t, "PESH' Neuro Éveil", self.f_nom, 960, (255, 255, 255), 1.1)
        texte(calque, t, "Association · Troubles du Neuro-Développement", self.f_info, 1060,
              SABLE, 1.3)
        texte(calque, t, "Enfants · adultes · familles", self.f_info_l, 1120, TEAL_CLAIR, 1.4)
        texte(calque, t, "11 rue de l'Arbalète · 77100 Meaux", self.f_info_l, 1180, TEAL_CLAIR, 1.5)
        a = apparition(t, 1.9, 0.7)
        if a > 0:
            pulse = 1 + 0.03 * math.sin(max(0, t - 2.6) * 3.5)
            bw = (d.textlength(self.cta, font=self.f_cta) + 110) * pulse
            bh = 116 * pulse
            yc = 1380 + (1 - a) * 40
            d.rounded_rectangle((W / 2 - bw / 2, yc - bh / 2, W / 2 + bw / 2, yc + bh / 2),
                                bh / 2, fill=CORAIL + (int(255 * a),))
            d.text((W / 2, yc), self.cta, font=self.f_cta,
                   fill=(255, 255, 255, int(255 * a)), anchor="mm")
        texte(calque, t, "#PESHNeuroEveil  ·  #Meaux", self.f_info_l, 1510, TEAL_CLAIR, 2.3)
        img.alpha_composite(calque)
        return img.convert("RGB")


# ---------------------------------------------------------------- montages
def montage(numero, m):
    p = lambda n: os.path.join(m, n)  # noqa: E731
    if numero == 1:
        return [
            Ouverture(3.4, "ASSOCIATION · MEAUX", "Révéler le potentiel"),
            CartePhoto(p("lecture.jpg"), 4.4, "Apprendre",
                       ["à son rythme,", "avec des outils adaptés"]),
            KenBurns(p("monnaie.jpg"), 4.4, "Comprendre",
                     ["par le concret,", "en manipulant, en jouant"], cx=0.5, cy=0.42),
            KenBurns(p("boucles.jpg"), 4.4, "Grandir",
                     ["en autonomie,", "un geste après l'autre"], cx=0.5, cy=0.55,
                     derive=(0, 0.02)),
            Visuel(p("apaiser.png"), 3.4),
            Cloture(5.6, ["Chaque enfant", "a un potentiel."], "Adhésion sur HelloAsso"),
        ]
    titre, texte_m = font("titre", 76), font("texte_leger", 48)
    return [
        Question(4.4, [
            ("Vous accompagnez", texte_m, 700, TEAL_CLAIR, 0.2),
            ("un enfant avec un TND ?", texte_m, 770, TEAL_CLAIR, 0.45),
            ("Et vous,", font("script", 150), 1000, (255, 255, 255), 1.6),
            ("qui prend soin de vous ?", titre, 1140, SABLE, 2.1),
        ]),
        Visuel(p("ecouter.png"), 3.6),
        CarteOffre(5.2, "PARCOURS MENSUEL · LE LUNDI SOIR", ["L'Art de", "se ressourcer"],
                   "Prévention et mieux-être · Meaux",
                   ["Aucune compétence artistique", "8 participantes maximum",
                    "Vous participez à votre rythme"]),
        Visuel(p("soutenir.png"), 3.4),
        CarteOffre(4.6, "LE MARDI SOIR", ["L'Apéro", "des parents"],
                   "Échanges libres · aucun thème imposé",
                   ["Entre parents qui comprennent", "Gratuit pour les adhérents"],
                   couleur=CORAIL),
        Cloture(5.6, ["Prendre soin de vous,", "c'est aussi prendre", "soin d'eux."],
                "Rejoignez-nous sur HelloAsso"),
    ]


# ---------------------------------------------------------------- audio
def nappe_sonore(chemin, duree, graine):
    """Nappe d'ambiance douce générée (aucun droit musical à gérer)."""
    sr = 44100
    n = int(duree * sr)
    t = np.arange(n) / sr
    accords = [[261.63, 329.63, 392.00, 493.88],   # Cmaj7
               [220.00, 261.63, 329.63, 392.00],   # Am7
               [174.61, 220.00, 261.63, 329.63],   # Fmaj7
               [196.00, 246.94, 293.66, 392.00]]   # G
    if graine == 2:
        accords = accords[2:] + accords[:2]
    seg = duree / 4
    out = np.zeros(n)
    for i, acc in enumerate(accords * 2):
        debut = i * seg
        if debut >= duree:
            break
        fin = min(duree, debut + seg + 1.5)
        a, b = int(debut * sr), int(fin * sr)
        tt = t[a:b] - debut
        env = np.minimum(1, tt / 1.2) * np.minimum(1, (fin - debut - tt) / 1.5)
        for f in acc:
            for k, g in ((1, 1.0), (2, 0.25), (0.5, 0.35)):
                out[a:b] += g * np.sin(2 * math.pi * f * k * tt + 0.3 * np.sin(2 * math.pi * 0.2 * tt)) * env
    # petites notes cristallines
    rng = np.random.default_rng(graine)
    for _ in range(int(duree * 0.9)):
        f = rng.choice([523.25, 659.25, 783.99, 987.77, 1046.5])
        d0 = rng.uniform(0.5, duree - 2)
        a = int(d0 * sr)
        tt = np.arange(int(2 * sr)) / sr
        out[a:a + len(tt)] += 0.6 * np.sin(2 * math.pi * f * tt) * np.exp(-tt * 3)
    out *= np.minimum(1, t / 1.5) * np.minimum(1, (duree - t) / 2.0)
    out = out / np.max(np.abs(out)) * 0.45
    st = np.stack([out, np.roll(out, 300)], axis=1)
    with wave.open(chemin, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((st * 32767).astype(np.int16).tobytes())


# ---------------------------------------------------------------- rendu
def rendre(scenes, sortie, graine):
    debuts, t0 = [], 0.0
    for s in scenes:
        debuts.append(t0)
        t0 += s.duree - XFADE
    total = t0 + XFADE
    audio = sortie + ".wav"
    nappe_sonore(audio, total, graine)
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
        img = scenes[k].frame(tl)
        if len(actives) > 1 and tl < XFADE:
            kp, tlp = actives[-2]
            img = Image.blend(scenes[kp].frame(tlp), img, ease_in_out(tl / XFADE))
        ff.stdin.write(img.tobytes())
        if i % 60 == 0:
            print(f"  {i}/{nb}", file=sys.stderr, flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print(f"{sortie} · {total:.1f} s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("numero", type=int, choices=[1, 2])
    ap.add_argument("--medias", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    rendre(montage(a.numero, a.medias), a.sortie, a.numero)
