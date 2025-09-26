# spotify-playlist-importer

Un importeur "fichiers audio locaux → playlist Spotify" qui scanne un dossier, fait du matching dans le catalogue Spotify, et ajoute les pistes trouvées dans une playlist (création ou mise à jour).

Important: aucun upload de fichiers audio. Le script ne fait que rechercher des équivalents et les ajouter via l'API Spotify.

## What / Why
- Outil d’import « local → playlist Spotify » par matching du catalogue.
- Ne transfère aucun fichier audio vers Spotify. Il se contente de rechercher des équivalents et de les ajouter via l’API.

## Prérequis
- Python 3.11+
- Compte Spotify
- Une application Spotify pour obtenir un Client ID
  - Configurer une Redirect URI (ex: `http://127.0.0.1:9090/callback`)

## Installation
```
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

## Configuration (.env)
1) Dupliquer `.env.example` en `.env`
2) Renseigner les variables:
```
SPOTIFY_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
SPOTIFY_REDIRECT_URI=http://127.0.0.1:9090/callback
```
- Auth PKCE sans client secret. Le jeton est mis en cache local `.cache/`.

## Authentification (PKCE)
Au premier lancement, le navigateur s’ouvre pour autoriser l’application.
Scopes demandés:
- `playlist-modify-public`
- `playlist-modify-private`
- `playlist-read-private`

Le refresh token est géré automatiquement par la librairie.

## Usage
Commande minimale:
```
python -m src.cli --path-import "D:/Musique/Imports"
```

Flow console après connexion:
```
Que souhaitez-vous faire ?
[1] Créer une nouvelle playlist
[2] Mettre à jour une playlist existante
[Q] Quitter
```

- Création → saisie du nom (obligatoire), public/privé, collaborative, description.
- Mise à jour → liste paginée de vos playlists, filtre texte, sélection par index, fiche récap et double confirmation.
- Contrôle des droits: si vous n’êtes pas propriétaire et la playlist n’est pas collaborative → refus.

### Options CLI
- `--market` (défaut: `FR`)
- `--public` / `--private` (impactent la création)
- `--collab` (playlist collaborative à la création)
- `--auto-accept` (float 0–1, défaut 0.92)
- `--max-candidates` (int, 1–5, défaut 5) → nombre de candidats affichés en mode interactif
- `--dry-run` (aucun ajout, mais matching et résumés générés)
- `--resume` (chemin vers `state.json` pour reprendre un run)
- `--extensions` (CSV, défaut: `mp3,m4a,aac,flac,ogg,opus,wav,aiff,alac,wma,aif`)
- `--no-follow-symlinks`, `--ignore-hidden`

## Heuristique de matching
1) Stratégie de requêtes successives:
   - `isrc:XXXX` si disponible
   - `track:"Title" artist:"Artist"`
   - variantes sans guillemets, sans suffixes `(Live)`, `(Remastered)`, sans `feat.`
   - collecte jusqu’à 20 résultats bruts
2) Scoring local (0–1):
   - Titre 40% + Artiste 40% (fuzzy via `rapidfuzz`)
   - Album 10%
   - Durée 10% (score plein si ±3s)
   - Bonus: année ±1 (+0.02), tracknumber exact (+0.02) / ±1 (+0.01)
   - Normalisation: si album/durée manquants, les poids restants sont renormalisés
3) Décision:
   - Si `best_score >= --auto-accept` → auto-accept (sauf `--dry-run`)
   - Sinon menu interactif (jusqu’à 5 candidats)
   - Choix: `[1–5]` valider, `[s]kip`, `[m]anual` (requête libre), `[q]` quitter & reprendre

## Lecture des métadonnées
- Lecture via `mutagen`: `title`, `artist`, `album`, `tracknumber`, `date/year`, `duration_ms`, `isrc`
- Fallback sur le nom de fichier: motifs courants `Artist - Title.ext`, `Artist_Title.ext` avec nettoyage de suffixes et `feat.`

## Logs & Rapports
- Log par run: `logs/spotify-import-YYYYmmdd_HHMMSS.log`
- Rapports:
  - `reports/summary-YYYYmmdd_HHMMSS.csv` (une ligne par fichier)
  - `reports/summary-YYYYmmdd_HHMMSS.json` (NDJSON)
- Statuts possibles: `ADDED`, `SKIPPED`, `NOT_FOUND`, `AMBIGUOUS`, `DUPLICATE`, `PLANNED_ADD` (dry-run)

## Reprise (`--resume`)
- `state.json` conserve la position et les correspondances validées.
- En cas d’arrêt (`[q]`), le script sauvegarde et peut reprendre plus tard.

## Robustesse & quota
- Backoff exponentiel + jitter (`tenacity`), gestion `429` via `Retry-After`.
- Ajout par lots de 100 URIs (limite API Spotify).
- Déduplication avant envoi.

## Dépannage
- 429 / rate-limit → attendre; le script respecte `Retry-After`.
- Titres non jouables ou indisponibles sur votre marché (`--market`).
- Droits playlist: vous devez être propriétaire ou la playlist doit être collaborative.
- Problèmes d’auth: vérifier `SPOTIFY_REDIRECT_URI` et les scopes.
- Tags manquants: le fallback par nom de fichier s’applique.

## Sécurité
- Aucun secret commité. PKCE sans client secret.
- Cache token local (`.cache/`) ignoré par Git.
- Ne jamais commiter `.env`, `state.json`.

## Limites
- Disponibilité par pays, versions live/remaster peuvent nuire au matching.
- Faux positifs possibles lorsque métadonnées incomplètes.
- Aucun upload de vos fichiers audio vers Spotify.

## Exemple d’interaction
```
$ python -m src.cli --path-import "/media/music/new"
Connexion à Spotify → navigateur ouvert...
✔ Connecté en tant que liam

Que souhaitez-vous faire ?
[1] Créer une nouvelle playlist
[2] Mettre à jour une playlist existante
[Q] Quitter
> 2

Filtre (laisser vide pour tout) : chill
Page 1/3
  1 | Chill & Focus             | moi        | 124 | Privé  | Non  | 37f...a9
  2 | Chilltrain                | moi        |  89 | Public | Non  | 5ab...d1
  3 | Chillhop Essentials 2020  | autre_user |  56 | Public | Non  | 91c...20
[n] suivante, [p] précédente, [#] sélectionner, [q] quitter
> 1

Vous avez choisi: "Chill & Focus" (124 titres) — propriétaire: moi
Confirmez en retapant l'index (1) puis Y/N :
> 1
> Y

Scan des fichiers…  73 trouvés
Analyser: "Artist - Title.flac" …
Meilleurs candidats:
  1) "Title" — Artist • Album • 03:42 • score=0.96 • uri=spotify:track:...
  2) "Title (Remastered)" — Artist • ... • 03:41 • score=0.92 • uri=...
[s]kip, [m]anual, [1-2], [q]uit
> 1
→ Ajout planifié (batch)

…
Ajout des 100 premiers titres…
OK

Résumé:
 ADDED=68  SKIPPED=3  NOT_FOUND=2  AMBIGUOUS=0  DUPLICATE=0
Log: logs/spotify-import-20250103_231402.log
CSV: reports/summary-20250103_231402.csv
JSON: reports/summary-20250103_231402.json
```

## Tests
```
pytest -q
```

## Licence
MIT
