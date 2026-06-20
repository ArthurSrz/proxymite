// =====================================================================
// Effectifs open data EN -> graphe FSU-SNUipp : Contacts DÉRIVÉS (potentiel théorique)
// Matérialise Etablissement.effectif en nœuds : 1 ETP enseignant = 1 Contact dérivé.
// Requêtes UNWIND paramétrées (param $records) — parité avec fsu_snuipp_ingestion.cypher.
// La construction des $records (répartition corps/genre/âge/ancienneté) est faite par
// load_neo4j.py ; ce fichier documente / permet un rejeu manuel via cypher-shell.
// =====================================================================

// ---------------------------------------------------------------------
// 1. CONTRAINTES
//    Canonique (Aura/Enterprise) : IS NODE KEY. Sur Neo4j Community (local) : IS UNIQUE.
// ---------------------------------------------------------------------
CREATE CONSTRAINT Etablissement_uai IF NOT EXISTS FOR (n:Etablissement) REQUIRE n.code_uai   IS UNIQUE;
CREATE CONSTRAINT Contact_id        IF NOT EXISTS FOR (n:Contact)       REQUIRE n.id_contact IS UNIQUE;

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
// 3. CONTACTS DÉRIVÉS (derive:true => séparables des contacts réels, inertes en requête électorale)
//    rec = {id_contact, corps, genre, tranche_age, tranche_anciennete, type_affectation,
//           degre, statut_adhesion, qualite_donnee, source, annee_rentree, derive}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MERGE (c:Contact {id_contact: rec.id_contact})
SET c += {corps: rec.corps, genre: rec.genre, tranche_age: rec.tranche_age,
          tranche_anciennete: rec.tranche_anciennete, type_affectation: rec.type_affectation,
          degre: rec.degre, statut_adhesion: rec.statut_adhesion, qualite_donnee: rec.qualite_donnee,
          source: rec.source, annee_rentree: rec.annee_rentree, derive: rec.derive};

// ---------------------------------------------------------------------
// 4. RELATION  (:Contact)-[:TRAVAILLE_DANS {source, quotite, annee}]->(:Etablissement)
//    rec = {sourceId: Contact.id_contact, targetId: Etablissement.code_uai, source, quotite, annee}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (e:Etablissement {code_uai: rec.targetId})
MERGE (c)-[r:TRAVAILLE_DANS]->(e)
SET r += {source: rec.source, quotite: rec.quotite, annee: rec.annee};

// ---------------------------------------------------------------------
// 5. VÉRIFICATIONS
// ---------------------------------------------------------------------
// Invariant : effectif == nombre de contacts rattachés (doit renvoyer 0 ligne)
// MATCH (e:Etablissement)
// OPTIONAL MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e)
// WITH e, count(c) AS n WHERE n <> e.effectif RETURN count(e);
//
// Répartition par genre (~62% F attendu) :
// MATCH (c:Contact {derive:true}) RETURN c.genre, count(*) ORDER BY count(*) DESC;
//
// Aucune pollution des requêtes électorales (les dérivés n'ont pas de propension_vote) :
// MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e:Ecole)
// WHERE c.propension_vote >= 0.6 AND c.statut_adhesion <> 'adherent' RETURN count(c);
