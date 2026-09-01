# Commande /module-metier

Lance le sous-agent spécialisé correspondant au module métier demandé.

## Usage

```
/module-metier $ARGUMENTS
```

`$ARGUMENTS` doit contenir : le nom du module (ex: "conciergerie"), le client, et les paramètres spécifiques au module.

## Modules disponibles

| Module | Sous-agent | Paramètres requis |
|--------|-----------|-------------------|
| `conciergerie` | `reporting-conciergerie` | client, mois, taux_commission, fichier_donnees |
| `audit-process` | `architecte-process` | client, chemin_fichiers, periode |
| `montage-video` | `montage-video` | client, chemin_video, dossier_sortie, rendre (optionnel) |

## Étapes à exécuter

1. **Identifier le module** depuis les arguments. Si non précisé, lister les modules disponibles et demander.

2. **Collecter les paramètres** requis pour le module identifié. Lire `clients/[client]/config.yaml` pour pré-remplir taux_commission, devise, chemins.

3. **Lancer le sous-agent** correspondant avec les paramètres complets :

   Pour `conciergerie` :
   - Déléguer au sous-agent `reporting-conciergerie` avec :
     - client, mois, taux_commission, fichier_donnees

   Pour `audit-process` :
   - Déléguer au sous-agent `architecte-process` avec :
     - client, chemin_fichiers, periode, focus (optionnel)

   Pour `montage-video` :
   - Déléguer au sous-agent `montage-video` avec :
     - client, chemin_video, dossier_sortie, rendre (optionnel — false par défaut)

4. **Relayer le résultat** du sous-agent tel quel, en ajoutant uniquement le bloc de statut final si absent.

5. **Journaliser** :
   ```
   [DATE] · [CLIENT] · module [NOM_MODULE] · exécuté
   ```
   dans `journal/DECISIONS.md`.

## Ajout d'un nouveau module

Pour ajouter un module métier :
1. Créer `.claude/agents/[nom-module].md` avec les instructions du sous-agent
2. Ajouter une ligne dans le tableau "Modules disponibles" ci-dessus
3. Créer le script Python correspondant dans `scripts/` si calculs nécessaires

## Règles

- Toujours vérifier que les paramètres requis sont disponibles avant de lancer le sous-agent.
- Si un fichier de données est introuvable, signaler l'erreur clairement.
- Utiliser le français.
