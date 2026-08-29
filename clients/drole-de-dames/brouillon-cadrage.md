---
titre: "Note de Cadrage — Plateforme digitale d'accompagnement pédagogique"
client: "Drôle de Dames"
type: cadrage
date: "2026-08-29"
reference: "CADRAGE-2026-08-DROLE-DE-DAMES"
auteur: "AKOMA DIGITAL LTD"
---

# Note de Cadrage — Plateforme digitale d'accompagnement pédagogique

**Client :** Drôle de Dames (collectif en formation)
**Mission :** Cadrage du projet de création d'une plateforme digitale d'expertise pédagogique
**Date :** 29 août 2026
**Référence :** CADRAGE-2026-08-DROLE-DE-DAMES
**Rédigé par :** AKOMA DIGITAL LTD — Kathya Abiola

---

## Contexte

Drôle de Dames est un collectif de quatre expertes (Amandine Verstrepen, Kathya Abiola, Julie Chipot, Salomé Gautier) combinant des compétences en ingénierie pédagogique, gestion de projet, numérique, inclusion et accompagnement. Depuis le kick-off du 10 août 2026, le collectif a consolidé une vision commune : constituer une **cellule d'expertise et de support** pour aider les organismes et centres de formation à concevoir, structurer, digitaliser et faire évoluer des dispositifs pédagogiques durables et inclusifs.

Trois réunions de cadrage (10, 13 et 17 août 2026) ont permis de valider le positionnement, les quatre domaines de services et une architecture technique cible. La mission d'AKOMA est de structurer ce projet en une feuille de route opérationnelle, d'organiser la gouvernance et d'accompagner la livraison des premiers jalons.

---

## Périmètre

### Ce qui est inclus

- Formalisation de la vision, du positionnement et de la proposition de valeur
- Structuration des 4 domaines de services en livrables clients concrets
- Définition et documentation de l'architecture technique cible (Nextcloud / Moodle / Dolibarr / API)
- Cadrage RGPD et sécurité (grille de conformité)
- Organisation des groupes de travail et du rythme opérationnel
- Pilotage des jalons et compte rendu de chaque réunion (RIDA)
- Accompagnement à la définition du MVP (premier périmètre priorisé)

### Ce qui est explicitement exclu

- Développement technique des outils (Moodle, Dolibarr, API) — sous-traité à des partenaires
- Création de la structure juridique (décision reportée après validation de la proposition de valeur)
- Production de contenus pédagogiques (responsabilité des groupes de travail internes)
- Modules conciergerie et projets annexes (hors périmètre jusqu'à qualification)

---

## Domaines de services (4 features validées)

| # | Domaine | Description | Groupe responsable |
|---|---------|-------------|-------------------|
| 1 | Ingénierie pédagogique agile & gamification | Outiller la conception pédagogique, intégrer l'agilité et la gamification | Julie / Salomé |
| 2 | Digitalisation des contenus | Transformer les ressources existantes en contenus numériques accessibles | Kathya / Amandine |
| 3 | Accompagnement déploiement & amélioration | Processus et outils pour structurer et améliorer les services de formation | Amandine / Kathya |
| 4 | Audit pédagogique, organisationnel & conformité | Diagnostic des pratiques, conformité réglementaire, outils et data | À attribuer |

---

## Architecture technique cible

| Brique | Usage | Statut |
|--------|-------|--------|
| Nextcloud | Collaboration, stockage, chat, visio, Kanban | Retenu |
| Moodle | LMS — contenus, parcours, quiz, suivi apprenant | Retenu |
| Dolibarr | ERP — facturation, tiers, comptabilité | Retenu |
| API Moodle / Dolibarr | Automatisation des flux (inscriptions, factures, attestations) | À spécifier |
| Hébergement | Serveurs Debian/Linux européens | À qualifier (RGPD, HDS si besoin) |
| Vidéo IA | Production de contenus assistée | À tester (test prévu semaine du 17-23/08) |

---

## Livrables attendus

| Livrable | Format | Date cible | Responsable |
|----------|--------|-----------|-------------|
| Note de cadrage validée | Word + PDF | 05/09/2026 | AKOMA |
| Schéma architecture technique | Diagramme | 18/08/2026 | Amandine / Kathya |
| Grille RGPD et sécurité | Tableau | Avant mise en production | À attribuer |
| Liste flux API priorisés | Tableau | Prochaine réunion | Équipe technique |
| Fiche groupe 1 — Ingénierie pédagogique | Markdown | Prochaine consolidation | Julie / Salomé |
| Fiche groupe 2 — Digitalisation | Markdown | Prochaine consolidation | Kathya / Amandine |
| MVP défini et priorisé | Document | Fin septembre 2026 | Le groupe |
| Décision structure juridique | Note arbitrage | Après validation MVP | Le groupe |

---

## Rôles et responsabilités

| Rôle | Responsable | Périmètre |
|------|-------------|----------|
| Pilotage et coordination | Kathya Abiola (AKOMA) | Suivi jalons, RIDA, arbitrages, comptes rendus |
| Architecture technique | Amandine Verstrepen | Choix outils, partenaires, interopérabilité |
| Ingénierie pédagogique | Julie Chipot / Salomé Gautier | Feature 1, contenus, gamification |
| Digitalisation | Kathya / Amandine | Feature 2, besoins numériques |
| Partenaires techniques | À qualifier (Julien cité) | Développements Dolibarr, signature, URSSAF |
| Validation client | Le collectif (vote collectif) | Toute décision structurante |

---

## Jalons

| Date | Étape | Livrable associé |
|------|-------|------------------|
| 10/08/2026 | Kick-off — vision commune validée | RIDA 10/08 ✅ |
| 13/08/2026 | 4 features et cibles validées | RIDA 13/08 ✅ |
| 17/08/2026 | Architecture technique présentée | RIDA 17/08 ✅ |
| 24/08/2026 | Test vidéo IA | Résultats comparatifs |
| 05/09/2026 | Note de cadrage validée par le groupe | Ce document |
| Fin sept. 2026 | MVP défini et priorisé | Document de priorisation |
| À définir | Décision structure juridique | Note d'arbitrage |
| À définir | Lancement des développements techniques | Plan de projet technique |

---

## Risques

| # | Risque | Probabilité | Impact | Mitigation |
|---|--------|-------------|--------|------------|
| 1 | Éparpillement — nouvelles idées non rattachées au périmètre | Élevée | Élevé | Toute nouvelle idée passée en backlog qualifié avant arbitrage |
| 2 | Non-conformité RGPD / HDS avant mise en production | Moyenne | Élevé | Grille de conformité à produire avant tout développement |
| 3 | Propriété intellectuelle non formalisée entre membres | Élevée | Élevé | Accord de collaboration à formaliser avant toute exploitation commerciale |
| 4 | Disponibilités disparates — rythme de travail non tenu | Moyenne | Moyen | Rituels fixes (mardi 15h) + session mensuelle obligatoire |
| 5 | Dépendance à un seul partenaire technique | Faible | Moyen | Qualifier au moins deux partenaires Dolibarr |

---

## Organisation opérationnelle

- **Réunion hebdomadaire :** chaque mardi à 15 h (Teams / Nextcloud)
- **Session mensuelle obligatoire :** dernière semaine du mois
- **Outil de pilotage :** Trello (backlog Scrum) + RIDA à chaque réunion
- **Espace collaboratif :** Nextcloud (à mettre en place)
- **Partage des décisions :** journal `journal/DECISIONS.md` mis à jour après chaque réunion

---

## Validation

Cette note de cadrage doit être relue et validée par l'ensemble du collectif avant le **5 septembre 2026**.

Toute modification du périmètre après validation est soumise à vote collectif et donne lieu à une mise à jour numérotée de ce document.

> **🔴 Rappel :** tout document transmis à un tiers (partenaire, client, investisseur) requiert la validation explicite de Kathya Abiola avant envoi.

---

*AKOMA DIGITAL LTD · akoma.digital.ltd@gmail.com · Structurer. Transformer. Piloter l'impact.*
