# Test rapide des améliorations

## Test 1 : Vérifier que l'API anime fonctionne

```bash
python -c "from pathlib import Path; from src.advanced import enhance_from_filename_anime; result = enhance_from_filename_anime(Path('Bleach OP14 NC.mp3')); print(f'Titre: {result.get(\"title\")}'); print(f'Artiste: {result.get(\"artist\")}')"
```

**Résultat attendu** :
```
Titre: BLUE
Artiste: ViViD
```

## Test 2 : Vérifier la recherche multi-marchés

```bash
python -c "from src.auth import get_spotify_client; from src.matcher import search_candidates; from src.types import LocalTrack; from pathlib import Path; sp = get_spotify_client(['playlist-modify-public']); lt = LocalTrack(path=Path('test.mp3'), title='BLUE', artist='ViViD', album=None, duration_ms=92000, year=None, isrc=None, tracknumber=None); cands = search_candidates(sp, lt, 'FR', limit=5); print(f'Trouvé {len(cands)} candidats'); print(f'Premier: {cands[0].name} par {cands[0].artists[0]} (score: {cands[0].score:.2f})')"
```

**Résultat attendu** :
```
Trouvé 5 candidats
Premier: BLUE par Vivid (score: 0.71)
```

## Test 3 : Test complet avec le CLI

```bash
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime
```

**Pour "Bleach OP14 NC.mp3"** :
- ✅ Doit afficher dans les logs : "Anime metadata found: BLUE by ViViD"
- ✅ Doit trouver "BLUE — Vivid" avec score ~0.71
- ✅ Doit être auto-accepté (score >= 0.7)

**Pour la recherche manuelle** :
- Taper `[a]` puis "BLUE" + "Vivid"
- ✅ Doit trouver "BLUE — Vivid" dans les premiers résultats
- ✅ Doit chercher sur marchés FR, JP, US

**Pour la recherche manuelle libre** :
- Taper `[m]` puis "BLUE Vivid"
- ✅ Doit trouver "BLUE — Vivid" dans les premiers résultats

## Vérification des logs

Activer les logs détaillés :
```bash
python -m src.cli --path-import "Z:\NAS WD\Test spotify-import" --auto-accept 0.7 --advanced-search anime --verbose
```

Chercher dans les logs :
- `INFO | Anime metadata found: BLUE by ViViD` → ✅ L'API anime fonctionne
- Pas d'erreur `Anime search failed` → ✅ Pas de problème d'API

## Problèmes possibles

### Si l'API anime ne trouve rien
- Vérifier que `requests` est installé : `pip install requests`
- Vérifier la connexion internet
- Tester manuellement : https://api.animethemes.moe/anime?filter[name]=Bleach

### Si Spotify ne trouve pas le titre
- Vérifier que le multi-marchés fonctionne (logs)
- Le titre peut ne pas exister sur Spotify
- Essayer avec un autre marché principal : `--market JP`

### Si le score est trop bas
- Vérifier que les métadonnées sont correctes (titre, artiste, durée)
- Ajuster le seuil : `--auto-accept 0.6`
