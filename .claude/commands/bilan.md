# Commande /bilan

Produit le bilan hebdomadaire AKOMA avec KPIs et synthèse de la semaine.

## Usage

```
/bilan
```

Optionnel­lement : `/bilan semaine 35` ou `/bilan 2026-08-25/2026-08-29`.

## Étapes à exécuter

1. **Déterminer la période** : semaine en cours par défaut, ou période spécifiée dans les arguments. Calculer lundi-vendredi de la semaine.

2. **Collecter les données** :
   - Lire `journal/DECISIONS.md` pour les décisions de la semaine
   - Lister les livrables produits (fichiers créés dans `clients/*/livrables/` sur la période)
   - Compter les clients actifs (dossiers avec activité sur la semaine)
   - Récupérer les tâches complétées depuis ClickUp si connecté

3. **Calculer les KPIs** :
   - Nombre de livrables produits
   - Nombre de clients servis
   - Nombre de décisions journalisées
   - Nombre de tâches clôturées (si ClickUp disponible)
   - Estimation de valeur créée (en heures économisées, si calculable)

4. **Rédiger le bilan** au format :

```
# Bilan Hebdomadaire AKOMA — Semaine [N] — [DATE_DEBUT] au [DATE_FIN]

## Synthèse en 3 phrases
[Ce qui a avancé, ce qui est bloqué, ce qui est prioritaire la semaine prochaine]

## Réalisations de la semaine
| Livrable | Client | Date | Impact |
|----------|--------|------|--------|
| ...      | ...    | ...  | ...    |

## KPIs de la semaine
| Métrique | Valeur | vs Semaine précédente |
|----------|--------|-----------------------|
| Livrables produits | X | — |
| Clients actifs | X | — |
| Décisions prises | X | — |
| Tâches clôturées | X | — |

## Ce qui a bien fonctionné
[2-3 points positifs]

## Ce qui mérite attention
[1-2 points d'amélioration]

## Priorités semaine prochaine
1. [Action 1]
2. [Action 2]
3. [Action 3]
```

5. **Statut final** :
   ```
   ✅ Bilan semaine [N] produit
   ⏭️ Suivant : [priorité n°1 de la semaine prochaine]
   ⏱️ Gagné : [temps de synthèse économisé]
   ```

## Règles

- Ne pas inventer de chiffres. Marquer "ND" si une métrique n'est pas disponible.
- Utiliser le français.
- Le bilan ne doit pas dépasser 2 pages.
