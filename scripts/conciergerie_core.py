#!/usr/bin/env python3
"""
conciergerie_core.py — Module métier Conciergerie AKOMA DIGITAL LTD
Calcule le reporting mensuel à partir d'un fichier CSV ou YAML de réservations.

Usage:
    python3 conciergerie_core.py --client NOM --mois 2026-08 --taux 0.10 --fichier donnees.csv
    python3 conciergerie_core.py --client NOM --mois 2026-08 --taux 0.10 --fichier donnees.yaml

Structure CSV attendue (colonnes minimales):
    propriete, date_arrivee, date_depart, montant_brut, statut
    (statut: confirmee, annulee, en_attente)

Structure YAML attendue:
    reservations:
      - propriete: "Nom Propriété"
        date_arrivee: "2026-08-01"
        date_depart: "2026-08-05"
        montant_brut: 450.00
        statut: "confirmee"
"""

import argparse
import csv
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import Optional

try:
    import yaml
    YAML_DISPONIBLE = True
except ImportError:
    YAML_DISPONIBLE = False


# ============================================================
# STRUCTURES DE DONNÉES
# ============================================================

class Reservation:
    """Représente une réservation locative."""

    def __init__(
        self,
        propriete: str,
        date_arrivee: date,
        date_depart: date,
        montant_brut: float,
        statut: str = "confirmee",
    ):
        self.propriete = propriete
        self.date_arrivee = date_arrivee
        self.date_depart = date_depart
        self.montant_brut = montant_brut
        self.statut = statut.lower().strip()

    @property
    def nuits(self) -> int:
        """Nombre de nuits du séjour."""
        delta = self.date_depart - self.date_arrivee
        return max(0, delta.days)

    @property
    def est_confirmee(self) -> bool:
        return self.statut in ("confirmee", "confirmed", "validee", "payee")

    def __repr__(self) -> str:
        return (
            f"Reservation({self.propriete!r}, {self.date_arrivee} → {self.date_depart}, "
            f"{self.montant_brut}€, {self.statut})"
        )


# ============================================================
# CHARGEMENT DES DONNÉES
# ============================================================

def _parser_date(valeur: str) -> date:
    """Parse une date depuis plusieurs formats courants."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(valeur.strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    raise ValueError(f"Format de date non reconnu : {valeur!r}")


def charger_csv(chemin: Path) -> list[Reservation]:
    """Charge les réservations depuis un fichier CSV."""
    reservations = []
    try:
        with open(chemin, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            # Normaliser les noms de colonnes (minuscules, sans espaces)
            fieldnames_norm = {}
            if reader.fieldnames:
                for fn in reader.fieldnames:
                    fieldnames_norm[fn.lower().replace(" ", "_").strip()] = fn

            for i, row in enumerate(reader, start=2):
                # Normaliser les clés
                row_norm = {k.lower().replace(" ", "_").strip(): v for k, v in row.items()}

                try:
                    propriete = (
                        row_norm.get("propriete")
                        or row_norm.get("property")
                        or row_norm.get("logement")
                        or "Propriété inconnue"
                    )
                    date_arrivee_str = (
                        row_norm.get("date_arrivee")
                        or row_norm.get("arrivee")
                        or row_norm.get("checkin")
                        or row_norm.get("check_in")
                        or ""
                    )
                    date_depart_str = (
                        row_norm.get("date_depart")
                        or row_norm.get("depart")
                        or row_norm.get("checkout")
                        or row_norm.get("check_out")
                        or ""
                    )
                    montant_str = (
                        row_norm.get("montant_brut")
                        or row_norm.get("montant")
                        or row_norm.get("ca")
                        or row_norm.get("revenue")
                        or "0"
                    )
                    statut = (
                        row_norm.get("statut")
                        or row_norm.get("status")
                        or "confirmee"
                    )

                    if not date_arrivee_str or not date_depart_str:
                        print(f"AVERTISSEMENT: Ligne {i} ignorée (dates manquantes)", file=sys.stderr)
                        continue

                    montant = float(str(montant_str).replace(",", ".").replace("€", "").replace("£", "").strip() or 0)
                    reservations.append(
                        Reservation(
                            propriete=str(propriete).strip(),
                            date_arrivee=_parser_date(date_arrivee_str),
                            date_depart=_parser_date(date_depart_str),
                            montant_brut=montant,
                            statut=str(statut),
                        )
                    )
                except (ValueError, KeyError) as e:
                    print(f"AVERTISSEMENT: Ligne {i} ignorée ({e})", file=sys.stderr)

    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier CSV introuvable : {chemin}")
    except Exception as e:
        raise RuntimeError(f"Erreur lecture CSV ({chemin}): {e}")

    return reservations


def charger_yaml(chemin: Path) -> list[Reservation]:
    """Charge les réservations depuis un fichier YAML."""
    if not YAML_DISPONIBLE:
        raise ImportError("Le module 'pyyaml' est requis pour lire les fichiers YAML. pip install pyyaml")

    try:
        with open(chemin, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Fichier YAML introuvable : {chemin}")
    except yaml.YAMLError as e:
        raise ValueError(f"Erreur de parsing YAML : {e}")

    reservations_data = (
        data.get("reservations")
        or data.get("bookings")
        or (data if isinstance(data, list) else [])
    )

    reservations = []
    for i, item in enumerate(reservations_data, start=1):
        try:
            propriete = (
                item.get("propriete")
                or item.get("property")
                or item.get("logement")
                or "Propriété inconnue"
            )
            date_arrivee = _parser_date(str(item.get("date_arrivee") or item.get("arrivee") or item.get("checkin", "")))
            date_depart = _parser_date(str(item.get("date_depart") or item.get("depart") or item.get("checkout", "")))
            montant = float(item.get("montant_brut") or item.get("montant") or item.get("ca") or 0)
            statut = str(item.get("statut") or item.get("status") or "confirmee")
            reservations.append(
                Reservation(
                    propriete=str(propriete).strip(),
                    date_arrivee=date_arrivee,
                    date_depart=date_depart,
                    montant_brut=montant,
                    statut=statut,
                )
            )
        except (ValueError, KeyError, TypeError) as e:
            print(f"AVERTISSEMENT: Entrée YAML {i} ignorée ({e})", file=sys.stderr)

    return reservations


def charger_donnees(chemin_fichier: str) -> list[Reservation]:
    """Charge les réservations depuis un CSV ou YAML selon l'extension."""
    chemin = Path(chemin_fichier)
    ext = chemin.suffix.lower()
    if ext in (".yaml", ".yml"):
        return charger_yaml(chemin)
    elif ext == ".csv":
        return charger_csv(chemin)
    else:
        # Tentative CSV par défaut
        try:
            return charger_csv(chemin)
        except Exception:
            if YAML_DISPONIBLE:
                return charger_yaml(chemin)
            raise ValueError(f"Format non reconnu : {ext}. Utilisez .csv ou .yaml")


# ============================================================
# CALCULS MÉTIER
# ============================================================

def filtrer_par_mois(reservations: list[Reservation], mois: str) -> list[Reservation]:
    """
    Filtre les réservations dont la date d'arrivée est dans le mois donné.
    mois: format "YYYY-MM"
    """
    try:
        annee, mois_num = int(mois[:4]), int(mois[5:7])
    except (ValueError, IndexError):
        raise ValueError(f"Format de mois invalide : {mois!r}. Attendu : YYYY-MM")

    return [
        r for r in reservations
        if r.date_arrivee.year == annee and r.date_arrivee.month == mois_num
    ]


def jours_dans_mois(mois: str) -> int:
    """Retourne le nombre de jours dans le mois."""
    from calendar import monthrange
    annee, mois_num = int(mois[:4]), int(mois[5:7])
    return monthrange(annee, mois_num)[1]


def calculer_reporting(
    client: str,
    mois: str,
    taux_commission: float,
    fichier_donnees: str,
) -> dict:
    """
    Calcule le reporting mensuel de conciergerie.

    Args:
        client: Nom ou identifiant du client
        mois: Mois au format "YYYY-MM"
        taux_commission: Taux de commission AKOMA (ex: 0.10 pour 10%)
        fichier_donnees: Chemin vers le fichier CSV ou YAML

    Returns:
        Dict avec toutes les métriques calculées.
        Les chiffres sont issus exclusivement des données fournies.
    """
    # Chargement
    toutes_reservations = charger_donnees(fichier_donnees)
    reservations_mois = filtrer_par_mois(toutes_reservations, mois)
    reservations_confirmees = [r for r in reservations_mois if r.est_confirmee]

    # Métriques globales
    nb_sejours = len(reservations_confirmees)
    nuits_totales = sum(r.nuits for r in reservations_confirmees)
    ca_brut = sum(r.montant_brut for r in reservations_confirmees)
    commission = round(ca_brut * taux_commission, 2)
    ca_net_client = round(ca_brut - commission, 2)

    # Taux d'occupation (basé sur les nuits disponibles dans le mois)
    nb_jours_mois = jours_dans_mois(mois)
    proprietes = list(set(r.propriete for r in toutes_reservations))
    nb_proprietes = len(proprietes) if proprietes else 1
    nuits_disponibles = nb_jours_mois * nb_proprietes
    taux_occupation = round((nuits_totales / nuits_disponibles) * 100, 1) if nuits_disponibles > 0 else 0.0

    # Détail par propriété
    detail_proprietes = {}
    for r in reservations_confirmees:
        if r.propriete not in detail_proprietes:
            detail_proprietes[r.propriete] = {
                "sejours": 0,
                "nuits": 0,
                "ca_brut": 0.0,
            }
        detail_proprietes[r.propriete]["sejours"] += 1
        detail_proprietes[r.propriete]["nuits"] += r.nuits
        detail_proprietes[r.propriete]["ca_brut"] = round(
            detail_proprietes[r.propriete]["ca_brut"] + r.montant_brut, 2
        )

    # Réservations annulées sur le mois
    nb_annulations = len([r for r in reservations_mois if not r.est_confirmee])

    return {
        "client": client,
        "mois": mois,
        "taux_commission": taux_commission,
        "fichier_donnees": fichier_donnees,
        "nb_sejours": nb_sejours,
        "nuits_totales": nuits_totales,
        "ca_brut": round(ca_brut, 2),
        "commission_akoma": commission,
        "ca_net_client": ca_net_client,
        "taux_occupation_pct": taux_occupation,
        "nb_proprietes": nb_proprietes,
        "nb_annulations": nb_annulations,
        "detail_proprietes": detail_proprietes,
        "total_reservations_chargees": len(toutes_reservations),
        "reservations_mois_total": len(reservations_mois),
    }


def formater_rapport(resultats: dict) -> str:
    """Formate les résultats en texte lisible."""
    r = resultats
    lignes = [
        f"# Reporting Conciergerie — {r['client']} — {r['mois']}",
        "",
        "## Résumé exécutif",
        f"- Nombre de séjours confirmés : {r['nb_sejours']}",
        f"- Nuits totales : {r['nuits_totales']}",
        f"- Taux d'occupation : {r['taux_occupation_pct']}%",
        f"- Chiffre d'affaires brut : {r['ca_brut']:.2f} €",
        f"- Commission AKOMA ({r['taux_commission']*100:.1f}%) : {r['commission_akoma']:.2f} €",
        f"- CA net client : {r['ca_net_client']:.2f} €",
        f"- Annulations sur le mois : {r['nb_annulations']}",
        "",
    ]

    if r["detail_proprietes"]:
        lignes += [
            "## Détail par propriété",
            "",
            "| Propriété | Séjours | Nuits | CA brut |",
            "|-----------|---------|-------|---------|" ,
        ]
        for prop, d in r["detail_proprietes"].items():
            lignes.append(f"| {prop} | {d['sejours']} | {d['nuits']} | {d['ca_brut']:.2f} € |")
        lignes.append("")

    lignes += [
        "## Données sources",
        f"- Fichier : {r['fichier_donnees']}",
        f"- Réservations totales chargées : {r['total_reservations_chargees']}",
        f"- Réservations sur le mois : {r['reservations_mois_total']}",
    ]

    return "\n".join(lignes)


# ============================================================
# POINT D'ENTRÉE CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Calcule le reporting mensuel de conciergerie AKOMA."
    )
    parser.add_argument("--client", required=True, help="Nom du client")
    parser.add_argument("--mois", required=True, help="Mois au format YYYY-MM")
    parser.add_argument(
        "--taux",
        type=float,
        required=True,
        help="Taux de commission AKOMA (ex: 0.10 pour 10%%)",
    )
    parser.add_argument("--fichier", required=True, help="Chemin vers le CSV ou YAML de réservations")
    parser.add_argument("--json", action="store_true", help="Sortie en JSON (pour intégration)")
    args = parser.parse_args()

    try:
        resultats = calculer_reporting(
            client=args.client,
            mois=args.mois,
            taux_commission=args.taux,
            fichier_donnees=args.fichier,
        )
    except FileNotFoundError as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"ERREUR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERREUR inattendue: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(resultats, ensure_ascii=False, indent=2, default=str))
    else:
        print(formater_rapport(resultats))


if __name__ == "__main__":
    main()
