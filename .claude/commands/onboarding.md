# Commande /onboarding

Arguments : `<client> <presta>`

Crée le dossier client et produis un pack de démarrage 48h pour l'onboarding d'un prestataire.

## Étapes

1. **Créer le dossier client** (si absent) en copiant `clients/_TEMPLATE/` vers `clients/<client>/`
2. **Collecter** : lis `clients/<client>/brief-client.md` — si vide, pose les questions essentielles (🟡)
3. **Rédiger** le markdown depuis `modeles/pack-onboarding.md` en personnalisant pour `<presta>`
4. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-onboarding.md --sortie sorties/<client>/Onboarding_<presta>_AAAA-MM.docx --pdf
   ```
5. **Inscrire** dans `journal/DECISIONS.md`

## ⚠️ Document 🔴

Le pack onboarding part à un tiers (le prestataire) : validation Kathya obligatoire avant envoi.

## Compte rendu obligatoire

```
✅ Fait      : Pack onboarding <presta> / <client> généré + dossier créé
⚠️ À valider : Kathya valide avant envoi à <presta>
⏭️ Suivant   : Envoyer après validation
⏱️ Gagné     : ~1h30 de préparation
```
