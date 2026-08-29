# Commande /audit

Arguments : `<client> [process]`

Produis un diagnostic flash pour le client indiqué, sur le process précisé (ou sur l'ensemble des opérations si non précisé).

## Étapes

1. **Cadrer** : lis `clients/<client>/brief-client.md` et `clients/<client>/config.yaml`
   - Si le dossier n'existe pas : crée `clients/<client>/` depuis `clients/_TEMPLATE/` et demande les informations manquantes (🟡)
2. **Déléguer** : lance le sous-agent `architecte-process` avec le client, le process et les chemins de fichiers
3. **Rédiger** le markdown depuis `modeles/audit-flash.md` en intégrant les résultats du sous-agent
4. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-audit.md --sortie sorties/<client>/Audit_<process>_AAAA-MM.docx --pdf
   ```
5. **Vérifier** : aucun `À CONFIRMER` dans un document final, aucun tableau qui déborde
6. **Inscrire** dans `journal/DECISIONS.md` : `AAAA-MM-JJ · <client> · audit · <process ou général>`

## Compte rendu obligatoire

```
✅ Fait      : Audit flash <client> — <process> généré (Word + PDF)
⚠️ À valider : <question précise si besoin, sinon « Aucun »>
⏭️ Suivant   : Présenter à <client> / Kathya valide avant envoi
⏱️ Gagné     : ~2h de collecte et mise en forme
```
