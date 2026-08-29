# Commande /reporting

Arguments : `<client> <mois>` (format mois : AAAA-MM)

Produis le rapport d'avancement mensuel pour le client.

## Étapes

1. **Cadrer** : lis `clients/<client>/brief-client.md` et `clients/<client>/config.yaml`
2. **Collecter les données** : cherche dans `sorties/<client>/` les livrables du mois, et dans `journal/DECISIONS.md` les actions du mois
3. Si le module métier est configuré (ex. conciergerie) : lance le sous-agent correspondant
4. **Rédiger** le markdown depuis `modeles/rapport-avancement.md`
5. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-reporting.md --sortie sorties/<client>/Rapport_<client>_<mois>.docx --pdf
   ```
6. **Inscrire** dans `journal/DECISIONS.md`

## ⚠️ Document 🔴

Le rapport part au client : validation Kathya obligatoire avant envoi.

## Compte rendu obligatoire

```
✅ Fait      : Rapport <mois> / <client> généré (Word + PDF)
⚠️ À valider : <chiffres à confirmer ou « Aucun »>
⏭️ Suivant   : Kathya valide avant envoi client
⏱️ Gagné     : ~2h de collecte et rédaction
```
