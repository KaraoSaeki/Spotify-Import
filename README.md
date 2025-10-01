# spotify-playlist-importer

Un importeur "fichiers audio locaux → playlist Spotify" qui scanne un dossier, fait du matching dans le catalogue Spotify, et ajoute les pistes trouvées dans une playlist (création ou mise à jour).

**Important** : Aucun upload de fichiers audio. Le script ne fait que rechercher des équivalents et les ajouter via l'API Spotify.

## Table des matières

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Nouvelles fonctionnalités](#-nouvelles-fonctionnalités)
- [Options CLI](#options-cli)
- [Heuristique de matching](#heuristique-de-matching)
- [Options interactives](#options-interactives)
- [Logs & Rapports](#logs--rapports)
- [Exemples pratiques](#exemples-pratiques)

## Prérequis

- Python 3.11+
- Compte Spotify
- Une application Spotify pour obtenir un Client ID
  - Configurer une Redirect URI (ex: `http://127.0.0.1:9090/callback`)

## Installation

```bash
python -m venv .venv
.venv/Scripts/activate  # Windows
pip install -r requirements.txt
```

## Configuration (.env)

1. Dupliquer `.env.example` en `.env`
2. Renseigner les variables:

```env
SPOTIFY_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
SPOTIFY_REDIRECT_URI=http://127.0.0.1:9090/callback
```

Auth PKCE sans client secret. Le jeton est mis en cache local `.cache/`.

## Authentification (PKCE)

Au premier lancement, le navigateur s'ouvre pour autoriser l'application.

Scopes demandés:
- `playlist-modify-public`
- `playlist-modify-private`
- `playlist-read-private`

Le refresh token est géré automatiquement par la librairie.

## Usage

### Commande minimale

```bash
python -m src.cli --path-import "D:/Musique/Imports"
```

### Flow console

```
Que souhaitez-vous faire ?
[1] Créer une nouvelle playlist
[2] Mettre à jour une playlist existante
[Q] Quitter
```

- **Création** → Saisie du nom (obligatoire), public/privé, collaborative, description
- **Mise à jour** → Liste paginée de vos playlists, filtre texte, sélection par index
- **Contrôle des droits** : Vous devez être propriétaire ou la playlist doit être collaborative

## 🆕 Nouvelles fonctionnalités

### 🎌 Recherche anime avancée (`--advanced-search anime`)

Détection automatique des openings/endings anime via l'API animethemes.moe :

**Fonctionnalités** :
- ✅ Détecte : `OP14`, `OP 14`, `Opening 14`, `Opening14`, `ED3`, `Ending 3`, etc.
- ✅ Nettoie : `NC`, `Raw`, `Creditless`, `【MAD】`, `【New Opening 24】`, `[AMV]`, etc.
- ✅ Supprime les numéros de piste : `14. Title` → `Title`
- ✅ Récupère le titre et l'artiste officiels depuis animethemes.moe
- ✅ Supporte les variantes : "Naruto Shippuden" → "Naruto: Shippuuden"

**Exemple** :
```bash
python -m src.cli --path-import "Z:\Anime" --advanced-search anime --market JP --auto-accept 0.7
```

**Résultat** :
- `Bleach OP14 NC.mp3` → Trouve "BLUE" par "ViViD" (score: 0.71) ✅
- `【MAD】Naruto Shippuden 【New Opening 24】.mp3` → Trouve "Koko kara" par "Anly" ✅
- `14. 消えた町.mp3` → Nettoie en "消えた町" + lit l'artiste "RADWIMPS" ✅

### 🌍 Recherche multi-marchés

Le système essaie automatiquement plusieurs marchés Spotify pour maximiser les chances de trouver le titre :

**Ordre de recherche** :
1. Marché spécifié (ex: FR)
2. Marché japonais (JP) - crucial pour l'anime/J-pop
3. Marché US - large catalogue
4. Recherche globale (sans restriction)

**Avantage** : Trouve les titres région-lockés qui ne sont disponibles que sur certains marchés.

### 🔄 Changement de marché dynamique (`[c]hange market`)

Changez le marché Spotify **pendant le traitement** sans relancer le script :

```
[s]kip, [m]anual, [a]utre, [l]ien, [c]hange market [market: FR], [1-5], [q]uit > c
Marché actuel: FR
Nouveau marché: JP
✓ Marché changé en: JP
```

**Cas d'usage** :
- Dossier mixte (français + anime) : Changez de FR à JP quand vous arrivez aux anime
- Test de différents marchés : Essayez JP, US, GB sans relancer

### 🚫 Filtrage avancé

#### Exclusion de fichiers (`--exclude`)

Ignore les fichiers dont le nom contient certains mots-clés :

```bash
--exclude "AMV,Nightcore,Remix,MAD,COVER,Epic,triste"
```

**Fonctionnement** :
- Insensible à la casse : `AMV` = `amv` = `Amv`
- Groupes de mots : `"Musique triste"` exclut les fichiers contenant "Musique triste"
- Autant de mots-clés que nécessaire

#### Exclusion de dossiers (`--exclude-dirs`)

Ignore des dossiers **entiers** lors du scan récursif :

```bash
--exclude-dirs "AMV,Covers,Live,Remixes,Nightcore,8D Audio"
```

**Fonctionnement** :
- Ignore le dossier et tous ses sous-dossiers
- Insensible à la casse
- Appliqué à tous les niveaux de l'arborescence
- **Gain de performance** : ~40% plus rapide (dossiers jamais scannés)

**Exemple** :
```
Z:\Music\
├── Anime/
│   ├── Naruto/OP1.mp3          ✓ Traité
│   └── AMV/Video.mp3            ✗ Dossier AMV exclu
└── Covers/Cover.mp3             ✗ Dossier Covers exclu
```

### ⚖️ Auto-deny (`--auto-deny`)

Refuse automatiquement les résultats avec un score trop bas :

```bash
--auto-accept 0.7 --auto-deny 0.3
```

**Comportement** :
- Score >= 0.7 → Auto-accepté ✅
- Score <= 0.3 → Auto-refusé ❌ (skip automatique)
- 0.3 < score < 0.7 → Menu interactif ❓

**Avantage** : Évite de devoir manuellement skipper les mauvais résultats.

### 🔗 Ajout par lien Spotify (`[l]ien`)

Collez directement un lien Spotify pour ajouter un titre :

```
[l]ien spotify
Collez: https://open.spotify.com/intl-fr/track/1REvFyAnTvUYggDlgCtGrM?si=d417ea6758f04afe
✓ URI extrait: spotify:track:1REvFyAnTvUYggDlgCtGrM
→ Titre ajouté ✅
```

**Formats supportés** :
- `https://open.spotify.com/track/ID`
- `https://open.spotify.com/intl-fr/track/ID?si=...`
- `spotify:track:ID`

**Cas d'usage** :
- Titres introuvables par recherche automatique
- Noms japonais/coréens avec romanisation différente
- Titres région-lockés
- Versions spécifiques (live, remix, etc.)

**Comment obtenir le lien** :
1. Trouvez le titre sur Spotify
2. Clic droit → Partager → Copier le lien du titre
3. Collez dans le terminal

### 🔄 Gestion des doublons

En mode **mise à jour de playlist**, détection automatique des doublons avec confirmation :

```
⚠️  DOUBLON DÉTECTÉ
   Titre: "BLUE" — Vivid
   URI: spotify:track:1REvFyAnTvUYggDlgCtGrM
   Ce titre est déjà présent dans la playlist.

Ajouter quand même ce doublon ? [y]es / [n]o (défaut=non) >
```

**Options** :
- `[n]o` (défaut) : Ignore le doublon, passe au suivant
- `[y]es` : Ajoute le doublon (titre apparaît 2 fois)

**Avantage** : Playlist propre sans répétitions involontaires.

## Options CLI

### Options de base
- `--path-import` (obligatoire) : Chemin du dossier à scanner
- `--market` (défaut: `FR`) : Marché Spotify (FR, JP, US, GB, DE, ES, IT, KR, etc.)
- `--public` / `--private` : Type de playlist à créer
- `--collab` : Playlist collaborative à la création

### Options de matching
- `--auto-accept` (float 0–1, défaut 0.92) : Score minimum pour auto-accepter
- `--auto-deny` (float 0–1, défaut: None) : Score maximum pour auto-refuser
- `--max-candidates` (int, 1–5, défaut 5) : Nombre de candidats affichés
- `--advanced-search anime` : Active la recherche anime via animethemes.moe

### Options de filtrage
- `--exclude` (CSV) : Mots-clés à exclure des fichiers
  - Exemple : `"AMV,Nightcore,Remix,MAD,COVER"`
- `--exclude-dirs` (CSV) : Dossiers à exclure du scan récursif
  - Exemple : `"AMV,Covers,Live,Remixes,Nightcore"`
- `--extensions` (CSV, défaut: `mp3,m4a,aac,flac,ogg,opus,wav,aiff,alac,wma,aif`)

### Options de scan
- `--no-recursive` : Ne pas descendre dans les sous-dossiers
- `--no-follow-symlinks` : Ne pas suivre les liens symboliques
- `--ignore-hidden` : Ignorer les fichiers/dossiers cachés

### Options de session
- `--dry-run` : Mode test (aucun ajout réel)
- `--resume` (chemin vers `state.json`) : Reprendre une session interrompue

## Heuristique de matching

### 1. Amélioration des métadonnées (si `--advanced-search anime`)
- Détection des patterns anime dans le nom de fichier
- Nettoyage automatique des patterns de bruit
- Requête API animethemes.moe pour métadonnées officielles
- Amélioration du titre et de l'artiste avant la recherche Spotify

### 2. Stratégies de recherche Spotify
Recherche multi-marchés avec plusieurs stratégies :
- `isrc:XXXX` si disponible
- Recherche simple combinée : `Title Artist`
- Recherche structurée : `track:"Title" artist:"Artist"`
- Variantes nettoyées : sans suffixes, sans `feat.`
- Collecte jusqu'à 50 résultats

### 3. Scoring local (0–1)
- **Titre** : 40% (fuzzy via `rapidfuzz`)
- **Artiste** : 40% (fuzzy via `rapidfuzz`)
- **Album** : 10%
- **Durée** : 10% (score plein si ±3s)
- **Bonus** : année ±1 (+0.02), tracknumber exact (+0.02)
- **Normalisation** : Poids redistribués si métadonnées manquantes

### 4. Décision
- Si `best_score >= --auto-accept` → Auto-accepté ✅
- Si `best_score <= --auto-deny` → Auto-refusé ❌
- Sinon → Menu interactif

## Options interactives

Pendant le traitement, vous avez accès à ces options :

### `[1-5]` : Sélectionner un candidat
Choisissez un des 5 meilleurs candidats affichés.

### `[s]kip` : Ignorer ce fichier
Passe au fichier suivant sans rien ajouter.

### `[m]anual` : Recherche manuelle
Saisissez une requête de recherche libre (comme dans Spotify).

### `[a]utre` : Recherche par titre/artiste
Saisissez le titre et l'artiste séparément, avec option de spécifier le marché :
```
Titre: BLUE
Artiste: Vivid
Marché (vide = FR, ex: JP, US, FR): JP
```

### `[l]ien` : Coller un lien Spotify
Collez directement un lien Spotify pour ajouter le titre :
```
Collez: https://open.spotify.com/track/1REvFyAnTvUYggDlgCtGrM
✓ URI extrait et ajouté
```

### `[c]hange market` : Changer le marché
Changez le marché de recherche pour tous les fichiers suivants :
```
Marché actuel: FR
Nouveau marché: JP
✓ Marché changé en: JP
```

### `[q]uit` : Quitter et sauvegarder
Sauvegarde la progression dans `state.json` pour reprendre plus tard.

## Lecture des métadonnées

### Lecture via mutagen
- `title`, `artist`, `album`, `tracknumber`, `date/year`, `duration_ms`, `isrc`
- Support multi-format : `artist`, `TPE1`, `©ART`, `ARTIST`

### Fallback sur le nom de fichier
- Motifs courants : `Artist - Title.ext`, `Artist_Title.ext`
- Nettoyage automatique : suffixes, `feat.`, numéros de piste

### Amélioration anime (si activée)
- Détection OP/ED dans le nom de fichier
- Requête API animethemes.moe
- Métadonnées officielles utilisées pour la recherche

## Logs & Rapports

### Logs
- `logs/spotify-import-YYYYmmdd_HHMMSS.log`

### Rapports
- `reports/summary-YYYYmmdd_HHMMSS.csv` (une ligne par fichier)
- `reports/summary-YYYYmmdd_HHMMSS.json` (NDJSON)

### Listes par statut
- `reports/ADDED-YYYYmmdd_HHMMSS.txt`
- `reports/SKIPPED-YYYYmmdd_HHMMSS.txt`
- `reports/NOT_FOUND-YYYYmmdd_HHMMSS.txt`
- `reports/AMBIGUOUS-YYYYmmdd_HHMMSS.txt`
- `reports/DUPLICATE-YYYYmmdd_HHMMSS.txt`
- `reports/PLANNED_ADD-YYYYmmdd_HHMMSS.txt` (mode dry-run)

### Statuts possibles
- `ADDED` : Titre ajouté avec succès
- `SKIPPED` : Fichier ignoré par l'utilisateur
- `NOT_FOUND` : Aucune correspondance trouvée
- `AMBIGUOUS` : Plusieurs candidats, aucun choix fait
- `DUPLICATE` : Titre déjà présent dans la playlist
- `PLANNED_ADD` : Ajout planifié (mode dry-run)

## Exemples pratiques

### Exemple 1 : Traitement anime optimisé

```bash
python -m src.cli \
  --path-import "Z:\Anime Music" \
  --auto-accept 0.7 \
  --auto-deny 0.3 \
  --exclude "AMV,MAD,PMV" \
  --exclude-dirs "AMV,Covers,Live" \
  --advanced-search anime \
  --market JP
```

**Résultat** :
- ✅ Détection automatique des anime OP/ED
- ✅ Recherche sur marchés JP, US, FR, global
- ✅ Auto-accepte les scores >= 0.7
- ✅ Auto-refuse les scores <= 0.3
- ✅ Ignore les fichiers/dossiers non désirés
- ⚡ Gain de temps : ~75%

### Exemple 2 : Traitement standard

```bash
python -m src.cli \
  --path-import "D:\Music\New Albums" \
  --auto-accept 0.8 \
  --market FR
```

**Résultat** :
- Recherche standard sur marché français
- Auto-accepte uniquement les scores >= 0.8 (strict)
- Menu interactif pour les autres

### Exemple 3 : Dry-run pour tester

```bash
python -m src.cli \
  --path-import "Z:\Music" \
  --auto-accept 0.7 \
  --dry-run
```

**Résultat** :
- Aucun ajout réel à la playlist
- Génère les rapports et statistiques
- Permet de voir ce qui serait ajouté

### Exemple 4 : Reprise après interruption

```bash
python -m src.cli \
  --path-import "Z:\Music" \
  --auto-accept 0.7 \
  --resume state.json
```

**Résultat** :
- Reprend là où vous vous étiez arrêté
- Ignore les fichiers déjà traités
- Conserve les correspondances validées

### Exemple 5 : Dossier mixte avec changement dynamique

```bash
python -m src.cli \
  --path-import "Z:\Music" \
  --auto-accept 0.7 \
  --market FR
```

**Pendant le traitement** :
1. Fichiers français → Traités avec marché FR
2. Fichier anime → `[c]` → `JP` → Tous les anime suivants utilisent JP
3. Retour à français → `[c]` → `FR`

## Robustesse & quota

- Backoff exponentiel + jitter (`tenacity`)
- Gestion `429` via `Retry-After`
- Ajout par lots de 100 URIs (limite API Spotify)
- Déduplication avant envoi

## Reprise (`--resume`)

- `state.json` conserve la position et les correspondances validées
- En cas d'arrêt (`[q]`), le script sauvegarde automatiquement
- Reprise avec `--resume state.json`

## Dépannage

### Titre introuvable
1. Essayez `--market JP` pour les titres japonais/anime
2. Utilisez `[a]utre` pour saisir manuellement titre + artiste
3. Utilisez `[c]hange market` pour tester différents marchés
4. Utilisez `[l]ien` pour coller un lien Spotify direct

### Rate-limit (429)
- Le script respecte automatiquement `Retry-After`
- Patientez, le script reprendra automatiquement

### Droits playlist
- Vous devez être propriétaire OU la playlist doit être collaborative
- Vérifiez les droits dans Spotify

### Tags manquants
- Le fallback par nom de fichier s'applique automatiquement
- Format recommandé : `Artist - Title.ext`

### Artiste non lu
- Vérifiez que le fichier a bien des métadonnées (clic droit → Propriétés → Détails)
- Le système essaie plusieurs formats de tags : `artist`, `TPE1`, `©ART`, `ARTIST`

## Sécurité

- Aucun secret commité
- PKCE sans client secret
- Cache token local (`.cache/`) ignoré par Git
- Ne jamais commiter `.env`, `state.json`

## Limites

- Disponibilité par pays (certains titres sont région-lockés)
- Versions live/remaster peuvent nuire au matching
- Faux positifs possibles si métadonnées incomplètes
- Aucun upload de vos fichiers audio vers Spotify

## Performance

### Sans optimisations
- 500 fichiers
- ~300 interventions manuelles
- ~2-3 heures

### Avec optimisations
- 500 fichiers
- Filtrage `--exclude-dirs` : ~200 fichiers restants
- Auto-deny : ~50 interventions manuelles
- **~30-45 minutes** (gain de 75%) 🚀

## Tests

```bash
pytest -q
```

## Documentation détaillée

- `AMELIORATIONS.md` : Documentation technique des améliorations
- `NOUVELLES_FONCTIONNALITES.md` : Guide des nouvelles fonctionnalités
- `CHANGEMENT_MARKET_DYNAMIQUE.md` : Guide du changement de marché
- `LIEN_SPOTIFY_DIRECT.md` : Guide de l'ajout par lien
- `EXCLUSION_DOSSIERS.md` : Guide de l'exclusion de dossiers
- `GESTION_DOUBLONS.md` : Guide de la gestion des doublons
- `CHANGELOG.md` : Historique des changements

## Licence

MIT
