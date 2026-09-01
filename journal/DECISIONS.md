# Journal des Décisions — AKOMA DIGITAL LTD

Format : `YYYY-MM-DD · CLIENT · SUJET · DÉCISION OU ACTION`

---

2026-08-29 · AKOMA · initialisation du système · premier déploiement du système bras-droit AKOMA dans claude-skills
2026-08-29 · Drôle de Dames · cadrage · Note de cadrage plateforme digitale générée — CADRAGE-2026-08-DROLE-DE-DAMES
2026-09-01 · AKOMA · nouveau module montage-video · pipeline Gemini (transcription + détection bafouillages) → ffmpeg (coupe) → HyperFrames (habillage sous-titres/b-roll) livré dans scripts/montage_video_core.py + sous-agent .claude/agents/montage-video.md. À CONFIRMER : nom du client destinataire, vidéo source, clé GEMINI_API_KEY, et le contrat HTML exact de HyperFrames (skill non installable dans cet environnement — à valider avec `npx hyperframes preview` avant tout rendu réel)
2026-09-01 · AKOMA · montage-video : secours gratuit sans abonnement · ajout d'une bascule automatique sur faster-whisper (local, sans clé API) si Gemini échoue — détection des bafouillages par heuristique, moins fine, toujours signalée (champ "moteur" dans transcript.json + alerte de relecture humaine)
2026-09-01 · PeshNeuroeveil · montage-video : client créé + skills HyperFrames officielles installées · dossier clients/PeshNeuroeveil/ créé (brief et secteur À CONFIRMER). `npx skills add heygen-com/hyperframes --full-depth` exécuté avec succès (bloqué la veille par le classificateur de permissions) : le vrai contrat de composition diffère du HTML deviné précédemment (timeline GSAP obligatoire, data-duration racine). L'étape "habiller" de scripts/montage_video_core.py ne génère plus de HTML à l'aveugle — elle exporte sous_titres.json (sous-titres + points b-roll suggérés), et l'agent .claude/agents/montage-video.md authore la composition avec les vraies skills (/hyperframes, /hyperframes-core, /embedded-captions, /media-use, /hyperframes-keyframes), validée par `npx hyperframes check` avant tout rendu. À CONFIRMER : vidéo source du client, clé GEMINI_API_KEY
