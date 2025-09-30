# Nouvelles améliorations - 30/09/2025

## 🎯 Problèmes résolus

### 1. Nomenclature avec brackets japonais 【】

**Fichier problématique** : `【MAD】Naruto Shippuden 【New Opening 24】.mp3`

**Problèmes** :
- `【MAD】` (MAD = Music Anime Douga, vidéo fan-made) perturbait la recherche
- `【New Opening 24】` contenait l'info OP24 mais n'était pas détectée

**✅ Solution implémentée** :
- Détection de `Opening/OP` et `Ending/ED` **dans les brackets** avant de les supprimer
- Nettoyage automatique de `【MAD】`, `【AMV】`, etc.
- Extraction correcte : "Naruto Shippuden" + OP24

**Résultat** :
```
Avant : 【MAD】Naruto Shippuden 【New Opening 24】
Après : Base="Naruto Shippuden", Type=OP, Seq=24
API   : Trouve le bon titre et artiste via animethemes.moe
```

### 2. Numéros de piste au début du titre

**Fichier problématique** : `14. 消えた町.mp3`

**Problèmes** :
- Le "14." au début perturbait la recherche
- L'artiste "RADWIMPS" était dans les métadonnées Windows mais pas lu par le code

**✅ Solutions implémentées** :

#### A. Nettoyage du numéro de piste
- Suppression automatique de `^\d+\.\s*` (ex: "14. ", "01. ", etc.)
- Le titre devient juste "消えた町"

#### B. Lecture améliorée des métadonnées artiste
- Essai de **plusieurs formats de tags** : `artist`, `TPE1`, `©ART`, `ARTIST`
- Compatible avec MP3 (ID3), M4A, FLAC, etc.
- Lit maintenant "RADWIMPS" depuis les propriétés Windows

**Résultat** :
```
Avant : Titre="14. 消えた町", Artiste=""
Après : Titre="消えた町", Artiste="RADWIMPS"
```

### 3. Patterns additionnels nettoyés

**Ajouts** :
- `[AMV]`, `[MAD]`, `[MMV]`, `[PMV]` (vidéos fan-made)
- `[HD]`, `[HQ]`, `[1080p]`, `[720p]`, `[480p]` (qualité vidéo)
- Mots-clés : `MAD`, `AMV`, `MMV`, `PMV` dans le texte

## 📝 Fichiers modifiés

### 1. `src/metadata.py`
**Changement** : Lecture améliorée des tags artiste
```python
# Essaie plusieurs formats de tags
for key in ("artist", "TPE1", "©ART", "ARTIST"):
    if tags and tags.get(key):
        artist = ...
        break
```

### 2. `src/advanced.py`
**Changements** :
- Suppression des numéros de piste : `^\d+\.\s*`
- Détection OP/ED dans brackets japonais : `【New Opening 24】`
- Nettoyage des brackets : `【MAD】`, `【AMV】`
- Nettoyage des brackets carrés : `[HD]`, `[1080p]`
- Ajout de mots-clés à nettoyer : `MAD`, `AMV`, `MMV`, `PMV`

## 🧪 Tests

### Test 1 : Brackets japonais
```bash
Fichier : 【MAD】Naruto Shippuden 【New Opening 24】.mp3
✅ Détecte : Base="Naruto Shippuden", OP24
✅ API trouve le titre et artiste
```

### Test 2 : Numéro de piste
```bash
Fichier : 14. 消えた町.mp3
✅ Nettoie : "消えた町" (sans le "14.")
✅ Lit l'artiste : "RADWIMPS"
```

### Test 3 : Bleach (déjà fonctionnel)
```bash
Fichier : Bleach OP14 NC.mp3
✅ Détecte : Base="Bleach", OP14
✅ API trouve : "BLUE" par "ViViD"
```

### Test 4 : Bleach OP8
```bash
Fichier : Bleach OP8 v1 Raw.mp3
✅ Détecte : Base="Bleach", OP8
✅ API trouve le titre et artiste
```

## 🚀 Utilisation

Aucun changement dans la commande :
```bash
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime --market JP
```

Les améliorations sont **automatiques** et **rétrocompatibles**.

## 📊 Impact attendu

### Avant ces améliorations
- ❌ `【MAD】Naruto Shippuden 【New Opening 24】` → Pas de détection
- ❌ `14. 消えた町` → Artiste manquant, numéro perturbant
- ❌ Patterns MAD/AMV perturbaient la recherche

### Après ces améliorations
- ✅ Détection correcte des brackets japonais
- ✅ Extraction OP/ED depuis les brackets
- ✅ Lecture de l'artiste depuis les métadonnées Windows
- ✅ Nettoyage des numéros de piste
- ✅ Nettoyage des patterns vidéo (MAD, AMV, HD, etc.)

## 🎯 Cas d'usage typiques

### Fichiers avec nomenclature complexe
```
【MAD】Naruto Shippuden 【New Opening 24】.mp3
[AMV] One Piece Opening 1 [HD].mp3
14. Attack on Titan OP3 [1080p].mp3
```
→ Tous correctement nettoyés et détectés

### Fichiers avec métadonnées Windows
```
Fichier : 14. 消えた町.mp3
Propriétés Windows → Interprètes : RADWIMPS
```
→ Artiste correctement lu et utilisé pour la recherche

## 🔍 Titres japonais vs anglais sur Spotify

**Problème identifié** : Certains titres sont en japonais dans le fichier mais en anglais sur Spotify.

**Solution actuelle** : La recherche multi-marchés (FR, JP, US, global) aide à trouver les titres.

**Solution future possible** :
- Intégration de `pykakasi` ou `romkan` pour romanisation automatique
- Recherche avec les deux versions (japonais + romanisé)
- Exemple : "消えた町" → "Kieta Machi"

**Pour l'instant** : Utilisez la recherche manuelle `[a]utre` si le titre n'est pas trouvé automatiquement.

## 📚 Documentation mise à jour

- ✅ `NOUVELLES_AMELIORATIONS.md` (ce fichier)
- ✅ `AMELIORATIONS.md` (documentation principale)
- ✅ `CHANGELOG.md` (historique des changements)

## 🎉 Résumé

**3 nouveaux problèmes résolus** :
1. ✅ Brackets japonais 【】 avec détection OP/ED
2. ✅ Numéros de piste au début des titres
3. ✅ Lecture améliorée des métadonnées artiste

**Impact** : Encore moins d'interventions manuelles sur vos 500 fichiers ! 🚀
