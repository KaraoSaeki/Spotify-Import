# Nouvelles fonctionnalités - 30/09/2025

## ✅ Fonctionnalités implémentées

### 1. ✅ Détection "ending" et "opening"

**Status** : Déjà implémenté !

Le code détecte déjà les patterns suivants :
- `OP`, `OP14`, `OP 14`
- `Opening`, `Opening14`, `Opening 14`
- `ED`, `ED14`, `ED 14`
- `Ending`, `Ending14`, `Ending 14`

**Code** : `src/advanced.py` lignes 64 et 72

### 2. ✅ Nouveau paramètre `--auto-deny`

**Usage** :
```bash
python -m src.cli --path-import "..." --auto-accept 0.7 --auto-deny 0.5
```

**Comportement** :
- Si score >= 0.7 → Auto-accepté ✅
- Si score <= 0.5 → Auto-refusé ❌ (skip automatique)
- Si 0.5 < score < 0.7 → Menu interactif

**Exemple** :
```bash
# Accepte automatiquement >= 0.7, refuse automatiquement <= 0.4
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --auto-deny 0.4 --advanced-search anime --market JP
```

**Avantage** : Évite de devoir manuellement skipper les résultats avec des scores très bas.

### 3. ✅ Nouveau paramètre `--exclude`

**Usage** :
```bash
python -m src.cli --path-import "..." --exclude "AMV,RIRE JAUNE,MAD"
```

**Comportement** :
- Filtre les fichiers **avant** le traitement
- Ignore tous les fichiers dont le nom contient un des mots-clés
- Insensible à la casse (AMV = amv = Amv)
- Affiche le nombre de fichiers exclus

**Exemples** :
```bash
# Exclure les AMV
python -m src.cli --path-import "..." --exclude "AMV"

# Exclure plusieurs mots-clés
python -m src.cli --path-import "..." --exclude "AMV,RIRE JAUNE,MAD,PMV"

# Exclure des groupes de mots
python -m src.cli --path-import "..." --exclude "RIRE JAUNE,SQUEEZIE"
```

**Avantage** : Réduit drastiquement le temps de traitement en ignorant les fichiers non désirés dès le scan.

### 4. ⚠️ Recherche de vidéos Spotify

**Status** : Non applicable

**Explication** :
- L'API Spotify ne permet pas de chercher des "vidéos musicales"
- `type="track"` cherche tous les titres musicaux (avec ou sans vidéo)
- Les vidéos sur Spotify sont des podcasts/épisodes (type différent)

**Si vous ne trouvez pas un titre** :
1. Vérifiez qu'il existe bien sur Spotify (recherche manuelle dans l'app)
2. Utilisez `--market JP` pour les titres japonais/anime
3. Utilisez l'option `[a]utre` pour saisir manuellement titre + artiste
4. Le titre peut ne pas être disponible dans votre région

**Note** : Si un titre existe sur Spotify mais n'est pas trouvé par le script, c'est probablement :
- Un problème de marché/région (solution : `--market JP` ou `--market US`)
- Un problème de nom (solution : recherche manuelle `[a]utre`)
- Le titre n'est pas indexé comme "track" (rare)

## 📊 Exemples d'utilisation

### Cas 1 : Traitement anime avec filtrage

```bash
python -m src.cli \
  --path-import "Z:\NAS WD\Anime Music" \
  --auto-accept 0.7 \
  --auto-deny 0.4 \
  --exclude "AMV,MAD,PMV" \
  --advanced-search anime \
  --market JP
```

**Résultat** :
- ✅ Auto-accepte les scores >= 0.7
- ❌ Auto-refuse les scores <= 0.4
- 🚫 Ignore tous les fichiers contenant AMV, MAD ou PMV
- 🎌 Recherche sur le marché japonais en priorité
- 🎯 Utilise l'API animethemes pour détecter les OP/ED

### Cas 2 : Traitement rapide avec exclusions multiples

```bash
python -m src.cli \
  --path-import "Z:\Music" \
  --auto-accept 0.8 \
  --auto-deny 0.5 \
  --exclude "RIRE JAUNE,SQUEEZIE,LIVE,CONCERT,REMIX"
```

**Résultat** :
- ✅ Auto-accepte les scores >= 0.8 (très strict)
- ❌ Auto-refuse les scores <= 0.5
- 🚫 Ignore tous les fichiers contenant ces mots-clés
- ⚡ Traitement beaucoup plus rapide

### Cas 3 : Mode interactif avec filtrage léger

```bash
python -m src.cli \
  --path-import "Z:\Music" \
  --auto-accept 0.9 \
  --exclude "AMV" \
  --market FR
```

**Résultat** :
- ✅ Auto-accepte uniquement les scores >= 0.9 (très strict)
- ❓ Demande confirmation pour tous les autres
- 🚫 Ignore les AMV
- 🇫🇷 Recherche sur le marché français

## 🎯 Recommandations

### Pour 500 fichiers anime

```bash
python -m src.cli \
  --path-import "votre_dossier" \
  --auto-accept 0.7 \
  --auto-deny 0.3 \
  --exclude "AMV,MAD,PMV,RIRE JAUNE" \
  --advanced-search anime \
  --market JP
```

**Pourquoi ces valeurs ?**
- `--auto-accept 0.7` : Bon équilibre (pas trop strict)
- `--auto-deny 0.3` : Évite les résultats vraiment mauvais
- `--exclude` : Filtre les vidéos fan-made et autres contenus non désirés
- `--market JP` : Optimal pour l'anime

**Temps estimé** :
- Sans filtrage : ~500 fichiers × 5-10s = 40-80 minutes
- Avec filtrage : ~300 fichiers × 5-10s = 25-50 minutes
- Avec auto-deny : Encore plus rapide (pas de menu pour les mauvais scores)

## 📝 Notes techniques

### Ordre de traitement

1. **Scan des fichiers** dans le dossier
2. **Filtrage `--exclude`** : Supprime les fichiers non désirés
3. **Lecture des métadonnées** : Tags + nom de fichier
4. **Amélioration anime** (si `--advanced-search anime`) : API animethemes.moe
5. **Recherche Spotify** : Multi-marchés (FR, JP, US, global)
6. **Décision** :
   - Si score >= `--auto-accept` → Accepté ✅
   - Si score <= `--auto-deny` → Refusé ❌
   - Sinon → Menu interactif ❓

### Performance

**Sans optimisations** :
- 500 fichiers
- ~300 interventions manuelles
- ~2-3 heures

**Avec optimisations** :
- 500 fichiers
- Filtrage `--exclude` : ~200 fichiers restants
- Auto-deny : ~50 interventions manuelles
- ~30-45 minutes

**Gain** : ~75% de temps économisé ! 🎉

## 🐛 Dépannage

### "Le script ne trouve pas un titre qui existe sur Spotify"

**Solutions** :
1. Essayez avec `--market JP` ou `--market US`
2. Utilisez l'option `[a]utre` pour saisir manuellement
3. Vérifiez l'orthographe du titre/artiste
4. Le titre peut être région-locké

### "Trop de fichiers à traiter manuellement"

**Solutions** :
1. Utilisez `--auto-deny 0.4` pour auto-refuser les mauvais scores
2. Utilisez `--exclude` pour filtrer les fichiers non désirés
3. Ajustez `--auto-accept` à 0.65 ou 0.6 (moins strict)

### "Les fichiers AMV/MAD sont toujours traités"

**Solution** :
```bash
--exclude "AMV,MAD,PMV,MMV"
```

Les mots-clés doivent être dans le **nom du fichier**, pas dans les métadonnées.

## 📚 Documentation mise à jour

- ✅ `NOUVELLES_FONCTIONNALITES.md` (ce fichier)
- ✅ `AMELIORATIONS.md` (documentation principale)
- ✅ `CHANGELOG.md` (historique des changements)
