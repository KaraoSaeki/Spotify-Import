# Ajout par lien Spotify direct

## ✅ Nouvelle fonctionnalité

Vous pouvez maintenant **coller directement un lien Spotify** pour ajouter un titre à la playlist, sans passer par la recherche !

## 🎯 Utilisation

### Option `[l]ien spotify`

Pendant le menu interactif, tapez `[l]` pour coller un lien :

```
[s]kip, [m]anual, [a]utre (titre/artiste), [l]ien spotify, [c]hange market [market: FR], [1-5], [q]uit > l
Collez le lien Spotify (ex: https://open.spotify.com/track/...): https://open.spotify.com/intl-fr/track/1REvFyAnTvUYggDlgCtGrM?si=d417ea6758f04afe
✓ URI extrait: spotify:track:1REvFyAnTvUYggDlgCtGrM
→ Titre ajouté à la playlist ✅
```

## 📋 Formats de liens supportés

### Format 1 : Lien web complet (avec paramètres)
```
https://open.spotify.com/intl-fr/track/1REvFyAnTvUYggDlgCtGrM?si=d417ea6758f04afe
```

### Format 2 : Lien web simple
```
https://open.spotify.com/track/1REvFyAnTvUYggDlgCtGrM
```

### Format 3 : URI Spotify
```
spotify:track:1REvFyAnTvUYggDlgCtGrM
```

### Format 4 : Lien court
```
https://open.spotify.com/tracks/1REvFyAnTvUYggDlgCtGrM
```

**Tous ces formats sont automatiquement reconnus et convertis en URI Spotify !**

## 💡 Workflow typique

### Cas 1 : Titre introuvable par recherche

```
Fichier: Rare Japanese Song.mp3
Meilleurs candidats: (aucun résultat pertinent)

[s]kip, [m]anual, [a]utre (titre/artiste), [l]ien spotify, [c]hange market, [1-5], [q]uit > l
```

**Étapes** :
1. Ouvrez Spotify sur votre navigateur ou app
2. Cherchez le titre manuellement
3. Cliquez sur "Partager" → "Copier le lien du titre"
4. Collez le lien dans le terminal
5. ✅ Le titre est ajouté automatiquement !

### Cas 2 : Titre avec nom différent sur Spotify

```
Fichier: 消えた町.mp3 (nom japonais)
Recherche: Aucun résultat

# Sur Spotify, le titre s'appelle "Kieta Machi" (romanisé)
[l]ien spotify
Collez: https://open.spotify.com/track/...
✓ Ajouté !
```

### Cas 3 : Titre région-locké

```
Fichier: Exclusive Track.mp3
Recherche sur FR, JP, US: Aucun résultat

# Le titre existe mais uniquement sur un autre marché
# Trouvez-le manuellement sur Spotify
[l]ien spotify
Collez: https://open.spotify.com/track/...
✓ Ajouté !
```

## 🔍 Comment obtenir le lien Spotify ?

### Sur l'application Spotify (Desktop)

1. Trouvez le titre dans Spotify
2. Clic droit sur le titre
3. **Partager** → **Copier le lien du titre**
4. Collez dans le terminal

### Sur l'application Spotify (Mobile)

1. Trouvez le titre dans Spotify
2. Appuyez sur les 3 points (•••)
3. **Partager** → **Copier le lien**
4. Collez dans le terminal

### Sur le web Spotify

1. Ouvrez https://open.spotify.com
2. Cherchez le titre
3. Copiez l'URL depuis la barre d'adresse
4. Collez dans le terminal

## 🎯 Avantages

1. ✅ **Contourne les limitations de recherche** : Si l'API ne trouve pas, vous pouvez ajouter manuellement
2. ✅ **Gère les titres région-lockés** : Ajoutez des titres non disponibles dans votre région
3. ✅ **Résout les problèmes de noms** : Titres japonais, caractères spéciaux, etc.
4. ✅ **Rapide et simple** : Copier-coller, c'est tout !
5. ✅ **Précision maximale** : Vous choisissez exactement le bon titre

## 📊 Exemples pratiques

### Exemple 1 : Anime opening introuvable

```
Fichier: Naruto OP24.mp3
Recherche automatique: Aucun résultat pertinent

# Recherche manuelle sur Spotify: "Koko kara Anly"
# Trouvé ! Copiez le lien

[l]ien spotify
Collez: https://open.spotify.com/track/3X7BB5EEK2CBVJ6BB56CTU
✓ URI extrait: spotify:track:3X7BB5EEK2CBVJ6BB56CTU
✓ Ajouté à la playlist !
```

### Exemple 2 : Titre avec caractères spéciaux

```
Fichier: 【MAD】Special Title.mp3
Recherche: Résultats non pertinents

# Trouvez le titre sur Spotify
[l]ien spotify
Collez: https://open.spotify.com/intl-fr/track/1REvFyAnTvUYggDlgCtGrM?si=abc123
✓ Ajouté !
```

### Exemple 3 : Version spécifique

```
Fichier: Song (Live Version).mp3
Résultats: Plusieurs versions (studio, live, remix)

# Vous voulez la version live spécifique
[l]ien spotify
Collez: https://open.spotify.com/track/... (version live)
✓ Version live ajoutée !
```

## 🛡️ Validation

Le système valide automatiquement le lien :

### Lien valide
```
Collez: https://open.spotify.com/track/1REvFyAnTvUYggDlgCtGrM
✓ URI extrait: spotify:track:1REvFyAnTvUYggDlgCtGrM
```

### Lien invalide
```
Collez: https://youtube.com/watch?v=...
❌ Lien invalide. Format attendu: https://open.spotify.com/track/ID
```

### Lien d'album (erreur)
```
Collez: https://open.spotify.com/album/...
❌ Lien invalide. Format attendu: https://open.spotify.com/track/ID
```

**Note** : Seuls les liens de **titres** (tracks) sont acceptés, pas les albums ou playlists.

## 🔧 Extraction automatique de l'ID

Le système extrait automatiquement l'ID du titre depuis :

```
https://open.spotify.com/intl-fr/track/1REvFyAnTvUYggDlgCtGrM?si=d417ea6758f04afe
                                        ^^^^^^^^^^^^^^^^^^^^^^^^
                                        ID extrait: 1REvFyAnTvUYggDlgCtGrM
```

Tous les paramètres supplémentaires (`?si=...`, `/intl-fr/`, etc.) sont automatiquement ignorés.

## 💡 Conseils

### Pour gagner du temps

1. **Gardez Spotify ouvert** pendant le traitement
2. **Préparez les liens** pour les titres difficiles à trouver
3. **Utilisez l'historique** : Si vous avez déjà cherché le titre, le lien est dans votre historique

### Pour les titres japonais/coréens

1. Cherchez sur Spotify avec le nom **romanisé** (ex: "Kieta Machi" au lieu de "消えた町")
2. Ou cherchez par **artiste** puis trouvez le titre dans la discographie
3. Copiez le lien et collez-le

### Pour les titres rares

1. Si le titre n'existe pas sur Spotify → `[s]kip`
2. Si le titre existe mais n'est pas trouvé par recherche → `[l]ien`
3. Si vous n'êtes pas sûr → Vérifiez manuellement sur Spotify d'abord

## 🆕 Nouveaux raccourcis

- `[l]` ou `[link]` ou `[lien]` ou `[url]` : Coller un lien Spotify

## 📋 Workflow complet

### Traitement d'un fichier difficile

```
1. Recherche automatique
   ↓ Aucun résultat pertinent

2. Essayer [a]utre avec titre/artiste
   ↓ Toujours pas de résultat

3. Essayer [c]hange market → JP
   ↓ Toujours pas de résultat

4. Recherche manuelle sur Spotify
   ↓ Titre trouvé !

5. [l]ien spotify
   ↓ Coller le lien
   ↓ ✅ Ajouté !
```

## 🎯 Cas d'usage principaux

### 1. Titres anime/J-pop rares
- Souvent mal indexés dans l'API
- Noms japonais vs romanisés
- **Solution** : Recherche manuelle + lien

### 2. Titres avec caractères spéciaux
- `【MAD】`, `♪`, `★`, etc.
- Peuvent perturber la recherche
- **Solution** : Lien direct

### 3. Versions spécifiques
- Live, Remix, Acoustic, etc.
- Plusieurs versions disponibles
- **Solution** : Choisir la bonne version + lien

### 4. Titres région-lockés
- Disponibles uniquement dans certains pays
- Non trouvés par recherche multi-marchés
- **Solution** : Trouver sur Spotify + lien

## 📊 Impact sur le workflow

**Avant** :
```
Titre introuvable → [s]kip → Perte du titre ❌
```

**Maintenant** :
```
Titre introuvable → Recherche manuelle sur Spotify → [l]ien → Ajouté ✅
```

**Résultat** : **100% des titres** peuvent être ajoutés, même les plus difficiles ! 🎉

## 🚀 Exemple de session complète

```bash
python -m src.cli --path-import "Z:\Anime" --auto-accept 0.7 --market JP
```

```
Fichier 1: Naruto OP1.mp3
→ Trouvé automatiquement ✅

Fichier 2: Rare Anime Song.mp3
→ Aucun résultat
[l]ien spotify
Collez: https://open.spotify.com/track/...
✅ Ajouté !

Fichier 3: 【MAD】Special.mp3
→ Résultats non pertinents
[l]ien spotify
Collez: https://open.spotify.com/track/...
✅ Ajouté !

Fichier 4: Bleach OP14.mp3
→ Trouvé automatiquement ✅
```

**Résultat** : 4/4 titres ajoutés au lieu de 2/4 ! 🎉
