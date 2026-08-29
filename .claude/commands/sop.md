# Commande /sop

Arguments : `<client> <process>`

Produis une SOP (Standard Operating Procedure) d'une page pour le process indiqué.

## Étapes

1. **Cadrer** : lis `clients/<client>/brief-client.md` et `clients/<client>/config.yaml`
2. **Collecter** : si des informations manquent sur le process, pose UNE question précise (🟡)
3. **Rédiger** le markdown depuis `modeles/sop.md` :
   - Chaque étape reçoit un tag : 🟢 (autonome), 🟡 (vérification), 🔴 (validation obligatoire)
   - Inclure le mode dégradé (que faire si l'outil/personne n'est pas disponible)
4. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-sop.md --sortie sorties/<client>/SOP_<process>_AAAA-MM.docx --pdf
   ```
5. **Inscrire** dans `journal/DECISIONS.md`

## Compte rendu obligatoire

```
✅ Fait      : SOP <process> générée pour <client> (Word + PDF)
⚠️ À valider : <question ou « Aucun »>
⏭️ Suivant   : Faire valider par le responsable du process
⏱️ Gagné     : ~1h30 de rédaction et mise en forme
```
