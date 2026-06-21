# Troubleshooting

## Neo4j ingestion

### Cypher string escaping: `''` is invalid (use `\'`)

**Problème :** `load_model.py` échouait sur le vocabulaire `ObjectifAction` :
```
Invalid input ''organisation'': expected an expression, ',' or '}'
"  {nom:'voter_orga',  description:'Voter pour l''organisation'},"
```

**Cause :** `model/fsu_snuipp_ingestion.cypher` utilisait l'échappement SQL `''` pour
insérer une apostrophe dans une chaîne. Cypher ne reconnaît pas `''` : il ferme la chaîne
sur le premier quote, puis voit `organisation'` comme une expression invalide.

**Solution :** échapper avec un backslash — `'Voter pour l\'organisation'`. (Alternative :
utiliser des guillemets doubles `"Voter pour l'organisation"`.)

### Édition Neo4j et contraintes NODE KEY

`IS NODE KEY` est réservé à **Neo4j Enterprise / Aura**. En **Community**, utiliser
`IS UNIQUE`. `load_model.py` détecte l'édition (`CALL dbms.components()`) et convertit
automatiquement `NODE KEY -> UNIQUE` si nécessaire. L'instance locale du projet est en
édition **enterprise**, donc les `NODE KEY` du schéma canonique s'appliquent telles quelles.

### Rollups géographiques et arêtes non-hiérarchiques

Un rollup (somme montante des effectifs) suppose un **arbre** : chaque enfant a un seul
parent. Dans la donnée, l'académie *Guadeloupe* portait deux régions (*Guadeloupe* et
*TOM et Collectivités territoriales*) → double-comptage (+5 922). `build_geo_records()`
rend les liens inter-niveaux **fonctionnels** (une seule cible par source = la dominante,
plus gros effectif cumulé), ce qui restaure la conservation du total à tous les niveaux.
