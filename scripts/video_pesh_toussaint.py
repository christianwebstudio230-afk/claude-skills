#!/usr/bin/env python3
"""Reel PESH Neuro-Éveil — Accueil de la Toussaint 2026, à partir du carrousel 7 visuels.

Les textes du carrousel sont recomposés en typographie animée (mots qui montent un à un),
les illustrations sont reprises du carrousel et animées, des feuilles en papier découpé
tombent. Palette du carrousel : crème, marine, rose, terracotta, sauge, moutarde.

Usage :
    python3 scripts/video_pesh_toussaint.py --medias <dossier> --sortie <fichier.mp4>

Le dossier médias contient slide1.png … slide7.png (carrousel 1080x1350) et logo_disque.png.
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from video_pesh import bande_son, clamp, coller, ease_back, ease_in_out, ease_out, prog, rect_arrondi

W, H, FPS = 1080, 1920, 30
TRANSITION = 0.7

CREME = (251, 242, 226)
MARINE = (15, 61, 87)
ROSE = (235, 8, 84)
TERRACOTTA = (220, 100, 70)
SAUGE = (142, 154, 114)
MOUTARDE = (232, 179, 60)
BLANC = (255, 255, 255)

FONTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")


def font(nom, taille):
    fichiers = {"lato": "Lato-Black.ttf", "titre": "Roboto-Bold.ttf", "texte": "Roboto-Medium.ttf"}
    return ImageFont.truetype(os.path.join(FONTS, fichiers[nom]), taille)


# ---------------------------------------------------------------- typographie animée
_CACHE = {}


def mot_sprite(mot, police, couleur):
    cle = (mot, police.path, police.size, couleur)
    if cle not in _CACHE:
        asc, desc = police.getmetrics()
        w = int(ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength(mot, font=police)) + 8
        img = Image.new("RGBA", (w, asc + desc + 12), (0, 0, 0, 0))
        ImageDraw.Draw(img).text((2, asc + 6), mot, font=police, fill=couleur + (255,), anchor="ls")
        _CACHE[cle] = img
    return _CACHE[cle]


def ligne_revelee(calque, t, segments, police, x, base, debut, decalage=0.07, duree=0.55):
    """Chaque mot monte depuis sous sa ligne de base, comme révélé par un masque."""
    d = ImageDraw.Draw(calque)
    asc, _ = police.getmetrics()
    espace = d.textlength(" ", font=police)
    i = 0
    for texte_seg, couleur in segments:
        for mot in texte_seg.split(" "):
            if not mot:
                continue
            sp = mot_sprite(mot, police, couleur)
            p = ease_out(prog(t, debut + i * decalage, duree))
            if p > 0:
                boite = Image.new("RGBA", sp.size, (0, 0, 0, 0))
                boite.alpha_composite(sp, (0, int((1 - p) * sp.height)))
                calque.alpha_composite(boite, (int(x), int(base - asc - 6)))
            x += sp.width - 8 + espace
            i += 1
    return i


def texte_fondu(calque, t, contenu, police, x, y, couleur, debut, ancre="ls"):
    a = ease_out(prog(t, debut, 0.6))
    if a > 0:
        ImageDraw.Draw(calque).text((x, y + (1 - a) * 30), contenu, font=police,
                                    fill=couleur + (int(255 * a),), anchor=ancre)


def pilule(contenu, police, fond, encre=BLANC, pad=(36, 20), rayon=None):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    asc, desc = police.getmetrics()
    w, h = int(d.textlength(contenu, font=police) + 2 * pad[0]), asc + desc + 2 * pad[1]
    img = rect_arrondi(w, h, rayon if rayon is not None else h // 2, fond + (255,))
    ImageDraw.Draw(img).text((w / 2, h / 2), contenu, font=police, fill=encre + (255,), anchor="mm")
    return img


# ---------------------------------------------------------------- décor
def feuille_papier(couleur, longueur, graine):
    """Feuille en papier découpé : forme pointue, nervure claire, légère ombre portée."""
    rng = np.random.default_rng(graine)
    k = 3
    L, l = longueur * k, longueur * k * rng.uniform(0.38, 0.5)
    w, h = int(L + 30 * k), int(l + 30 * k)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pts = []
    for j in range(60):
        u = j / 59
        pts.append((15 * k + u * L, h / 2 - math.sin(math.pi * u) ** 0.8 * l / 2))
    for j in range(60):
        u = 1 - j / 59
        pts.append((15 * k + u * L, h / 2 + math.sin(math.pi * u) ** 0.8 * l / 2))
    ombre = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(ombre).polygon([(x + 4 * k, y + 6 * k) for x, y in pts], fill=(60, 40, 20, 70))
    img.alpha_composite(ombre.filter(ImageFilter.GaussianBlur(4 * k)))
    d = ImageDraw.Draw(img)
    d.polygon(pts, fill=couleur + (255,))
    clair = tuple(min(255, c + 45) for c in couleur)
    d.line([(15 * k, h / 2), (15 * k + L * 0.92, h / 2)], fill=clair + (255,), width=2 * k)
    for u in (0.3, 0.5, 0.7):
        x0 = 15 * k + u * L
        for s in (-1, 1):
            d.line([(x0, h / 2), (x0 + L * 0.12, h / 2 + s * l * 0.32)], fill=clair + (255,), width=k)
    return img.resize((w // k, h // k), Image.LANCZOS)


class Feuilles:
    """Feuilles d'automne qui tombent en tournoyant."""

    def __init__(self, graine, n, debut=0.0, rafale=False):
        rng = np.random.default_rng(graine)
        couleurs = [TERRACOTTA, MOUTARDE, SAUGE, ROSE, TERRACOTTA, MOUTARDE]
        self.items = []
        for i in range(n):
            self.items.append(dict(
                sp=feuille_papier(couleurs[i % len(couleurs)], int(rng.uniform(70, 130)), graine * 31 + i),
                x=rng.uniform(40, W - 40),
                y0=rng.uniform(-500, -80) if rafale else rng.uniform(-300, H * 0.6),
                v=rng.uniform(110, 190), amp=rng.uniform(40, 90), f=rng.uniform(0.8, 1.6),
                ph=rng.uniform(0, 6.28), rot=rng.uniform(0, 360), retard=rng.uniform(0, 0.8) + debut))

    def dessiner(self, calque, t):
        for f in self.items:
            tt = t - f["retard"]
            if tt < 0:
                continue
            y = f["y0"] + f["v"] * tt
            if y > H + 120:
                continue
            x = f["x"] + f["amp"] * math.sin(tt * f["f"] + f["ph"])
            ang = f["rot"] + 35 * math.sin(tt * f["f"] * 1.3 + f["ph"]) + 20 * tt
            sp = f["sp"].rotate(ang, resample=Image.BICUBIC, expand=True)
            calque.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height / 2)))


class Tache:
    """Forme organique rose qui ondule dans un coin (motif du carrousel)."""

    def __init__(self, coin, couleur=ROSE, rayon=330):
        self.coin, self.couleur, self.rayon = coin, couleur, rayon

    def dessiner(self, calque, t, apparition=1.0):
        if apparition <= 0:
            return
        cx, cy = {"hg": (-40, -60), "hd": (W + 40, -60), "bd": (W + 60, H + 40), "bg": (-60, H + 40)}[self.coin]
        r0 = self.rayon * ease_out(apparition)
        pts = []
        for i in range(80):
            a = 2 * math.pi * i / 80
            r = r0 * (1 + 0.09 * math.sin(3 * a + t * 1.1) + 0.05 * math.sin(5 * a - t * 0.8))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        k = 2
        img = Image.new("RGBA", (W // k, H // k), (0, 0, 0, 0))
        ImageDraw.Draw(img).polygon([(x / k, y / k) for x, y in pts], fill=self.couleur + (235,))
        calque.alpha_composite(img.resize((W, H), Image.BICUBIC))


class Illustration:
    """Illustration du carrousel, détourée en fondu sur le fond crème, qui monte puis respire."""

    def __init__(self, chemin, boite, y_haut=1080, y_bas=1800):
        src = Image.open(chemin).convert("RGB").crop(boite)
        h_dispo = y_bas - y_haut
        r = W / src.width
        src = src.resize((W, int(src.height * r)), Image.LANCZOS)
        if src.height < h_dispo:  # agrandir pour remplir la place, recadrage centré
            r = h_dispo / src.height
            src = src.resize((int(W * r), h_dispo), Image.LANCZOS)
            x0 = (src.width - W) // 2
            src = src.crop((x0, 0, x0 + W, h_dispo))
        elif src.height > h_dispo:
            src = src.crop((0, src.height - h_dispo, W, src.height))
        img = src.convert("RGBA")
        masque = np.full((img.height, W), 255.0)
        fondu = 140
        rampe = np.linspace(0, 1, fondu) ** 1.6
        masque[:fondu] *= rampe[:, None]
        masque[-fondu:] *= rampe[::-1][:, None]
        img.putalpha(Image.fromarray(masque.astype(np.uint8)))
        self.img, self.y = img, y_bas - img.height

    def dessiner(self, calque, t, duree, debut=0.25):
        a = ease_out(prog(t, debut, 0.9))
        if a <= 0:
            return
        z = 1.0 + 0.05 * ease_in_out(t / duree)
        img = self.img.resize((int(W * z), int(self.img.height * z)), Image.BICUBIC)
        x = (W - img.width) // 2
        y = self.y + self.img.height - img.height + int((1 - a) * 140)
        if a < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        calque.alpha_composite(img, (x, y))


# ---------------------------------------------------------------- scène
class Diapo:
    def __init__(self, duree, illustration, titre, sous_titre=(), coin=None, extra=None,
                 feuilles=(6, False), graine=1, logo=None):
        self.duree = duree
        self.illus = illustration
        self.titre = titre          # [(segments, police, base_y)]
        self.sous_titre = sous_titre  # [(texte, police, base_y)]
        self.tache = Tache(coin) if coin else None
        self.extra = extra
        self.feuilles = Feuilles(graine, feuilles[0], rafale=feuilles[1])
        self.logo = logo
        self.f_pied = font("titre", 32)

    def frame(self, t):
        img = Image.new("RGBA", (W, H), CREME + (255,))
        if self.tache:
            self.tache.dessiner(img, t, prog(t, 0.0, 0.8))
        self.illus.dessiner(img, t, self.duree)
        self.feuilles.dessiner(img, t)
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        debut, n = 0.15, 0
        for segments, police, base in self.titre:
            n += ligne_revelee(c, t, segments, police, 80, base, debut + n * 0.07)
        fin_titre = debut + n * 0.07 + 0.3
        for i, (txt, police, base) in enumerate(self.sous_titre):
            texte_fondu(c, t, txt, police, 82, base, MARINE, fin_titre + i * 0.12)
        if self.extra:
            self.extra(c, t, fin_titre)
        if self.logo is not None:
            a = ease_back(prog(t, 0.1, 0.6))
            coller(c, self.logo, W - 130, 150, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
        d = ImageDraw.Draw(c)
        d.text((W / 2, 1860), "PESH Neuro-Éveil  ·  Meaux", font=self.f_pied, fill=MARINE + (255,),
               anchor="mm")
        img.alpha_composite(c)
        return img.convert("RGB")


# ---------------------------------------------------------------- éléments spécifiques
def extra_pilule(texte, y):
    sp = pilule(texte, font("titre", 40), ROSE, rayon=16, pad=(30, 18))

    def f(c, t, debut):
        a = ease_back(prog(t, debut, 0.6))
        coller(c, sp, 80 + sp.width / 2, y, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
    return f


def extra_programme(y):
    items = [("Ateliers créatifs", SAUGE), ("Défis", TERRACOTTA), ("Jeux", MOUTARDE),
             ("Sorties de proximité", MARINE)]
    sps = [pilule(txt, font("titre", 44), coul) for txt, coul in items]
    pos = [(80, y), (80 + sps[0].width + 24, y), (80, y + 110), (80 + sps[2].width + 24, y + 110)]

    def f(c, t, debut):
        for i, (sp, (x, yy)) in enumerate(zip(sps, pos)):
            a = ease_back(prog(t, debut + i * 0.22, 0.55))
            coller(c, sp, x + sp.width / 2, yy, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
    return f


def extra_jours(y):
    jours = [("LUN", "19"), ("MAR", "20"), ("MER", "21"), ("JEU", "22"), ("VEN", "23")]
    f_j, f_n = font("titre", 30), font("titre", 64)

    def case(j, n, actif):
        fond = ROSE if actif else BLANC
        encre = BLANC if actif else MARINE
        img = rect_arrondi(168, 168, 30, fond + (255,))
        if not actif:
            ImageDraw.Draw(img).rounded_rectangle((1, 1, 166, 166), 30, outline=MARINE + (60,), width=3)
        d = ImageDraw.Draw(img)
        d.text((84, 50), j, font=f_j, fill=encre + (255,), anchor="mm")
        d.text((84, 110), n, font=f_n, fill=encre + (255,), anchor="mm")
        return img
    off = [case(j, n, False) for j, n in jours]
    on = [case(j, n, True) for j, n in jours]

    def f(c, t, debut):
        for i in range(5):
            a = ease_back(prog(t, debut + i * 0.12, 0.5))
            x = 80 + 84 + i * 190
            coller(c, off[i], x, y, echelle=max(a, 0.01), alpha=clamp(a * 1.5))
            g = ease_out(prog(t, debut + 0.9 + i * 0.18, 0.3))
            if g > 0:
                coller(c, on[i], x, y, echelle=1 + 0.06 * math.sin(math.pi * g), alpha=g)
    return f


def extra_contact(y):
    from video_pesh import coeur_plein
    f_cta = font("titre", 56)
    tw = ImageDraw.Draw(Image.new("RGBA", (1, 1))).textlength("Contactez-nous", font=f_cta)
    bw, bh = int(tw + 190), 132
    btn = rect_arrondi(bw, bh, bh // 2, ROSE + (255,))
    btn.alpha_composite(coeur_plein(48, BLANC), (52, (bh - 48) // 2))
    ImageDraw.Draw(btn).text((bw / 2 + 32, bh / 2), "Contactez-nous", font=f_cta, fill=BLANC + (255,),
                             anchor="mm")
    f_adr = font("texte", 38)

    def f(c, t, debut):
        a = ease_back(prog(t, debut + 0.3, 0.6))
        pulse = 1 + 0.03 * math.sin(max(0, t - debut - 0.9) * 4)
        coller(c, btn, 80 + bw / 2, y, echelle=max(a * pulse, 0.01), alpha=clamp(a * 1.5))
        texte_fondu(c, t, "13 rue de l'Arbalète · 77100 Meaux", f_adr, 82, y + 125, MARINE, debut + 0.6)
    return f


# ---------------------------------------------------------------- montage
def montage(m):
    p = lambda n: os.path.join(m, n)  # noqa: E731
    logo = Image.open(p("logo_disque.png")).convert("RGBA")
    logo.thumbnail((190, 190), Image.LANCZOS)
    lato, t120, t150, t180 = font("lato", 138), font("titre", 124), font("titre", 150), font("titre", 180)
    sous = font("texte", 50)
    sous_b = font("titre", 46)
    return [
        Diapo(4.2, Illustration(p("slide1.png"), (0, 630, 1080, 1185), 980),
              [([("Les vacances", MARINE)], lato, 470), ([("aussi,", ROSE)], lato, 620),
               ([("ça se construit", MARINE)], lato, 770)],
              coin="hg", extra=extra_pilule("Accueil de la Toussaint • 19–23 octobre 2026", 900),
              feuilles=(14, True), graine=1, logo=logo),
        Diapo(4.0, Illustration(p("slide2.png"), (0, 640, 1080, 1350), 950),
              [([("Une semaine", ROSE)], t120, 420), ([("pour découvrir,", ROSE)], t120, 560),
               ([("créer et jouer", ROSE)], t120, 700)],
              [("À son rythme, dans un", sous, 820), ("cadre collectif adaptable.", sous, 885)],
              coin="bd", graine=2, logo=logo),
        Diapo(3.8, Illustration(p("slide3.png"), (0, 720, 1080, 1350), 930),
              [([("Pour les", MARINE)], t180, 470), ([("8-14 ans", ROSE)], t180, 660)],
              [("Des profils et des besoins variés,", sous_b, 800),
               ("plusieurs façons de participer.", sous_b, 862)],
              graine=3, logo=logo),
        Diapo(4.4, Illustration(p("slide4.png"), (0, 560, 1080, 1160), 1000),
              [([("Au", MARINE)], t180, 450), ([("programme", ROSE)], t180, 640)],
              coin="hg", extra=extra_programme(790), graine=4, logo=logo),
        Diapo(4.0, Illustration(p("slide5.png"), (0, 600, 1080, 1350), 860),
              [([("Chacun peut", ROSE)], font("titre", 128), 450),
               ([("trouver sa place", ROSE)], font("titre", 128), 590)],
              [("Observer, essayer, choisir,", sous, 720), ("coopérer ou faire une pause.", sous, 785)],
              coin="hd", graine=5, logo=logo),
        Diapo(4.6, Illustration(p("slide6.png"), (0, 520, 1080, 1130), 1000),
              [([("Du lundi 19 au", MARINE)], font("titre", 104), 430),
               ([("vendredi 23 octobre", MARINE)], font("titre", 104), 555)],
              [("9h00 – 16h30 • Meaux", font("titre", 58), 665)],
              coin="hg", extra=extra_jours(830), graine=6, logo=logo),
        Diapo(5.4, Illustration(p("slide7.png"), (0, 760, 1080, 1350), 1080),
              [([("Envie d'en", MARINE)], t150, 430), ([("savoir", MARINE), ("plus ?", ROSE)], t150, 590)],
              [("Contactez-nous pour les modalités", font("texte", 44), 700),
               ("d'accueil et d'inscription.", font("texte", 44), 758)],
              extra=extra_contact(900), feuilles=(14, True), graine=7, logo=logo),
    ]


# ---------------------------------------------------------------- rendu
def transition(prec, suiv, p):
    """La scène suivante monte comme une feuille de papier, précédée d'une bande rose."""
    e = ease_in_out(p)
    base = Image.new("RGB", (W, H), CREME)
    base.paste(prec, (0, int(-e * H * 0.25)))
    y = int((1 - e) * H)
    d = ImageDraw.Draw(base)
    d.rectangle((0, y - 36, W, y), fill=ROSE)
    if y < H:
        base.paste(suiv.crop((0, 0, W, H - y)), (0, y))
    return base


def rendre(scenes, sortie):
    debuts, t0 = [], 0.0
    for s in scenes:
        debuts.append(t0)
        t0 += s.duree - TRANSITION
    total = t0 + TRANSITION
    audio = sortie + ".wav"
    bande_son(audio, total, 3)
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
    ap.add_argument("--medias", required=True)
    ap.add_argument("--sortie", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.sortie)), exist_ok=True)
    rendre(montage(a.medias), a.sortie)
