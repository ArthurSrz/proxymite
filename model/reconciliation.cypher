// =====================================================================
// Réconciliation Contact (SNUPers) ↔ Inconnu (effectifs EN)
// Templates Cypher documentés — exécutés par reconcile_snupers.py.
// =====================================================================

// ---------------------------------------------------------------------
// 1. CONTRAINTE Contact
// ---------------------------------------------------------------------
CREATE CONSTRAINT Contact_id IF NOT EXISTS FOR (n:Contact) REQUIRE n.id_contact IS UNIQUE;

// ---------------------------------------------------------------------
// 2. UPSERT CONTACTS RÉELS (SNUPers)
//    rec = {id_contact, id_snupers, nom, prenom, email, telephone, date_naissance,
//           genre, corps, type_affectation, score_proximite, propension_vote,
//           anciennete, degre, source}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MERGE (c:Contact {id_contact: rec.id_contact})
SET c += {id_snupers: rec.id_snupers, nom: rec.nom, prenom: rec.prenom,
          email: rec.email, telephone: rec.telephone,
          date_naissance: date(rec.date_naissance),
          genre: rec.genre, corps: rec.corps, type_affectation: rec.type_affectation,
          score_proximite: rec.score_proximite, propension_vote: rec.propension_vote,
          anciennete: rec.anciennete, degre: rec.degre, source: rec.source};

// ---------------------------------------------------------------------
// 3. LIEN TRAVAILLE_DANS  (:Contact)->(:Etablissement)
//    rec = {sourceId, targetId, source, annee}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (e:Etablissement {code_uai: rec.targetId})
MERGE (c)-[r:TRAVAILLE_DANS]->(e)
SET r += {source: rec.source, annee: rec.annee};

// ---------------------------------------------------------------------
// 4. DANS_CERCLE  (:Contact)->(:CercleProximite)
//    rec = {sourceId, targetId}  — targetId = section|adherent|sympathisant|contact
// ---------------------------------------------------------------------
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.sourceId})
MATCH (cp:CercleProximite {nom: rec.targetId})
MERGE (c)-[:DANS_CERCLE]->(cp);

// ---------------------------------------------------------------------
// 5. A_VOTE_A  (:Contact)->(:Election)
//    rec = {sourceId, electionId, annee}
// ---------------------------------------------------------------------
UNWIND $records AS rec
MERGE (el:Election {id_election: rec.electionId})
ON CREATE SET el.annee = rec.annee
WITH el, rec
MATCH (c:Contact {id_contact: rec.sourceId})
MERGE (c)-[v:A_VOTE_A]->(el)
SET v.a_vote = true;

// ---------------------------------------------------------------------
// 6. RÉCONCILIATION : suppression des Inconnus en trop
//    Pour chaque établissement avec des Contact réels, supprime les Inconnus
//    excédentaires pour maintenir : effectif == count(Contact) + count(Inconnu).
// ---------------------------------------------------------------------
MATCH (e:Etablissement)
WHERE e.effectif IS NOT NULL
OPTIONAL MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e)
WITH e, count(c) AS nb_reels
WHERE nb_reels > 0
OPTIONAL MATCH (i:Inconnu)-[:TRAVAILLE_DANS]->(e)
WITH e, nb_reels, collect(i) AS inconnus, count(i) AS nb_inconnus
WITH e, nb_reels, inconnus, nb_inconnus,
     CASE WHEN nb_reels >= e.effectif THEN nb_inconnus
          ELSE nb_inconnus - (e.effectif - nb_reels)
     END AS to_delete
WHERE to_delete > 0
UNWIND inconnus[0..to_delete] AS victim
DETACH DELETE victim
RETURN count(victim) AS deleted;

// ---------------------------------------------------------------------
// 7. MISE À JOUR DES CACHES ETABLISSEMENT
// ---------------------------------------------------------------------
MATCH (e:Etablissement)
OPTIONAL MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e)
OPTIONAL MATCH (i:Inconnu)-[:TRAVAILLE_DANS]->(e)
WITH e, count(DISTINCT c) AS nr, count(DISTINCT i) AS nd
SET e.nb_contacts_reels = nr,
    e.nb_contacts_derives = nd,
    e.depassement = CASE WHEN nr > e.effectif THEN nr - e.effectif ELSE null END;

// ---------------------------------------------------------------------
// 8. VÉRIFICATIONS
// ---------------------------------------------------------------------

// Invariant : aucun établissement ne doit avoir moins de nœuds rattachés que son effectif
// MATCH (e:Etablissement) WHERE e.effectif IS NOT NULL
// OPTIONAL MATCH (x)-[:TRAVAILLE_DANS]->(e) WHERE x:Contact OR x:Inconnu
// WITH e, count(x) AS n WHERE n < e.effectif
// RETURN e.code_uai, e.nom, e.effectif, n;

// Couverture par département
// MATCH (e:Etablissement)-[:DANS_DEPARTEMENT]->(d:Departement)
// RETURN d.nom, d.code_dept,
//        sum(e.effectif) AS potentiel,
//        sum(coalesce(e.nb_contacts_reels, 0)) AS connus,
//        round(toFloat(sum(coalesce(e.nb_contacts_reels, 0))) / sum(e.effectif), 3) AS taux_couverture
// ORDER BY taux_couverture ASC;

// Écoles à plus fort potentiel inconnu (cibles de prospection)
// MATCH (e:Etablissement)-[:DANS_DEPARTEMENT]->(d:Departement)
// RETURN e.code_uai, e.nom, e.commune, d.nom AS departement,
//        e.effectif, coalesce(e.nb_contacts_reels, 0) AS connus,
//        e.effectif - coalesce(e.nb_contacts_reels, 0) AS inconnus
// ORDER BY inconnus DESC LIMIT 100;
