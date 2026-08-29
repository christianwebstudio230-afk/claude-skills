# Bras droit AKOMA — le système

Un agent orchestrateur (ton COO) + un sous-agent spécialisé process, dans **Claude Code**,
sur ton abonnement Pro à 20 €/mois. Tu tapes une commande, tu obtiens un livrable Word et PDF
à l'identité AKOMA, prêt à relire.

Il fonctionne pour n'importe quel client : les sept niches AKOMA sont documentées, et une
grille générique permet d'attaquer tout autre secteur.

---

## Installation (20 minutes, une fois)

### Windows — dans PowerShell (pas CMD)

```powershell
irm https://claude.ai/install.ps1 | iex        # Claude Code (installeur officiel)
pip install python-docx openpyxl pandas pyyaml # moteur de documents
cd C:/Users/<toi>/Documents/akoma
claude                                          # puis se connecter au compte Pro
```

Prérequis : Python depuis python.org, avec la case **« Add python.exe to PATH »** cochée.
Git for Windows (git-scm.com) est optionnel mais recommandé — il donne à Claude Code un shell
plus complet. Si `python3` n'est pas reconnu, utilise `python`.

### macOS / Linux

```bash
curl -fsSL https://claude.ai/install.sh | bash
pip install python-docx openpyxl pandas pyyaml
cd akoma && claude
```

Connecteurs (optionnel — aucun livrable n'en dépend) :

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
claude mcp add --transport http gmail  https://gmailmcp.googleapis.com/mcp/v1
claude mcp add --transport http gdrive https://drivemcp.googleapis.com/mcp/v1
```

Puis `/mcp` pour autoriser chaque service.

---

## Les boutons

| Commande | Livrable produit |
|---|---|
| `/audit <client> [process]` | Diagnostic flash : irritants chiffrés, 3 quick wins, recommandation |
| `/sop <client> <process>` | SOP d'une page, tags 🟢🟡🔴, mode dégradé |
| `/cadrage <client> <projet>` | Note de cadrage : périmètre, livrables, rôles, jalons, risques |
| `/onboarding <client> <presta>` | Pack de démarrage 48 h + dossier client créé |
| `/reporting <client> <mois>` | Rapport d'avancement mensuel |
| `/cr <réunion>` | Compte rendu + tâches créées dans Notion/ClickUp |
| `/livrable <sujet ou .md>` | N'importe quel document, à l'identité AKOMA |
| `/brief` · `/bilan` · `/lead` | Priorités du jour · bilan hebdo + KPI · lead qualifié |
| `/module-metier <module> <client> <période>` | Les process chiffrés (ex. reporting conciergerie) |

Chaque commande finit par un Word + PDF dans `sorties/<client>/` et un compte rendu
`✅ Fait / ⚠️ À valider / ⏭️ Suivant / ⏱️ Gagné`.

---

## Carte du système

```
CLAUDE.md                      la constitution de l'orchestrateur
.claude/
  agents/architecte-process.md      le sous-agent spécialisé process
  agents/reporting-conciergerie.md  exemple de module métier chiffré
  commands/                         les boutons
  skills/personas-clients/          les enjeux business des 7 niches + grille générique
  skills/akoma-identite/            la charte des documents
  skills/livrables-obm/             les structures de livrables
modeles/                       6 trames markdown (sop, cadrage, CR, audit, reporting, onboarding)
scripts/livrable.py            LE moteur : markdown → Word/PDF à l'identité AKOMA
scripts/conciergerie_core.py   exemple de module chiffré (calculs déterministes)
clients/_TEMPLATE/             à dupliquer pour chaque client
sorties/<client>/              les livrables
journal/DECISIONS.md           la mémoire entre les sessions
docs/                          manager · offre commerciale · déploiement
```

## Le principe qui fait tenir l'ensemble

**Les règles dans le YAML, les calculs dans le Python, la mise en forme dans le moteur,
le jugement dans l'agent.** L'agent n'invente aucun chiffre et ne met en forme aucun document
à la main : il rédige, le moteur produit. C'est ce qui rend les livrables reproductibles —
donc facturables, donc déployables chez un client.

## Essai immédiat

```bash
python3 scripts/livrable.py modeles/audit-flash.md --sortie sorties/demo.docx --pdf
```

## Deux modules métier livrés

- **process** (générique) — le sous-agent `architecte-process`, utilisable pour tout client.
- **conciergerie** (exemple chiffré) — `/module-metier conciergerie <client> <mois> <taux>` :
  démontre comment un process chiffré propre à un secteur se branche sur le système.
  C'est le patron à copier pour industrialiser un autre calcul métier.
