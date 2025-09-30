# Changelog - Améliorations de recherche Spotify

## Version 2.0 - 2025-09-30

### 🎯 Objectif
Réduire drastiquement le nombre d'interventions manuelles lors du traitement de 500+ fichiers musicaux, notamment pour les titres anime avec des noms peu clairs.

### ✨ Nouvelles fonctionnalités

#### 1. Recherche multi-marchés automatique
- **Problème résolu** : Certains titres (surtout anime/J-pop) ne sont disponibles que sur certains marchés Spotify
- **Solution** : Recherche automatique sur FR → JP → US → Global
- **Impact** : Trouve maintenant "BLUE" par "Vivid" (Bleach OP14) avec score 0.71
- **Fichiers modifiés** : `src/matcher.py`

#### 2. Amélioration de l'API animethemes.moe
- **Problème résolu** : L'API ne trouvait pas les anime ou ne récupérait pas les artistes
- **Solutions** :
  - Utilisation de `filter[name]` pour recherche exacte
  - Fallback sur `filter[name]-like` pour recherche floue
  - Requête secondaire pour récupérer les artistes manquants
  - Détection améliorée des patterns : `OP14`, `OP 14`, `Opening14`, etc.
  - Nettoyage automatique de `NC`, `Raw`, `Creditless`, etc.
- **Impact** : "Bleach OP14 NC.mp3" → trouve "BLUE" par "ViViD"
- **Fichiers modifiés** : `src/advanced.py`

#### 3. Ordre d'exécution optimisé
- **Problème résolu** : La recherche anime était un fallback après échec
- **Solution** : Recherche anime effectuée EN PREMIER si `--advanced-search anime`
- **Impact** : Métadonnées améliorées avant la recherche Spotify
- **Fichiers modifiés** : `src/cli.py`

#### 4. Recherches manuelles améliorées
- **Option `[m]anual`** : Maintenant avec multi-marchés (FR, JP, US)
- **Option `[a]utre`** : Multi-marchés + stratégies de recherche multiples
- **Impact** : "BLUE" + "Vivid" trouve maintenant le bon titre
- **Fichiers modifiés** : `src/matcher.py`

#### 5. Logging amélioré
- Affiche quand des métadonnées anime sont trouvées
- Logs de debug pour diagnostiquer les problèmes
- **Fichiers modifiés** : `src/cli.py`

### 📊 Résultats

#### Avant
```
Fichier: Bleach OP14 NC.mp3
Recherche: "Bleach OP14 NC" (aucun artiste)
Meilleur résultat: "bleach" par Vandalism (score: 0.42)
Action: Intervention manuelle requise ❌
```

#### Après
```
Fichier: Bleach OP14 NC.mp3
Détection anime: "BLUE" par "ViViD" ✅
Recherche multi-marchés: FR, JP, US, Global
Meilleur résultat: "BLUE" par "Vivid" (score: 0.71)
Action: Auto-accepté ✅
```

### 🚀 Utilisation

```bash
# Mode normal avec recherche anime
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime

# Avec logs détaillés
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime --verbose

# Avec marché japonais par défaut (recommandé pour anime)
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime --market JP
```

### 📝 Notes de migration

#### Aucune action requise
Les améliorations sont rétrocompatibles. Aucun changement dans les arguments CLI.

#### Dépendances
- `requests` : Requis pour l'API animethemes.moe
- Installation : `pip install requests` (normalement déjà installé)

#### Performance
- **Recherche multi-marchés** : ~2-4x plus de requêtes API Spotify
- **Limite de rate** : Gérée automatiquement avec retry/backoff
- **Cache** : Évite les requêtes répétées pour les mêmes métadonnées

### 🐛 Corrections de bugs

1. **API animethemes** : Correction de l'extraction du nom d'anime depuis le nom de fichier
2. **Recherche manuelle** : Ajout du multi-marchés manquant
3. **LocalTrack** : Ajout du paramètre `path` manquant lors de la création

### 🔧 Améliorations techniques

#### Stratégies de recherche Spotify
1. Recherche simple combinée : `BLUE ViViD`
2. Recherche structurée avec guillemets : `track:"BLUE" artist:"ViViD"`
3. Recherche structurée sans guillemets : `track:BLUE artist:ViViD`
4. Versions nettoyées (sans feat., suffixes)

#### Marchés Spotify essayés
1. Marché principal (ex: FR)
2. Marché japonais (JP) - crucial pour anime
3. Marché US - large catalogue
4. Recherche globale (sans restriction)

### 📚 Documentation ajoutée

- `AMELIORATIONS.md` : Documentation détaillée des améliorations
- `TEST_QUICK.md` : Guide de test rapide
- `CHANGELOG.md` : Ce fichier

### 🎯 Prochaines étapes possibles

1. **AcoustID/MusicBrainz** : Recherche par empreinte acoustique pour les titres introuvables
2. **Cache persistant** : Sauvegarder les résultats de recherche entre sessions
3. **Recherche par similarité phonétique** : Pour gérer les variations de noms d'artistes
4. **Interface web** : Pour faciliter les interventions manuelles
5. **Statistiques** : Rapport de fin avec taux de réussite, temps économisé, etc.

### 👥 Contributeurs

- Amélioration de la recherche Spotify et de l'API anime
- Optimisation du workflow de traitement
- Documentation et tests
