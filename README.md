# Ms Publication — mise en place

Régie de publication automatique pour 1 à 3 chaînes YouTube et 1 à 3 comptes TikTok,
100% sur des briques gratuites. Lis d'abord la section **"Ce que tu dois savoir avant de lancer"**,
c'est important.

---

## Ce que tu dois savoir avant de lancer

1. **TikTok** : tant que ton app TikTok n'a pas passé l'audit officiel, toute vidéo postée par ce
   système sort **automatiquement en privé** (visible par toi seul). C'est TikTok qui impose ça à
   toutes les apps non auditées, pas une limite du code. Deux options :
   - Demander l'audit depuis le portail développeur TikTok une fois le projet fonctionnel (pas
     garanti, ça peut prendre du temps) ;
   - En attendant, ouvrir l'app TikTok chaque jour et rendre la vidéo publique en 2 taps depuis
     ton compte. Le dashboard te montrera clairement quelles vidéos sont en attente.
2. **YouTube** fonctionne en automatique complet dès la connexion, aucune limite de ce genre.
3. **Musique** : n'uploade que des morceaux dont tu as les droits (les tiens, ou une bibliothèque
   libre de droits). Comme il n'y a aucune vérification avant publication, un morceau protégé
   entraînera un signalement automatique — potentiellement sur toutes tes vidéos publiées avec.
4. **Revenus** : il n'existe pas d'API publique gratuite qui donne en temps réel l'argent gagné
   (ni côté YouTube sans démarche d'accès séparée, ni côté TikTok qui n'a aucune API de revenus).
   Le nombre d'abonnés se met à jour tout seul chaque semaine ; les revenus, tu les rentres à la
   main dans Supabase (2 clics, expliqué plus bas) si tu veux les voir dans le dashboard.

---

## Vue d'ensemble

```
Netlify (dashboard, gratuit)  ──lecture/écriture──▶  Supabase (base + fichiers, gratuit)
        │                                                      ▲
        │ déclenche à la demande                                │ lit/écrit
        ▼                                                      │
GitHub Actions (moteur d'automatisation, gratuit) ──────────────┘
        │
        ├─ Gemini API (script)       — gratuit
        ├─ edge-tts (voix off)       — gratuit
        ├─ Pixabay API (gameplay)    — gratuit
        ├─ ffmpeg (montage)          — gratuit, inclus dans le runner
        ├─ YouTube Data API v3       — gratuit, automatique
        └─ TikTok Content Posting API — gratuit, privé tant que non audité
```

---

## Étape 1 — Créer le dépôt GitHub

1. Crée un dépôt GitHub (public ou privé, peu importe).
2. Mets-y tous les fichiers de ce projet.
3. Garde son nom sous la forme `ton-compte/ms-publication` — tu en auras besoin plus bas.

## Étape 2 — Supabase (base de données + stockage)

1. Crée un compte sur supabase.com (gratuit), crée un nouveau projet.
2. Dans **SQL Editor**, colle le contenu de `supabase/schema.sql` et exécute-le.
3. Dans **Storage**, crée 3 buckets publics : `music`, `images`, `renders`.
4. Dans **Project Settings > API**, note :
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_ANON_KEY` (publique, pour le dashboard)
   - `service_role` key → `SUPABASE_SERVICE_ROLE_KEY` (secrète, jamais dans le navigateur)

## Étape 3 — Google Cloud (pour YouTube)

1. Va sur console.cloud.google.com, crée un projet.
2. Active **YouTube Data API v3** (bibliothèque d'API).
3. Configure l'écran de consentement OAuth (type "Externe", ajoute-toi comme testeur si l'app
   reste en mode test — suffisant pour 1 à 3 chaînes que tu gères toi-même).
4. Crée des identifiants **OAuth client ID**, type "Application Web".
5. Dans "URI de redirection autorisés", ajoute (tu remplaceras `TON-SITE` après le déploiement
   Netlify à l'étape 6) :
   `https://TON-SITE.netlify.app/.netlify/functions/youtube-oauth-callback`
6. Note `Client ID` et `Client Secret`.

## Étape 4 — TikTok for Developers

1. Va sur developers.tiktok.com, crée une app.
2. Ajoute le produit **Content Posting API** et **Login Kit**.
3. Renseigne l'URI de redirection :
   `https://TON-SITE.netlify.app/.netlify/functions/tiktok-oauth-callback`
4. Note `Client Key` et `Client Secret`.
5. Rappel : tant que l'app n'est pas auditée, les posts sortent en privé (voir plus haut).

## Étape 5 — Clés gratuites restantes

- **Gemini** : aistudio.google.com/apikey → crée une clé gratuite → `GEMINI_API_KEY`.
- **Pixabay** : pixabay.com/api/docs → crée un compte → `PIXABAY_API_KEY`.

## Étape 6 — Déployer le dashboard sur Netlify

1. Connecte ton dépôt GitHub à Netlify (New site from Git).
2. Netlify doit détecter `netlify.toml` automatiquement (base = `dashboard`).
3. Dans **Site configuration > Environment variables**, ajoute :
   - `DASHBOARD_PASSWORD` (le mot de passe que tu veux pour accéder au site)
   - `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`
   - `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`
   - `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`
   - `GITHUB_PAT` (un token GitHub avec la permission "Actions: read/write", généré dans
     GitHub > Settings > Developer settings > Fine-grained tokens)
   - `GITHUB_REPO` → `ton-compte/ms-publication`
4. Édite `dashboard/config.js` avec ton `SUPABASE_URL` et `SUPABASE_ANON_KEY` (ces deux-là
   peuvent être en clair dans le code, ce sont des clés publiques par design), commit, push.
5. Déploie. Note l'URL Netlify obtenue et reviens corriger les URI de redirection des
   étapes 3 et 4 avec cette URL définitive.

## Étape 7 — Secrets GitHub Actions (le moteur d'automatisation)

Dans le dépôt GitHub > **Settings > Secrets and variables > Actions**, ajoute les mêmes
secrets qu'à l'étape 6 (sauf `DASHBOARD_PASSWORD` et `GITHUB_PAT`/`GITHUB_REPO`, inutiles ici) :
`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, `PIXABAY_API_KEY`,
`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`.

## Étape 8 — Utilisation

1. Ouvre ton site Netlify, entre le mot de passe.
2. "+ Nouvelle chaîne" → choisis YouTube ou TikTok, donne-lui un nom, une niche
   (ex: *"faits divers insolites"*) et un mot-clé gameplay (ex: *"minecraft parkour"*).
3. Sur la fiche créée, clique "Connecter à YouTube/TikTok" et autorise l'accès.
4. Optionnel : ajoute une musique et des images depuis la fiche.
5. Le workflow `daily-publish.yml` tourne automatiquement chaque jour à 08:00 UTC pour
   toutes les chaînes actives. Le bouton "Publier maintenant" du dashboard permet de forcer
   une publication immédiate pour une seule chaîne (utile pour tester).
6. Le workflow `weekly-stats.yml` met à jour les abonnés chaque lundi.

## Limites connues à garder en tête

- **Coquilles gratuites = quotas** : GitHub Actions gratuit donne 2000 minutes/mois sur dépôt
  privé (illimité sur dépôt public). Un montage + upload prend quelques minutes ; largement
  suffisant pour 1 à 6 vidéos/jour.
- **edge-tts** est une librairie non officielle qui s'appuie sur le service de lecture à voix
  haute de Microsoft Edge. Elle est gratuite et largement utilisée, mais pas garantie à 100%
  dans le temps — si elle cesse de fonctionner un jour, Piper TTS (open source, auto-hébergé)
  est le repli gratuit le plus solide.
- **Pixabay** a un contenu gameplay generic (parkour, courses, etc.), pas des extraits de jeux
  AAA récents précis — ce qui est justement ce qui te protège du droit d'auteur.
