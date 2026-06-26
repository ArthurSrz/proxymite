// =====================================================================
// Effectifs open data EN -> graphe FSU-SNUipp : nœuds Inconnu (potentiel théorique)
// Matérialise Etablissement.effectif en nœuds : 1 ETP enseignant = 1 Inconnu.
// Requêtes UNWIND paramétrées (param $records) — parité avec fsu_snuipp_ingestion.cypher.
// La construction des $records (répartition corps/genre/âge/ancienneté) est faite par
// load_neo4j.py ; ce fichier documente / permet un rejeu manuel via cypher-shell.
// =====================================================================

// ---------------------------------------------------------------------
// 1. CONTRAINTES
//    Canonique (Aura/Enterprise) : IS NODE KEY. Sur Neo4j Community (local) : IS UNIQUE.
// ---------------------------------------------------------------------
CREATE CONSTRAINT Etablissement_uai IF NOT EXISTS FOR (n:Etablissement) REQUIRE n.code_uai    IS UNIQUE;
CREATE CONSTRAINT Inconnu_id        IF NOT EXISTS FOR (n:Inconnu)       REQUIRE n.id_inconnu  IS UNIQUE;

// ---------------------------------------------------------------------
// 2. ÉTABLISSEMENTS (label :Ecole ajouté pour le 1er degré)
//    rec = {code_uai, nom, type_etablissement, secteur, commune, code_postal,
//           code_departement, libelle_departement, libelle_academie, libelle_region,
//           latitude, longitude, degre, nb_eleves, effectif, source, is_1d}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MERGE (e:Etablissement {code_uai: rec.code_uai})
SET e += {nom: rec.nom, type_etablissement: rec.type_etablissement, secteur: rec.secteur,
          commune: rec.commune, code_postal: rec.code_postal, code_departement: rec.code_departement,
          libelle_departement: rec.libelle_departement, libelle_academie: rec.libelle_academie,
          libelle_region: rec.libelle_region, latitude: rec.latitude, longitude: rec.longitude,
          degre: rec.degre, nb_eleves: rec.nb_eleves, effectif: rec.effectif, source: rec.source}
FOREACH (_ IN CASE WHEN rec.is_1d THEN [1] ELSE [] END | SET e:Ecole);

// ---------------------------------------------------------------------
// 3. INCONNUS (enseignants non identifiés par le syndicat — potentiel théorique)
//    rec = {id_inconnu, corps, genre, tranche_age, tranche_anciennete, type_affectation,
//           degre, source, annee_rentree}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MERGE (i:Inconnu {id_inconnu: rec.id_inconnu})
SET i += {corps: rec.corps, genre: rec.genre, tranche_age: rec.tranche_age,
          tranche_anciennete: rec.tranche_anciennete, type_affectation: rec.type_affectation,
          degre: rec.degre, source: rec.source, annee_rentree: rec.annee_rentree};

// ---------------------------------------------------------------------
// 4. RELATION  (:Inconnu)-[:TRAVAILLE_DANS {source, quotite, annee}]->(:Etablissement)
//    rec = {sourceId: Inconnu.id_inconnu, targetId: Etablissement.code_uai, source, quotite, annee}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MATCH (i:Inconnu {id_inconnu: rec.sourceId})
MATCH (e:Etablissement {code_uai: rec.targetId})
MERGE (i)-[r:TRAVAILLE_DANS]->(e)
SET r += {source: rec.source, quotite: rec.quotite, annee: rec.annee};

// ---------------------------------------------------------------------
// 5. MAILLE GÉOGRAPHIQUE  Etablissement -> Departement -> Academie -> Region
//    (pas de circonscription dans la source : lien direct étab -> département)
// ---------------------------------------------------------------------
CREATE CONSTRAINT Departement_code IF NOT EXISTS FOR (n:Departement) REQUIRE n.code_dept   IS UNIQUE;
CREATE CONSTRAINT Academie_nom     IF NOT EXISTS FOR (n:Academie)    REQUIRE n.nom         IS UNIQUE;
CREATE CONSTRAINT Region_code      IF NOT EXISTS FOR (n:Region)      REQUIRE n.code_region IS UNIQUE;

// Nœuds  (rec = {code_dept, nom, est_drom} | {nom, code_academie, region} | {code_region, nom})
UNWIND $records AS rec
MERGE (d:Departement {code_dept: rec.code_dept}) SET d += {nom: rec.nom, est_drom: rec.est_drom};

UNWIND $records AS rec
MERGE (a:Academie {nom: rec.nom}) SET a += {code_academie: rec.code_academie, region: rec.region};

UNWIND $records AS rec
MERGE (r:Region {code_region: rec.code_region}) SET r += {nom: rec.nom};

// Relations inter-niveaux  (rec = {sourceId, targetId, source})
UNWIND $records AS rec
MATCH (e:Etablissement {code_uai: rec.sourceId}) MATCH (d:Departement {code_dept: rec.targetId})
MERGE (e)-[r:DANS_DEPARTEMENT]->(d) SET r += {source: rec.source};

UNWIND $records AS rec
MATCH (d:Departement {code_dept: rec.sourceId}) MATCH (a:Academie {nom: rec.targetId})
MERGE (d)-[r:DEPARTEMENT_DANS_ACADEMIE]->(a) SET r += {source: rec.source};

UNWIND $records AS rec
MATCH (a:Academie {nom: rec.sourceId}) MATCH (r:Region {code_region: rec.targetId})
MERGE (a)-[rel:ACADEMIE_DANS_REGION]->(r) SET rel += {source: rec.source};

// Rollups effectif (agrégation montante)
MATCH (e:Etablissement)-[:DANS_DEPARTEMENT]->(d:Departement)
WITH d, sum(e.effectif) AS eff SET d.effectif = eff;
MATCH (d:Departement)-[:DEPARTEMENT_DANS_ACADEMIE]->(a:Academie)
WITH a, sum(d.effectif) AS eff SET a.effectif = eff;
MATCH (a:Academie)-[:ACADEMIE_DANS_REGION]->(r:Region)
WITH r, sum(a.effectif) AS eff SET r.effectif = eff;

// ---------------------------------------------------------------------
// 6. VÉRIFICATIONS
// ---------------------------------------------------------------------
// Invariant : effectif == Inconnus rattachés (avant réconciliation, doit renvoyer 0 ligne)
// MATCH (e:Etablissement)
// OPTIONAL MATCH (i:Inconnu)-[:TRAVAILLE_DANS]->(e)
// WITH e, count(i) AS n WHERE n <> e.effectif RETURN count(e);
//
// Répartition par genre (~62% F attendu) :
// MATCH (i:Inconnu) RETURN i.genre, count(*) ORDER BY count(*) DESC;
//
// Après réconciliation : effectif == Contact + Inconnu rattachés
// MATCH (e:Etablissement)
// OPTIONAL MATCH (x)-[:TRAVAILLE_DANS]->(e) WHERE x:Contact OR x:Inconnu
// WITH e, count(x) AS n WHERE n < e.effectif RETURN count(e);
