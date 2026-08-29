# Commande /cadrage

Arguments : `<client> <projet>`

Produis une note de cadrage pour le projet indiqué.

## Étapes

1. **Cadrer** : lis `clients/<client>/brief-client.md` et `clients/<client>/config.yaml`
2. **Collecter** les informations manquantes (périmètre, livrables, rôles, jalons, risques) — pose UNE question par manque (🟡)
3. **Rédiger** le markdown depuis `modeles/note-cadrage.md`
4. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py sorties/<client>/brouillon-cadrage.md --sortie sorties/<client>/Cadrage_<projet>_AAAA-MM.docx --pdf
   ```
5. **Inscrire** dans `journal/DECISIONS.md`

## ⚠️ Avant d'envoyer au client

La note de cadrage est un document 🔴 : validation explicite de Kathya obligatoire avant tout envoi.

## Compte rendu obligatoire

```
✅ Fait      : Note de cadrage <projet> / <client> générée
⚠️ À valider : <question ou validation Kathya requise>
⏭️ Suivant   : Kathya relit et donne le feu vert avant envoi
⏱️ Gagné     : ~2h de structuration
```
