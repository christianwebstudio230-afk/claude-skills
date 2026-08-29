# Commande /cr

Arguments : `<réunion>` (ex: "réunion Freesia 2026-08-29")

Rédige le compte rendu de réunion et crée les tâches dans Notion/ClickUp.

## Étapes

1. **Collecter** : demande le résumé ou la transcription de la réunion si non fourni
2. **Identifier** : client concerné, décisions prises, actions (qui / quoi / quand)
3. **Rédiger** le markdown depuis `modeles/compte-rendu.md`
4. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-cr.md --sortie sorties/<client>/CR_AAAA-MM-JJ_<sujet>.docx --pdf
   ```
5. **Créer les tâches** dans Notion (base Suivi & CR `5a9e895f`) et ClickUp (liste Suivi `901523916069`) pour chaque action identifiée
6. **Inscrire** dans `journal/DECISIONS.md`

## Compte rendu obligatoire

```
✅ Fait      : CR <réunion> rédigé + <N> tâches créées
⚠️ À valider : <point ambigu ou « Aucun »>
⏭️ Suivant   : Partager le CR aux participants
⏱️ Gagné     : ~45 min de rédaction et saisie
```
