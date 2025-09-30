# Changement de marché dynamique

## ✅ Nouvelle fonctionnalité

Vous pouvez maintenant **changer le marché Spotify dynamiquement** pendant le traitement des fichiers, sans avoir à relancer le script !

## 🎯 Utilisation

### Option 1 : Changer le marché global

Pendant le menu interactif, tapez `[c]` pour changer le marché :

```
[s]kip, [m]anual, [a]utre (titre/artiste), [c]hange market [market: FR], [1-5], [q]uit > c
Marché actuel: FR
Marchés disponibles: FR, JP, US, GB, DE, ES, IT, etc.
Nouveau marché (ou vide pour annuler): JP
✓ Marché changé en: JP
```

Le nouveau marché sera utilisé pour **toutes les recherches suivantes** jusqu'au prochain changement.

### Option 2 : Spécifier le marché pour une recherche

Avec l'option `[a]utre`, vous pouvez maintenant spécifier le marché :

```
[s]kip, [m]anual, [a]utre (titre/artiste), [c]hange market [market: FR], [1-5], [q]uit > a
Titre (laisser vide si inconnu): BLUE
Artiste (laisser vide si inconnu): Vivid
Marché (vide = FR, ex: JP, US, FR): JP
```

Ce marché sera utilisé **uniquement pour cette recherche**.

## 📋 Workflow typique

### Cas 1 : Fichier anime introuvable

```
Fichier: Naruto OP24.mp3
Meilleurs candidats: (aucun résultat pertinent)

[s]kip, [m]anual, [a]utre (titre/artiste), [c]hange market [market: FR], [1-5], [q]uit > c
Nouveau marché: JP
✓ Marché changé en: JP

[s]kip, [m]anual, [a]utre (titre/artiste), [c]hange market [market: JP], [1-5], [q]uit > a
Titre: Koko kara
Artiste: Anly
Marché (vide = JP, ex: JP, US, FR): 
→ Recherche sur JP, trouve le titre ✅
```

### Cas 2 : Recherche ponctuelle sur un autre marché

```
Fichier: Some English Song.mp3
[market: FR]

[s]kip, [m]anual, [a]utre (titre/artiste), [c]hange market [market: FR], [1-5], [q]uit > a
Titre: Some English Song
Artiste: Artist Name
Marché (vide = FR, ex: JP, US, FR): US
→ Recherche sur US uniquement pour ce titre
```

### Cas 3 : Traitement de plusieurs fichiers anime

```
# Changez le marché en JP au début
[c] → JP

# Tous les fichiers suivants utiliseront JP
Fichier 1: Naruto OP24.mp3 → Recherche sur JP ✅
Fichier 2: Bleach OP14.mp3 → Recherche sur JP ✅
Fichier 3: One Piece OP1.mp3 → Recherche sur JP ✅
```

## 🌍 Marchés Spotify disponibles

### Principaux marchés

- **FR** : France (défaut)
- **JP** : Japon (recommandé pour anime/J-pop)
- **US** : États-Unis (large catalogue)
- **GB** : Royaume-Uni
- **DE** : Allemagne
- **ES** : Espagne
- **IT** : Italie
- **KR** : Corée du Sud (K-pop)
- **BR** : Brésil

### Liste complète

Tous les codes ISO 3166-1 alpha-2 sont supportés : AT, AU, BE, CA, CH, CL, CO, CZ, DK, FI, HK, IE, IN, MX, NL, NO, NZ, PL, PT, RU, SE, SG, TH, TR, TW, ZA, etc.

## 💡 Conseils

### Quand changer de marché ?

1. **Anime/J-pop** : Utilisez `JP`
2. **K-pop** : Utilisez `KR` ou `JP`
3. **Musique anglophone** : Utilisez `US` ou `GB`
4. **Musique latine** : Utilisez `ES`, `MX`, ou `BR`
5. **Musique européenne** : Utilisez le marché du pays d'origine

### Stratégie optimale

#### Pour un dossier mixte

1. Lancez avec `--market FR` (ou votre marché local)
2. Quand vous rencontrez un fichier anime → `[c]` → `JP`
3. Continuez avec JP pour les autres anime
4. Si vous revenez à de la musique française → `[c]` → `FR`

#### Pour un dossier anime

1. Lancez directement avec `--market JP`
2. Pas besoin de changer pendant le traitement
3. Si un titre n'est pas trouvé → `[a]utre` → spécifiez `US` ou `FR` ponctuellement

## 🔧 Fonctionnement technique

### Multi-marchés automatique

Même si vous spécifiez un marché, le système essaie automatiquement plusieurs marchés :

```
Marché spécifié: FR
Marchés essayés: FR → JP → US → Global
```

Cela maximise les chances de trouver le titre.

### Priorité des marchés

1. **Marché spécifié** (ex: FR)
2. **JP** (si pas déjà essayé)
3. **US** (si pas déjà essayé)
4. **Global** (sans restriction)

### Changement dynamique

Le changement de marché avec `[c]` modifie le **marché prioritaire** pour toutes les recherches suivantes.

## 📊 Exemples pratiques

### Exemple 1 : Dossier anime

```bash
python -m src.cli --path-import "Z:\Anime" --auto-accept 0.7 --market JP
```

Pendant le traitement :
- Tous les fichiers sont recherchés sur JP en priorité
- Si un titre n'est pas trouvé → `[a]utre` → testez avec `US` ou `FR`

### Exemple 2 : Dossier mixte

```bash
python -m src.cli --path-import "Z:\Music" --auto-accept 0.7 --market FR
```

Pendant le traitement :
- Fichiers français → OK avec FR
- Fichier anime → `[c]` → `JP` → continuez
- Retour à français → `[c]` → `FR`

### Exemple 3 : Recherche ciblée

```
Fichier: Unknown Japanese Song.mp3

[a]utre
Titre: 消えた町
Artiste: RADWIMPS
Marché: JP
→ Trouve le titre sur le marché japonais ✅
```

## 🎯 Avantages

1. **Flexibilité** : Changez de marché sans relancer le script
2. **Rapidité** : Testez différents marchés en quelques secondes
3. **Précision** : Spécifiez le marché optimal pour chaque titre
4. **Efficacité** : Évitez les recherches infructueuses

## 📝 Notes

- Le changement de marché est **temporaire** (pour la session en cours)
- Le marché par défaut est celui spécifié avec `--market` (ou FR)
- Vous pouvez changer de marché autant de fois que nécessaire
- Le marché actuel est affiché dans le prompt : `[market: JP]`

## 🆕 Nouveaux raccourcis

- `[c]` ou `[change]` ou `[market]` : Changer le marché global
- Dans `[a]utre` : Prompt "Marché" pour spécifier le marché de cette recherche

## 🚀 Workflow recommandé

Pour traiter 500 fichiers mixtes (français + anime) :

```bash
python -m src.cli --path-import "Z:\Music" --auto-accept 0.7 --auto-deny 0.3 --market FR
```

1. Traitez les fichiers français normalement
2. Quand vous arrivez aux anime → `[c]` → `JP`
3. Traitez tous les anime avec JP
4. Si retour à français → `[c]` → `FR`

**Gain de temps** : Pas besoin de relancer le script avec différents marchés ! 🎉
