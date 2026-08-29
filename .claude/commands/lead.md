# Commande /lead

Qualifie un lead selon les 7 niches AKOMA et produit une fiche de qualification.

## Usage

```
/lead $ARGUMENTS
```

`$ARGUMENTS` doit contenir : nom du prospect, secteur, et optionnellement : taille, CA estimé, problème exprimé, canal d'acquisition.

## Les 7 niches AKOMA

1. **Conciergerie locative** — gestion Airbnb/courte durée, propriétaires multi-biens
2. **Restauration / Food** — restaurants, traiteurs, dark kitchens
3. **PME en croissance** — 5-50 salariés, besoin de structuration opérationnelle
4. **Professions libérales** — avocats, consultants, coachs, thérapeutes
5. **Commerce de détail** — boutiques physiques, e-commerce hybride
6. **Associations / ONG** — structuration, reporting bailleurs, gouvernance
7. **Immobilier / Promotion** — agences, promoteurs, gestionnaires de patrimoine

## Étapes à exécuter

1. **Analyser les arguments** : extraire nom, secteur, taille, problème exprimé.

2. **Classifier dans une niche** : déterminer la niche principale et, si pertinent, une niche secondaire.

3. **Scorer le lead** sur 5 critères (note 1-5) :
   - **Urgence** : besoin exprimé et délai de décision
   - **Budget** : capacité d'investissement estimée
   - **Fit** : alignement avec l'offre AKOMA
   - **Accès décideur** : interlocuteur = décideur ?
   - **Scalabilité** : potentiel de mission longue durée

4. **Produire la fiche de qualification** :

```
# Fiche Lead — [NOM PROSPECT]

**Date** : [date]
**Niche** : [niche principale] — [niche secondaire si applicable]
**Score global** : [total/25] — [🔴 Froid / 🟡 Tiède / 🟢 Chaud]

## Informations clés
- Secteur : [secteur]
- Taille : [taille estimée]
- Problème exprimé : [verbatim ou reformulation]
- Canal d'acquisition : [source du lead]

## Scoring
| Critère | Note | Justification |
|---------|------|---------------|
| Urgence | /5 | ... |
| Budget | /5 | ... |
| Fit AKOMA | /5 | ... |
| Accès décideur | /5 | ... |
| Scalabilité | /5 | ... |
| **TOTAL** | **/25** | |

## Recommandation
- **Action** : [Contacter / Nourrir / Disqualifier]
- **Prochaine étape** : [action précise + délai]
- **Offre d'entrée suggérée** : [audit flash / cadrage / module métier]
- **Argument principal** : [angle d'approche adapté au problème exprimé]
```

5. **Sauvegarder** dans `clients/[NOM_PROSPECT]/brief-client.md` (créer le dossier depuis `_TEMPLATE` si lead qualifié 🟢).

6. **Statut final** :
   ```
   ✅ Fait : Lead [NOM] qualifié — Score [X/25] — [Chaud/Tiède/Froid]
   ⏭️ Suivant : [action recommandée]
   ```

## Règles

- Score 18-25 : Chaud 🟢 → contacter dans les 48h
- Score 10-17 : Tiède 🟡 → nourrir avec du contenu, relancer dans 2 semaines
- Score 0-9 : Froid 🔴 → archiver ou disqualifier
- Utiliser le français.
- Ne pas inventer d'informations : noter "Inconnu" si la donnée est absente.
