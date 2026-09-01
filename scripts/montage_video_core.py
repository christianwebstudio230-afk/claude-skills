#!/usr/bin/env python3
"""
montage_video_core.py — Module métier Montage Vidéo AKOMA DIGITAL LTD

Pipeline en 3 étapes :
    1. transcrire  — Gemini regarde la vidéo, transcrit et repère les bafouillages
                       (secours automatique et gratuit sur faster-whisper en local
                       si Gemini est indisponible — clé absente, quota, réseau)
    2. couper      — ffmpeg supprime les segments "bafouillage" de la vidéo
    3. habiller     — CE SCRIPT NE GÉNÈRE PAS LE HTML HYPERFRAMES. Il exporte les
                       sous-titres reprojetés sur la timeline coupée (JSON), prêts
                       à être injectés dans une composition authored par un agent
                       équipé des skills HyperFrames officielles (voir plus bas).

Usage:
    python3 montage_video_core.py transcrire --video source.mp4 --sortie transcript.json
    python3 montage_video_core.py couper --video source.mp4 --transcript transcript.json --sortie coupe.mp4
    python3 montage_video_core.py habiller --plan coupe.plan.json --sortie sous_titres.json
    python3 montage_video_core.py pipeline --video source.mp4 --sortie-dir sorties/<client>/

Prérequis :
    pip install google-genai pyyaml
    pip install faster-whisper     # solution de secours locale, gratuite, sans clé API
    ffmpeg installé et dans le PATH

Moteur de transcription : Gemini est utilisé en priorité (meilleure détection,
sémantique, comprend le contexte). Si Gemini échoue et que le secours n'est pas
désactivé (--sans-secours), le script bascule automatiquement sur faster-whisper
en local — gratuit, sans abonnement, mais la détection des bafouillages y est
une heuristique (répétition immédiate d'un mot, ou segment composé uniquement de
mots de remplissage) donc moins fiable sur les cas ambigus. Le moteur réellement
utilisé est toujours écrit dans le transcript.json et doit être signalé dans tout
compte rendu — jamais masqué.

SUR L'HABILLAGE : une première version de ce script générait un fichier HTML
HyperFrames "deviné" (contrat non vérifié). Depuis l'installation réelle de la
skill (`npx skills add heygen-com/hyperframes --full-depth`), on sait que ce
pari était faux sur plusieurs points (timeline GSAP obligatoire enregistrée sur
window.__timelines, data-duration racine, etc.) : générer du HTML à l'aveugle
depuis Python serait justement le genre de chiffre/contrat inventé que la
constitution AKOMA interdit. L'habillage (sous-titres, b-roll, zooms, plans de
coupe) est donc délégué à un agent qui charge /hyperframes → /hyperframes-core
(+ /media-use, /hyperframes-keyframes selon besoin) et authore la composition
avec le vrai contrat, validée par `npx hyperframes check` avant tout rendu.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# Mots de remplissage par défaut pour l'heuristique de secours (faster-whisper).
# Volontairement restreint aux marqueurs d'hésitation non ambigus — un mot comme
# "voilà" ou "donc" est trop souvent légitime pour être coupé sans relecture humaine.
MOTS_REMPLISSAGE_DEFAUT = ["euh", "heu", "hum", "hmm", "euhm"]

# ============================================================
# ÉTAPE 1 — TRANSCRIPTION + DÉTECTION DES BAFOUILLAGES (GEMINI, SECOURS WHISPER)
# ============================================================

PROMPT_TRANSCRIPTION = """Tu es un assistant de montage vidéo. Regarde intégralement cette vidéo \
et transcris-la avec précision, du début à la fin, sans rien omettre.

Découpe la transcription en segments courts (une phrase ou un groupe de mots cohérent).
Pour chaque segment, donne :
- "debut" et "fin" : timecodes en secondes depuis le début de la vidéo (nombres, précision 0.1s)
- "texte" : la transcription verbatim exacte de ce qui est dit, bafouillages inclus
- "type" : "bafouillage" si le segment contient une hésitation ("euh", "hum", "enfin"...),
  une répétition de mot, un faux départ, un mot coupé ou une reprise de phrase ratée ;
  "propre" dans tous les autres cas.

Réponds UNIQUEMENT avec un tableau JSON de segments, sans texte ni balise autour. Exemple :
[{"debut": 0.0, "fin": 2.3, "texte": "Bonjour à tous", "type": "propre"},
 {"debut": 2.3, "fin": 3.1, "texte": "euh, alors, alors", "type": "bafouillage"}]
"""


def _extraire_json(texte: str) -> list:
    """Extrait un tableau JSON d'une réponse Gemini (retire les fences ```json éventuelles)."""
    texte = texte.strip()
    if texte.startswith("```"):
        texte = texte.split("```")[1]
        if texte.startswith("json"):
            texte = texte[4:]
    debut = texte.find("[")
    fin = texte.rfind("]")
    if debut == -1 or fin == -1:
        raise ValueError(f"Aucun tableau JSON trouvé dans la réponse Gemini : {texte[:200]!r}")
    return json.loads(texte[debut : fin + 1])


def transcrire_video(
    chemin_video: Path,
    cle_api: str = None,
    modele: str = "gemini-2.5-pro",
) -> list[dict]:
    """
    Envoie la vidéo à Gemini, récupère la transcription segmentée avec
    détection des bafouillages. Nécessite `pip install google-genai`.
    """
    try:
        from google import genai
    except ImportError:
        raise ImportError(
            "Le module 'google-genai' est requis. Installez-le avec : pip install google-genai"
        )

    cle = cle_api or os.environ.get("GEMINI_API_KEY")
    if not cle:
        raise ValueError(
            "Aucune clé API Gemini fournie. Passez --cle-api ou définissez la variable "
            "d'environnement GEMINI_API_KEY."
        )

    client = genai.Client(api_key=cle)

    print(f"Envoi de la vidéo à Gemini : {chemin_video}")
    fichier = client.files.upload(file=str(chemin_video))

    # La vidéo est traitée côté Gemini avant d'être utilisable — on attend l'état ACTIF.
    delai_max = 300
    attente = 0
    while fichier.state.name == "PROCESSING":
        if attente >= delai_max:
            raise TimeoutError("Délai dépassé : Gemini n'a pas fini de traiter la vidéo.")
        time.sleep(5)
        attente += 5
        fichier = client.files.get(name=fichier.name)

    if fichier.state.name != "ACTIVE":
        raise RuntimeError(f"Échec du traitement de la vidéo par Gemini : état {fichier.state.name}")

    reponse = client.models.generate_content(
        model=modele,
        contents=[fichier, PROMPT_TRANSCRIPTION],
    )

    segments = _extraire_json(reponse.text)

    # Validation minimale de structure — on ne fait confiance qu'à ce que Gemini renvoie réellement.
    for i, seg in enumerate(segments):
        for cle_requise in ("debut", "fin", "texte", "type"):
            if cle_requise not in seg:
                raise ValueError(f"Segment {i} incomplet (clé '{cle_requise}' manquante) : {seg}")
        seg["type"] = "bafouillage" if seg["type"].strip().lower() == "bafouillage" else "propre"

    return segments


def _mots_normalises(texte: str) -> list[str]:
    return re.findall(r"[a-zàâäéèêëïîôöùûüç']+", texte.lower())


def _est_bafouillage_heuristique(texte: str, mots_remplissage: list[str]) -> bool:
    """
    Heuristique de secours (sans Gemini) : répétition immédiate d'un mot
    ("le le chat"), ou segment composé uniquement de mots de remplissage.
    Volontairement conservatrice pour éviter de couper du contenu réel.
    """
    mots = _mots_normalises(texte)
    if not mots:
        return False
    for i in range(len(mots) - 1):
        if mots[i] == mots[i + 1]:
            return True
    return all(m in mots_remplissage for m in mots)


def transcrire_video_whisper(
    chemin_video: Path,
    modele: str = "small",
    langue: str = "fr",
    mots_remplissage: list = None,
) -> list[dict]:
    """
    Solution de secours 100% locale et gratuite (aucune clé API, aucun abonnement) :
    transcrit avec faster-whisper et repère les bafouillages par heuristique.
    Moins fiable que Gemini sur les cas ambigus — à relire avant de valider les coupes.
    Nécessite : pip install faster-whisper
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise ImportError(
            "Le module 'faster-whisper' est requis pour la solution de secours. "
            "Installez-le avec : pip install faster-whisper"
        )

    mots_remplissage = [m.lower() for m in (mots_remplissage or MOTS_REMPLISSAGE_DEFAUT)]

    print(f"Transcription locale de secours (faster-whisper, modèle '{modele}') : {chemin_video}")
    modele_charge = WhisperModel(modele, device="cpu", compute_type="int8")
    segments_whisper, _info = modele_charge.transcribe(
        str(chemin_video), language=langue, word_timestamps=True, vad_filter=True
    )

    segments = []
    for seg in segments_whisper:
        texte = seg.text.strip()
        if not texte:
            continue
        segments.append({
            "debut": round(seg.start, 2),
            "fin": round(seg.end, 2),
            "texte": texte,
            "type": "bafouillage" if _est_bafouillage_heuristique(texte, mots_remplissage) else "propre",
        })
    return segments


def transcrire_avec_secours(
    chemin_video: Path,
    cle_api: str = None,
    modele_gemini: str = "gemini-2.5-pro",
    modele_whisper: str = "small",
    mots_remplissage: list = None,
    autoriser_secours: bool = True,
) -> tuple:
    """
    Essaie Gemini en premier (meilleure détection, comprend le sens et le contexte).
    Si Gemini échoue (clé absente, quota dépassé, erreur réseau, dépendance manquante)
    et que le secours est autorisé, bascule sur faster-whisper en local.

    Retourne (segments, moteur_utilisé) — le moteur réellement utilisé doit toujours
    apparaître dans le compte rendu final : c'est ce qui rend la coupe automatique
    vérifiable plutôt qu'une boîte noire.
    """
    try:
        segments = transcrire_video(chemin_video, cle_api=cle_api, modele=modele_gemini)
        return segments, "gemini"
    except Exception as e:
        if not autoriser_secours:
            raise
        print(
            f"AVERTISSEMENT: Gemini indisponible ({e}) — bascule sur la solution de "
            f"secours locale et gratuite (faster-whisper).",
            file=sys.stderr,
        )
        segments = transcrire_video_whisper(
            chemin_video, modele=modele_whisper, mots_remplissage=mots_remplissage
        )
        return segments, "whisper"


# ============================================================
# ÉTAPE 2 — CALCUL DU PLAN DE COUPE + DÉCOUPE FFMPEG
# ============================================================

def calculer_plan_de_coupe(
    segments: list[dict],
    duree_totale: float,
    marge_secondes: float = 0.15,
    duree_min_bafouillage: float = 0.3,
) -> list[tuple]:
    """
    À partir des segments Gemini, calcule les plages à CONSERVER (en secondes,
    sur la timeline d'origine). Une marge est retirée de chaque bord d'un
    bafouillage supprimé pour éviter les coupes trop sèches.
    """
    coupures = sorted(
        [
            (s["debut"], s["fin"])
            for s in segments
            if s["type"] == "bafouillage" and (s["fin"] - s["debut"]) >= duree_min_bafouillage
        ],
        key=lambda c: c[0],
    )

    # Fusionner les coupures qui se chevauchent ou se touchent
    fusionnees = []
    for debut, fin in coupures:
        if fusionnees and debut <= fusionnees[-1][1]:
            fusionnees[-1] = (fusionnees[-1][0], max(fusionnees[-1][1], fin))
        else:
            fusionnees.append((debut, fin))

    # Réduire chaque coupure de la marge de sécurité
    reduites = []
    for debut, fin in fusionnees:
        d, f = debut + marge_secondes, fin - marge_secondes
        if f > d:
            reduites.append((d, f))

    # Complément : ce qu'on garde
    garder = []
    curseur = 0.0
    for debut, fin in reduites:
        if debut > curseur:
            garder.append((round(curseur, 2), round(debut, 2)))
        curseur = max(curseur, fin)
    if curseur < duree_totale:
        garder.append((round(curseur, 2), round(duree_totale, 2)))

    return garder


def _duree_video(chemin_video: Path) -> float:
    """Récupère la durée d'une vidéo via ffprobe."""
    if not shutil.which("ffprobe"):
        raise EnvironmentError("ffprobe introuvable. Installez ffmpeg (fournit ffprobe).")
    resultat = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(chemin_video),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(resultat.stdout.strip())


def couper_video(chemin_video: Path, plan_garder: list[tuple], chemin_sortie: Path) -> Path:
    """
    Découpe la vidéo en supprimant tout ce qui n'est pas dans `plan_garder`,
    via un unique passage ffmpeg (trim + concat, ré-encodage pour un raccord précis).
    """
    if not shutil.which("ffmpeg"):
        raise EnvironmentError("ffmpeg introuvable dans le PATH.")
    if not plan_garder:
        raise ValueError("Plan de coupe vide : rien à conserver, vérifiez la transcription.")

    filtres, labels_v, labels_a = [], [], []
    for i, (debut, fin) in enumerate(plan_garder):
        filtres.append(
            f"[0:v]trim=start={debut}:end={fin},setpts=PTS-STARTPTS[v{i}];"
            f"[0:a]atrim=start={debut}:end={fin},asetpts=PTS-STARTPTS[a{i}]"
        )
        labels_v.append(f"[v{i}]")
        labels_a.append(f"[a{i}]")

    n = len(plan_garder)
    concat = "".join(f"{v}{a}" for v, a in zip(labels_v, labels_a))
    filtre_complexe = ";".join(filtres) + f";{concat}concat=n={n}:v=1:a=1[outv][outa]"

    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)
    commande = [
        "ffmpeg", "-y", "-i", str(chemin_video),
        "-filter_complex", filtre_complexe,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-c:a", "aac", str(chemin_sortie),
    ]
    print(f"Découpe ffmpeg : {n} segment(s) conservé(s) sur {len(plan_garder)}")
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        raise RuntimeError(f"Échec ffmpeg :\n{resultat.stderr[-2000:]}")

    return chemin_sortie


# ============================================================
# ÉTAPE 3 — HABILLAGE HYPERFRAMES (SOUS-TITRES, POINTS B-ROLL) + RENDU
# ============================================================

def construire_sous_titres(segments: list[dict], plan_garder: list[tuple]) -> list[dict]:
    """Reprojette les segments 'propre' sur la nouvelle timeline (après coupe)."""
    sous_titres = []
    offset_cumule = 0.0
    for debut_g, fin_g in plan_garder:
        for seg in segments:
            if seg["type"] != "propre":
                continue
            chevauchement_debut = max(seg["debut"], debut_g)
            chevauchement_fin = min(seg["fin"], fin_g)
            if chevauchement_fin > chevauchement_debut:
                sous_titres.append({
                    "debut": round(offset_cumule + (chevauchement_debut - debut_g), 2),
                    "fin": round(offset_cumule + (chevauchement_fin - debut_g), 2),
                    "texte": seg["texte"],
                })
        offset_cumule += fin_g - debut_g
    return sous_titres


def detecter_points_broll(sous_titres: list[dict], mots_cles_broll: list = None) -> list[dict]:
    """
    Repère les sous-titres contenant un mot-clé b-roll configuré. Ne choisit jamais
    l'asset : c'est un point de départ pour l'agent/l'éditeur humain, pas une décision
    créative que ce script peut prendre à leur place.
    """
    mots_cles_broll = mots_cles_broll or []
    points = []
    for st in sous_titres:
        for mot in mots_cles_broll:
            if mot.lower() in st["texte"].lower():
                points.append({"debut": st["debut"], "mot_cle": mot, "contexte": st["texte"]})
    return points


def exporter_sous_titres(
    sous_titres: list[dict],
    chemin_sortie_json: Path,
    mots_cles_broll: list = None,
) -> Path:
    """
    Exporte les sous-titres (déjà reprojetés sur la timeline coupée) et les points
    d'insertion b-roll suggérés, en JSON — pas en HTML HyperFrames. La composition
    elle-même doit être authored par un agent chargeant /hyperframes (contrat réel :
    timeline GSAP enregistrée, data-duration racine, etc. — voir SKILL.md), jamais
    générée à l'aveugle par ce script.
    """
    donnees = {
        "sous_titres": sous_titres,
        "points_broll_suggeres": detecter_points_broll(sous_titres, mots_cles_broll),
    }
    chemin_sortie_json.parent.mkdir(parents=True, exist_ok=True)
    chemin_sortie_json.write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")
    return chemin_sortie_json


# ============================================================
# POINT D'ENTRÉE CLI
# ============================================================

def _charger_config_yaml(chemin: str) -> dict:
    if not chemin:
        return {}
    try:
        import yaml
    except ImportError:
        raise ImportError("Le module 'pyyaml' est requis pour --config. pip install pyyaml")
    data = yaml.safe_load(Path(chemin).read_text(encoding="utf-8")) or {}
    return data.get("montage_video", {})


def main():
    parser = argparse.ArgumentParser(description="Module montage vidéo AKOMA (Gemini + ffmpeg + HyperFrames).")
    sous_parseurs = parser.add_subparsers(dest="commande", required=True)

    p_transcrire = sous_parseurs.add_parser("transcrire", help="Gemini transcrit et repère les bafouillages")
    p_transcrire.add_argument("--video", required=True, type=Path)
    p_transcrire.add_argument("--sortie", required=True, type=Path, help="Chemin du transcript JSON produit")
    p_transcrire.add_argument("--cle-api", default=None)
    p_transcrire.add_argument("--modele", default="gemini-2.5-pro")
    p_transcrire.add_argument("--modele-whisper", default="small", help="Modèle faster-whisper pour le secours")
    p_transcrire.add_argument(
        "--moteur", choices=["auto", "gemini", "whisper"], default="auto",
        help="auto = Gemini avec secours whisper automatique (défaut). "
             "gemini = pas de secours, échoue si Gemini échoue. whisper = force le secours local.",
    )
    p_transcrire.add_argument("--sans-secours", action="store_true", help="Désactive le secours whisper en mode auto")

    p_couper = sous_parseurs.add_parser("couper", help="Découpe la vidéo (retire les bafouillages)")
    p_couper.add_argument("--video", required=True, type=Path)
    p_couper.add_argument("--transcript", required=True, type=Path)
    p_couper.add_argument("--sortie", required=True, type=Path)
    p_couper.add_argument("--marge", type=float, default=0.15)
    p_couper.add_argument("--duree-min-bafouillage", type=float, default=0.3)

    p_habiller = sous_parseurs.add_parser(
        "habiller", help="Exporte les sous-titres + points b-roll (JSON) pour l'agent HyperFrames"
    )
    p_habiller.add_argument("--plan", required=True, type=Path, help="Fichier .plan.json produit par 'couper'")
    p_habiller.add_argument("--sortie", required=True, type=Path, help="Chemin du .json de sous-titres à générer")
    p_habiller.add_argument("--config", default=None, help="clients/<client>/config.yaml")

    p_pipeline = sous_parseurs.add_parser("pipeline", help="Enchaîne les 3 étapes")
    p_pipeline.add_argument("--video", required=True, type=Path)
    p_pipeline.add_argument("--sortie-dir", required=True, type=Path)
    p_pipeline.add_argument("--config", default=None)
    p_pipeline.add_argument("--cle-api", default=None)
    p_pipeline.add_argument(
        "--moteur", choices=["auto", "gemini", "whisper"], default="auto",
        help="auto = Gemini avec secours whisper automatique (défaut).",
    )
    p_pipeline.add_argument("--sans-secours", action="store_true", help="Désactive le secours whisper en mode auto")

    args = parser.parse_args()

    try:
        if args.commande == "transcrire":
            if args.moteur == "whisper":
                segments, moteur_utilise = transcrire_video_whisper(args.video, modele=args.modele_whisper), "whisper"
            elif args.moteur == "gemini":
                segments, moteur_utilise = transcrire_video(args.video, cle_api=args.cle_api, modele=args.modele), "gemini"
            else:
                segments, moteur_utilise = transcrire_avec_secours(
                    args.video, cle_api=args.cle_api, modele_gemini=args.modele,
                    modele_whisper=args.modele_whisper, autoriser_secours=not args.sans_secours,
                )
            args.sortie.parent.mkdir(parents=True, exist_ok=True)
            args.sortie.write_text(
                json.dumps({"moteur": moteur_utilise, "segments": segments}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"✅ Transcript produit ({moteur_utilise}) : {args.sortie} ({len(segments)} segments)")

        elif args.commande == "couper":
            transcript_data = json.loads(args.transcript.read_text(encoding="utf-8"))
            segments = transcript_data["segments"] if isinstance(transcript_data, dict) else transcript_data
            duree_totale = _duree_video(args.video)
            plan_garder = calculer_plan_de_coupe(
                segments, duree_totale, marge_secondes=args.marge,
                duree_min_bafouillage=args.duree_min_bafouillage,
            )
            couper_video(args.video, plan_garder, args.sortie)
            chemin_plan = args.sortie.with_suffix(".plan.json")
            chemin_plan.write_text(
                json.dumps(
                    {
                        "moteur": transcript_data.get("moteur", "inconnu") if isinstance(transcript_data, dict) else "inconnu",
                        "segments": segments,
                        "plan_garder": plan_garder,
                    },
                    ensure_ascii=False, indent=2,
                ),
                encoding="utf-8",
            )
            print(f"✅ Vidéo coupée : {args.sortie}")
            print(f"✅ Plan de coupe sauvegardé : {chemin_plan}")

        elif args.commande == "habiller":
            plan_data = json.loads(args.plan.read_text(encoding="utf-8"))
            sous_titres = construire_sous_titres(plan_data["segments"], plan_data["plan_garder"])
            config = _charger_config_yaml(args.config)
            mots_cles = config.get("mots_cles_broll", [])
            exporter_sous_titres(sous_titres, args.sortie, mots_cles)
            print(f"✅ Sous-titres + points b-roll exportés : {args.sortie}")
            print("⏭️  Composition HyperFrames à authorer via l'agent (skill /hyperframes), pas par ce script.")

        elif args.commande == "pipeline":
            config = _charger_config_yaml(args.config)
            args.sortie_dir.mkdir(parents=True, exist_ok=True)

            chemin_transcript = args.sortie_dir / "transcript.json"
            if args.moteur == "whisper":
                segments, moteur_utilise = transcrire_video_whisper(
                    args.video, modele=config.get("modele_whisper", "small"),
                    mots_remplissage=config.get("mots_de_remplissage"),
                ), "whisper"
            elif args.moteur == "gemini":
                segments, moteur_utilise = transcrire_video(
                    args.video, cle_api=args.cle_api, modele=config.get("gemini_modele", "gemini-2.5-pro")
                ), "gemini"
            else:
                segments, moteur_utilise = transcrire_avec_secours(
                    args.video, cle_api=args.cle_api,
                    modele_gemini=config.get("gemini_modele", "gemini-2.5-pro"),
                    modele_whisper=config.get("modele_whisper", "small"),
                    mots_remplissage=config.get("mots_de_remplissage"),
                    autoriser_secours=not args.sans_secours,
                )
            chemin_transcript.write_text(
                json.dumps({"moteur": moteur_utilise, "segments": segments}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"✅ Transcript produit ({moteur_utilise}) : {chemin_transcript} ({len(segments)} segments)")
            if moteur_utilise == "whisper":
                print(
                    "⚠️  Détection des bafouillages par heuristique locale (moins fine que Gemini) — "
                    "relire le transcript avant de valider les coupes.",
                    file=sys.stderr,
                )

            duree_totale = _duree_video(args.video)
            plan_garder = calculer_plan_de_coupe(
                segments, duree_totale,
                marge_secondes=config.get("marge_coupe_secondes", 0.15),
                duree_min_bafouillage=config.get("duree_min_bafouillage", 0.3),
            )
            chemin_coupe = args.sortie_dir / "coupe.mp4"
            couper_video(args.video, plan_garder, chemin_coupe)
            print(f"✅ Vidéo coupée : {chemin_coupe}")

            sous_titres = construire_sous_titres(segments, plan_garder)
            chemin_sous_titres = args.sortie_dir / "sous_titres.json"
            exporter_sous_titres(sous_titres, chemin_sous_titres, config.get("mots_cles_broll", []))
            print(f"✅ Sous-titres + points b-roll exportés : {chemin_sous_titres}")
            print(
                "⏭️  Habillage HyperFrames (sous-titres, b-roll, zooms, plans de coupe) à authorer "
                "par un agent chargeant la skill /hyperframes sur la vidéo coupée "
                f"({chemin_coupe}) et {chemin_sous_titres}. Valider avec `npx hyperframes check` "
                "puis `npx hyperframes preview --background` avant tout `npx hyperframes render`."
            )

    except Exception as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
