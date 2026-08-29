# Commande /brief

Affiche les priorités du jour : décisions récentes, tâches en cours, points d'attention.

## Usage

```
/brief
```

Aucun argument requis. La commande lit l'état du système AKOMA et produit un briefing matinal.

## Étapes à exécuter

1. **Lire les décisions récentes** : ouvrir `journal/DECISIONS.md` et extraire les 10 dernières lignes.

2. **Scanner les dossiers clients** : pour chaque dossier dans `clients/` (hors `_TEMPLATE`), vérifier s'il existe des fichiers modifiés dans les 7 derniers jours.

3. **Identifier les tâches en cours** si ClickUp est connecté :
   - Appeler `mcp__ClickUp__clickup_filter_tasks` avec statut "in progress"
   - Lister les tâches assignées à AKOMA DIGITAL avec échéance cette semaine

4. **Identifier les tâches Notion** si connecté :
   - Chercher les pages récemment modifiées liées aux clients actifs

5. **Produire le briefing** au format :

```
# Briefing AKOMA — [DATE]

## Décisions récentes (7 derniers jours)
[liste des dernières décisions depuis journal/DECISIONS.md]

## Clients actifs
[liste des clients avec dernière activité]

## Tâches en cours
[liste des tâches avec échéance, depuis ClickUp/Notion si disponible]

## Points d'attention
[délais proches, tâches bloquées, alertes]

## Suggestion du jour
[une action prioritaire à engager aujourd'hui]
```

6. **Statut final** :
   ```
   ✅ Brief du [DATE] prêt
   ⏭️ Suivant : [action prioritaire du jour]
   ```

## Règles

- Ne pas inventer de tâches. Si ClickUp/Notion ne sont pas connectés, signaler "Connexion non disponible".
- Se concentrer sur ce qui est actionnable aujourd'hui.
- Utiliser le français.
- Le brief doit tenir en une page.
