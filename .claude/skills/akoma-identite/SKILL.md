---
name: akoma-identite
description: Charte visuelle et règles de production des documents AKOMA DIGITAL (Word, Excel, PowerPoint, PDF). À utiliser dès qu'un livrable destiné à Kathya ou à un client doit être créé ou mis en forme — rapport, note de cadrage, SOP, compte rendu, proposition commerciale, tableau de suivi.
---

# Identité AKOMA DIGITAL — production de documents

Signature : **Structurer. Transformer. Piloter l'impact.** · Symbole : l'ankh (akoma).
Le document doit être reconnaissable en une seconde : sobre, chaud, terreux, jamais bariolé.

## Palette (planche d'identité officielle)

| Rôle | Nom | Hex |
|---|---|---|
| Texte courant, titres forts | Espresso | `#3A2418` |
| Titres, en-têtes de section | Brun cacao | `#5E3A1E` |
| Filets, en-têtes de tableau, accents | Terracotta | `#B5642F` |
| Mentions secondaires, légendes | Ocre doré | `#CE9A5C` |
| Aplats, séparateurs | Sable | `#E4D2B8` |
| Lignes de tableau paires | Crème | `#F4E9D8` |
| Fond de bloc, encadrés | Lin | `#FBF6EE` |

Jamais de bleu, de vert, ni de gris froid. Un seul accent vif par page : le terracotta.

## Typographie

- Marque (Canva, visuels, LinkedIn) : Playfair Display (titres), Montserrat (sous-titres),
  Lato (texte), Cormorant Garamond italique (citations). Brand kit Canva `kAGZ1T7DBSw`.
- **Documents de production (Word/Excel) : Arial**, parce qu'il s'affiche correctement chez
  tous les clients. Titre 18–20 pt, section 14–16 pt, texte 10 pt, légende 8–9 pt.

## Règles de mise en page

- A4 portrait, marges 2 cm.
- En-tête : logo `assets/logo_akoma.png` centré (3,2 cm), baseline en ocre italique,
  ligne « Client · type de document », filet ocre.
- Titres de section numérotés, brun cacao, soulignés d'un filet terracotta.
- Tableaux : en-tête terracotta texte blanc, lignes alternées crème / lin, chiffres à droite.
  Largeurs de colonnes fixées explicitement (total 17 cm) — jamais d'autofit.
- Pied de page : `AKOMA DIGITAL LTD · akoma.digital.ltd@gmail.com · Structurer. Transformer. Piloter l'impact.`
- Montants : `1 234,56 €` (espace fine, virgule décimale) · roupies : `52 838 Rs`.
- Dates : `31/05/2026` · mois en toutes lettres dans les titres : « mai 2026 ».

## Comment produire

Ne mets jamais un document en forme à la main. Tu rédiges du markdown, le moteur produit :

```bash
python3 scripts/livrable.py <fichier.md> --sortie sorties/<client>/<Nom>.docx --pdf
```

Syntaxe reconnue : en-tête YAML (titre, client, type, date, reference), `#` titre,
`##` section numérotée à filet, `###` sous-titre, listes, `- [ ]` cases à cocher,
tableaux markdown, `>` encadré lin, `***` saut de page, `**gras**`.

Pour un module métier chiffré qui produit ses propres documents, `scripts/rapport_docx.py`
montre comment appeler directement les helpers de charte.

Dépendances : `python-docx`, `openpyxl`, `pyyaml`, `pandas`.

## Contrôle qualité obligatoire

Après génération, convertis et regarde le résultat avant de le transmettre :

```bash
soffice --headless --convert-to pdf sorties/<client>/<mois>/<fichier>.docx
pdftoppm -jpeg -r 90 <fichier>.pdf page   # puis lis page-1.jpg
```

Trois défauts à traquer : en-tête de colonne qui passe à la ligne, tableau qui déborde
de la marge, texte à compléter oublié (`à compléter`, `À CONFIRMER`) dans un document
présenté comme final.

## Nommage et rangement

`Type_Objet_AAAA-MM.docx` — exemples : `Rapport_Freesia_2_2026-05.docx`,
`Synthese_portefeuille_2026-05.docx`, `CR_2026-05-14_cadrage.md`.
Rangement : `sorties/<client>/<période>/`. Rien à la racine.
