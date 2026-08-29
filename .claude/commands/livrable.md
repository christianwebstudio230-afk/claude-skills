# Commande /livrable

Arguments : `<sujet ou chemin vers .md>`

Produis n'importe quel document à l'identité AKOMA.

## Étapes

1. Si l'argument est un chemin `.md` existant : utilise-le directement
2. Sinon : rédige le markdown pour le sujet demandé (demande client et type si absents)
3. **Générer** le livrable :
   ```bash
   python3 scripts/livrable.py <fichier.md> --sortie sorties/<client>/<Nom_AAAA-MM>.docx --pdf
   ```
4. **Vérifier** : aucun `À CONFIRMER` oublié, aucun tableau qui déborde, en-têtes lisibles
5. **Inscrire** dans `journal/DECISIONS.md` si livrable significatif

## Nommage

`Type_Objet_AAAA-MM.docx` — ex: `Note_strategie_2026-08.docx`, `Proposition_Freesia_2026-08.docx`

## Compte rendu obligatoire

```
✅ Fait      : <Nom du document> généré (Word + PDF)
⚠️ À valider : <point ou « Aucun »>
⏭️ Suivant   : <action>
⏱️ Gagné     : ~<temps> de mise en forme
```
