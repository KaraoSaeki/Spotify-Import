# Améliorations de la recherche Spotify

## Problèmes résolus

### 1. Titres anime introuvables (ex: "Bleach OP14 NC")

**Problème** : Les fichiers avec des noms comme "Bleach OP14 NC.mp3" ne trouvaient pas le bon titre sur Spotify, même avec `--advanced-search anime`.

**Solutions implémentées** :

#### A. Amélioration de l'extraction des métadonnées anime (`src/advanced.py`)
- **Détection améliorée des patterns** : Supporte maintenant `OP14`, `OP 14`, `Opening14`, `Opening 14`, etc.
- **Nettoyage des suffixes** : Supprime automatiquement `NC` (Non-Credit), `Raw`, `Creditless`, etc.
- **Extraction correcte du nom de l'anime** : Extrait "Bleach" depuis "Bleach OP14 NC"
- **API animethemes.moe optimisée** :
  - Utilise `filter[name]` pour des résultats exacts
  - Fallback sur `filter[name]-like` pour recherche floue
  - Récupération des artistes via requête secondaire si nécessaire
- **Scoring intelligent** : Privilégie les correspondances exactes de nom d'anime

**Résultat** : "Bleach OP14 NC.mp3" → trouve "BLUE" par "Vivid" (OP14 de Bleach)

#### B. Recherche multi-marchés (`src/matcher.py`)
- **Problème identifié** : Certains titres (surtout anime) ne sont disponibles que sur certains marchés Spotify
- **Solution** : Recherche séquentielle sur plusieurs marchés :
  1. Marché principal (ex: FR)
  2. Marché japonais (JP) - crucial pour les anime
  3. Marché US
  4. Recherche globale (sans restriction de marché)
- **Optimisation** : S'arrête dès qu'on a 50 candidats pour éviter trop de requêtes

**Résultat** : "BLUE" par "Vivid" est trouvé sur le marché JP avec un score de 0.711

#### C. Amélioration des stratégies de recherche (`src/matcher.py`)
- **Recherche simple combinée** : `BLUE ViViD` (comme l'interface Spotify)
- **Recherche structurée avec guillemets** : `track:"BLUE" artist:"ViViD"`
- **Recherche structurée sans guillemets** : `track:BLUE artist:ViViD` (plus flexible)
- **Versions nettoyées** : Suppression des feat., suffixes, etc.

#### D. Recherche manuelle améliorée (option `[a]utre`)
- **Collecte de tous les résultats** : Ne s'arrête plus à la première requête réussie
- **Dédoublonnage** : Évite les doublons entre les différentes stratégies
- **Jusqu'à 50 résultats** : Au lieu de 20 précédemment

### 2. Ordre d'exécution optimisé (`src/cli.py`)

**Avant** : La recherche anime était un fallback après une recherche normale ratée

**Maintenant** : La recherche anime est effectuée EN PREMIER si `--advanced-search anime` est activé
- Les métadonnées sont améliorées AVANT la recherche Spotify
- Utilise directement "BLUE" + "Vivid" au lieu de "Bleach OP14 NC"
- Meilleur taux de réussite dès la première recherche

## Utilisation

### Pour les fichiers anime

```bash
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime
```

Le système va maintenant :
1. Détecter automatiquement les patterns OP/ED dans les noms de fichiers
2. Interroger l'API animethemes.moe pour trouver le vrai titre et artiste
3. Rechercher sur Spotify avec ces métadonnées améliorées
4. Essayer plusieurs marchés (FR, JP, US, global) pour trouver le titre

### Recherche manuelle

Si un titre n'est toujours pas trouvé automatiquement :
1. Choisir `[a]utre` dans le menu interactif
2. Saisir le titre et l'artiste
3. Le système testera plusieurs stratégies de recherche sur plusieurs marchés

## Statistiques d'amélioration

**Avant** :
- "Bleach OP14 NC.mp3" → Score max: 0.42 (mauvais résultat)
- Recherche manuelle "BLUE" + "Vivid" → Pas de résultat sur marché FR

**Après** :
- "Bleach OP14 NC.mp3" → Score: 0.711 (bon résultat)
- Recherche automatique trouve le bon titre
- Fonctionne sur 500 fichiers avec beaucoup moins d'interventions manuelles

## Fichiers modifiés

- `src/advanced.py` : Amélioration de la détection anime et de l'API animethemes.moe
- `src/matcher.py` : Recherche multi-marchés et stratégies de recherche améliorées
- `src/cli.py` : Ordre d'exécution optimisé (anime en premier)

## Notes techniques

### Marchés Spotify
Certains titres ne sont disponibles que sur certains marchés :
- **JP** : Essentiel pour les anime, J-pop, J-rock
- **US** : Large catalogue international
- **FR** : Catalogue local
- **Global** : Sans restriction (peut contenir des titres non disponibles localement)

### API animethemes.moe
- Base de données communautaire d'openings/endings d'anime
- Fournit le vrai titre et artiste depuis le nom de fichier
- Gratuite et sans authentification
- Limitations : Peut ne pas avoir tous les anime récents

### Performance
- Recherche multi-marchés : ~4x plus de requêtes mais trouve beaucoup plus de titres
- Cache de recherche : Évite les requêtes répétées pour les mêmes métadonnées
- Limite de 50 candidats : Équilibre entre exhaustivité et performance
