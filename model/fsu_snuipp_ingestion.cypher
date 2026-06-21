// =====================================================================
// FSU-SNUipp — Adhésion & base électorale (schéma en français)
// Contraintes + requêtes d'ingestion paramétrées (Neo4j 5.x)
// Chaque requête UNWIND prend une liste de dicts dans le paramètre $records.
// =====================================================================

// ---------------------------------------------------------------------
// 1. CONTRAINTES (NODE KEY = unicité + existence des clés)
// ---------------------------------------------------------------------
CREATE CONSTRAINT Contact_key         IF NOT EXISTS FOR (n:Contact)         REQUIRE (n.id_contact)   IS NODE KEY;
CREATE CONSTRAINT CercleProximite_key IF NOT EXISTS FOR (n:CercleProximite) REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT ObjectifAction_key  IF NOT EXISTS FOR (n:ObjectifAction)  REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Metier_key          IF NOT EXISTS FOR (n:Metier)          REQUIRE (n.code)         IS NODE KEY;
CREATE CONSTRAINT Adhesion_key        IF NOT EXISTS FOR (n:Adhesion)        REQUIRE (n.id_adhesion)  IS NODE KEY;
CREATE CONSTRAINT Ecole_key           IF NOT EXISTS FOR (n:Ecole)           REQUIRE (n.code_uai)     IS NODE KEY;
CREATE CONSTRAINT Circonscription_key IF NOT EXISTS FOR (n:Circonscription) REQUIRE (n.code_circo)   IS NODE KEY;
CREATE CONSTRAINT Section_key         IF NOT EXISTS FOR (n:Section)         REQUIRE (n.code_section) IS NODE KEY;
CREATE CONSTRAINT Departement_key     IF NOT EXISTS FOR (n:Departement)     REQUIRE (n.code_dept)    IS NODE KEY;
CREATE CONSTRAINT Academie_key        IF NOT EXISTS FOR (n:Academie)        REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Theme_key           IF NOT EXISTS FOR (n:Theme)           REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Action_key          IF NOT EXISTS FOR (n:Action)          REQUIRE (n.id_action)    IS NODE KEY;
CREATE CONSTRAINT TypeAction_key      IF NOT EXISTS FOR (n:TypeAction)      REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Campagne_key        IF NOT EXISTS FOR (n:Campagne)        REQUIRE (n.id_campagne)  IS NODE KEY;
CREATE CONSTRAINT Election_key        IF NOT EXISTS FOR (n:Election)        REQUIRE (n.id_election)  IS NODE KEY;
CREATE CONSTRAINT InstanceElue_key    IF NOT EXISTS FOR (n:InstanceElue)    REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Segment_key         IF NOT EXISTS FOR (n:Segment)         REQUIRE (n.id_segment)   IS NODE KEY;
CREATE CONSTRAINT Newsletter_key      IF NOT EXISTS FOR (n:Newsletter)      REQUIRE (n.nom)          IS NODE KEY;
CREATE CONSTRAINT Sollicitation_key   IF NOT EXISTS FOR (n:Sollicitation)   REQUIRE (n.id_sollicitation) IS NODE KEY;

// ---------------------------------------------------------------------
// 2. DONNÉES DE RÉFÉRENCE (vocabulaire contrôlé, à charger une fois)
// ---------------------------------------------------------------------
// Cercles de proximité
UNWIND [
  {nom:'section',      rang:1, role_attendu:'Organiser, recruter, faire campagne localement'},
  {nom:'adherent',     rang:2, role_attendu:'Se mobiliser, aller voter et faire voter'},
  {nom:'sympathisant', rang:3, role_attendu:'Relayer les messages, voter'},
  {nom:'contact',      rang:4, role_attendu:'Informer, voter'}
] AS r
MERGE (n:CercleProximite {nom:r.nom}) SET n += {rang:r.rang, role_attendu:r.role_attendu};

// Objectifs d'action (proximité multidimensionnelle — CR kick-off)
UNWIND [
  {nom:'voter',       description:'Aller voter aux élections professionnelles'},
  {nom:'voter_orga',  description:'Voter pour l\'organisation'},
  {nom:'adherer',     description:'Adhérer au syndicat'},
  {nom:'mobiliser',   description:'Se mobiliser sur une campagne'},
  {nom:'relayer',     description:'Relayer localement les messages'},
  {nom:'volontaire',  description:'Devenir volontaire / militant actif'}
] AS r
MERGE (n:ObjectifAction {nom:r.nom}) SET n += {description:r.description};

// Types d'action (poids dans le score d'engagement — à calibrer)
UNWIND [
  {nom:'petition', poids_engagement:0.3}, {nom:'enquete', poids_engagement:0.4},
  {nom:'sondage', poids_engagement:0.3}, {nom:'manifestation', poids_engagement:0.8},
  {nom:'greve', poids_engagement:0.9}, {nom:'reunion', poids_engagement:0.7},
  {nom:'enquete_carte_scolaire', poids_engagement:0.5}, {nom:'enquete_greve', poids_engagement:0.6},
  {nom:'stage', poids_engagement:0.7}, {nom:'ris', poids_engagement:0.6}
] AS r
MERGE (n:TypeAction {nom:r.nom}) SET n += {poids_engagement:r.poids_engagement};

// ---------------------------------------------------------------------
// 3. INGESTION DES NŒUDS (un bloc par label — passer $records)
// ---------------------------------------------------------------------
// Contact (enrichi SNUPers : identifiants, situation pro, clés de rapprochement)
UNWIND $records AS rec
MERGE (n:Contact {id_contact: rec.id_contact})
SET n += {id_snupers: rec.id_snupers, email: rec.email, telephone: rec.telephone,
          prenom: rec.prenom, nom: rec.nom, date_naissance: date(rec.date_naissance),
          statut_adhesion: rec.statut_adhesion, cycle_carriere: rec.cycle_carriere,
          grade: rec.grade, anciennete: rec.anciennete, type_affectation: rec.type_affectation,
          score_proximite: rec.score_proximite, score_engagement: rec.score_engagement,
          score_interet: rec.score_interet, propension_vote: rec.propension_vote,
          qualite_donnee: rec.qualite_donnee, methode_rapprochement: rec.methode_rapprochement,
          consentement_email: rec.consentement_email,
          source: rec.source, cree_le: datetime(rec.cree_le)};

// Newsletter
UNWIND $records AS rec
MERGE (n:Newsletter {nom: rec.nom}) SET n += {niveau: rec.niveau, outil: rec.outil};

// Sollicitation (outils de campagne : SNUTELLA)
UNWIND $records AS rec
MERGE (n:Sollicitation {id_sollicitation: rec.id_sollicitation})
SET n += {canal: rec.canal, date: date(rec.date), issue: rec.issue, outil: rec.outil};

// Metier
UNWIND $records AS rec
MERGE (n:Metier {code: rec.code}) SET n += {libelle: rec.libelle, categorie: rec.categorie};

// Adhesion
UNWIND $records AS rec
MERGE (n:Adhesion {id_adhesion: rec.id_adhesion})
SET n += {annee: rec.annee, date_debut: date(rec.date_debut), date_fin: date(rec.date_fin),
          statut: rec.statut, cotisation_payee: rec.cotisation_payee, montant: rec.montant};

// Ecole (+ open data EN : géolocalisation, source)
UNWIND $records AS rec
MERGE (n:Ecole {code_uai: rec.code_uai})
SET n += {nom: rec.nom, type_ecole: rec.type_ecole, effectif: rec.effectif, nb_adherents: rec.nb_adherents,
          latitude: rec.latitude, longitude: rec.longitude, source: rec.source};

// Circonscription (+ vigilance redécoupages open data)
UNWIND $records AS rec
MERGE (n:Circonscription {code_circo: rec.code_circo})
SET n += {nom: rec.nom, effectif: rec.effectif, nom_ien: rec.nom_ien,
          date_maj: date(rec.date_maj), source: rec.source};

// Section
UNWIND $records AS rec
MERGE (n:Section {code_section: rec.code_section})
SET n += {nom: rec.nom, est_drom: rec.est_drom, nb_adherents: rec.nb_adherents, nb_elus_2022: rec.nb_elus_2022};

// Departement
UNWIND $records AS rec
MERGE (n:Departement {code_dept: rec.code_dept})
SET n += {nom: rec.nom, est_drom: rec.est_drom, effectif: rec.effectif};

// Academie
UNWIND $records AS rec
MERGE (n:Academie {nom: rec.nom}) SET n += {region: rec.region};

// Theme
UNWIND $records AS rec
MERGE (n:Theme {nom: rec.nom}) SET n += {categorie: rec.categorie, est_prioritaire: rec.est_prioritaire};

// Action
UNWIND $records AS rec
MERGE (n:Action {id_action: rec.id_action})
SET n += {nom: rec.nom, date: date(rec.date), canal: rec.canal};

// Campagne
UNWIND $records AS rec
MERGE (n:Campagne {id_campagne: rec.id_campagne})
SET n += {nom: rec.nom, date_envoi: date(rec.date_envoi), canal: rec.canal, type: rec.type};

// Election
UNWIND $records AS rec
MERGE (n:Election {id_election: rec.id_election})
SET n += {nom: rec.nom, annee: rec.annee, date: date(rec.date), perimetre: rec.perimetre};

// InstanceElue
UNWIND $records AS rec
MERGE (n:InstanceElue {nom: rec.nom}) SET n += {niveau: rec.niveau, sieges: rec.sieges};

// Segment
UNWIND $records AS rec
MERGE (n:Segment {id_segment: rec.id_segment})
SET n += {nom: rec.nom, axe: rec.axe, priorite: rec.priorite, taille_estimee: rec.taille_estimee, regle: rec.regle};

// ---------------------------------------------------------------------
// 4. INGESTION DES RELATIONS (records: {sourceId, targetId, <props>})
// ---------------------------------------------------------------------
// Contact -[:EXERCE_METIER]-> Metier
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Metier {code: rec.targetId})
MERGE (s)-[:EXERCE_METIER]->(e);

// Contact -[:DANS_CERCLE]-> CercleProximite (version = traçabilité de la méthode de calcul)
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:CercleProximite {nom: rec.targetId})
MERGE (s)-[r:DANS_CERCLE]->(e) SET r += {depuis: date(rec.depuis), score: rec.score, version: rec.version};

// Contact -[:A_PROPENSION]-> ObjectifAction  (un enregistrement par contact x objectif)
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:ObjectifAction {nom: rec.targetId})
MERGE (s)-[r:A_PROPENSION]->(e) SET r += {score: rec.score, calcule_le: date(rec.calcule_le)};

// Contact -[:A_ADHESION]-> Adhesion
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Adhesion {id_adhesion: rec.targetId})
MERGE (s)-[:A_ADHESION]->(e);

// Adhesion -[:ADHESION_DANS_SECTION]-> Section
UNWIND $records AS rec
MATCH (s:Adhesion {id_adhesion: rec.sourceId}) MATCH (e:Section {code_section: rec.targetId})
MERGE (s)-[:ADHESION_DANS_SECTION]->(e);

// Contact -[:RATTACHE_A]-> Section
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Section {code_section: rec.targetId})
MERGE (s)-[:RATTACHE_A]->(e);

// Contact -[:TRAVAILLE_DANS]-> Ecole
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Ecole {code_uai: rec.targetId})
MERGE (s)-[r:TRAVAILLE_DANS]->(e) SET r += {depuis: date(rec.depuis)};

// Ecole -[:ECOLE_DANS_CIRCO]-> Circonscription
UNWIND $records AS rec
MATCH (s:Ecole {code_uai: rec.sourceId}) MATCH (e:Circonscription {code_circo: rec.targetId})
MERGE (s)-[:ECOLE_DANS_CIRCO]->(e);

// Circonscription -[:CIRCO_DANS_DEPARTEMENT]-> Departement
UNWIND $records AS rec
MATCH (s:Circonscription {code_circo: rec.sourceId}) MATCH (e:Departement {code_dept: rec.targetId})
MERGE (s)-[:CIRCO_DANS_DEPARTEMENT]->(e);

// Section -[:SECTION_COUVRE]-> Departement
UNWIND $records AS rec
MATCH (s:Section {code_section: rec.sourceId}) MATCH (e:Departement {code_dept: rec.targetId})
MERGE (s)-[:SECTION_COUVRE]->(e);

// Departement -[:DEPARTEMENT_DANS_ACADEMIE]-> Academie
UNWIND $records AS rec
MATCH (s:Departement {code_dept: rec.sourceId}) MATCH (e:Academie {nom: rec.targetId})
MERGE (s)-[:DEPARTEMENT_DANS_ACADEMIE]->(e);

// Contact -[:INTERESSE_PAR]-> Theme
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Theme {nom: rec.targetId})
MERGE (s)-[r:INTERESSE_PAR]->(e) SET r += {poids: rec.poids, source: rec.source};

// Contact -[:A_PARTICIPE_A]-> Action
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Action {id_action: rec.targetId})
MERGE (s)-[r:A_PARTICIPE_A]->(e) SET r += {date: date(rec.date), role: rec.role};

// Action -[:DE_TYPE]-> TypeAction
UNWIND $records AS rec
MATCH (s:Action {id_action: rec.sourceId}) MATCH (e:TypeAction {nom: rec.targetId})
MERGE (s)-[:DE_TYPE]->(e);

// Action -[:ACTION_SUR_THEME]-> Theme
UNWIND $records AS rec
MATCH (s:Action {id_action: rec.sourceId}) MATCH (e:Theme {nom: rec.targetId})
MERGE (s)-[:ACTION_SUR_THEME]->(e);

// Action -[:DANS_CAMPAGNE]-> Campagne
UNWIND $records AS rec
MATCH (s:Action {id_action: rec.sourceId}) MATCH (e:Campagne {id_campagne: rec.targetId})
MERGE (s)-[:DANS_CAMPAGNE]->(e);

// Contact -[:CIBLE_PAR]-> Campagne
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Campagne {id_campagne: rec.targetId})
MERGE (s)-[r:CIBLE_PAR]->(e) SET r += {envoye: rec.envoye, ouvert: rec.ouvert, clique: rec.clique, converti: rec.converti, date_envoi: date(rec.date_envoi)};

// Contact -[:ABONNE_A]-> Newsletter
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Newsletter {nom: rec.targetId})
MERGE (s)-[r:ABONNE_A]->(e) SET r += {depuis: date(rec.depuis)};

// Newsletter -[:EMISE_PAR]-> Section (newsletters départementales)
UNWIND $records AS rec
MATCH (s:Newsletter {nom: rec.sourceId}) MATCH (e:Section {code_section: rec.targetId})
MERGE (s)-[:EMISE_PAR]->(e);

// Campagne -[:VIA_NEWSLETTER]-> Newsletter
UNWIND $records AS rec
MATCH (s:Campagne {id_campagne: rec.sourceId}) MATCH (e:Newsletter {nom: rec.targetId})
MERGE (s)-[:VIA_NEWSLETTER]->(e);

// Contact -[:A_RECU]-> Sollicitation
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Sollicitation {id_sollicitation: rec.targetId})
MERGE (s)-[:A_RECU]->(e);

// Sollicitation -[:RELANCE_DANS_CAMPAGNE]-> Campagne
UNWIND $records AS rec
MATCH (s:Sollicitation {id_sollicitation: rec.sourceId}) MATCH (e:Campagne {id_campagne: rec.targetId})
MERGE (s)-[:RELANCE_DANS_CAMPAGNE]->(e);

// Contact -[:MILITANT_DANS]-> Circonscription (déclaratif sections)
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Circonscription {code_circo: rec.targetId})
MERGE (s)-[r:MILITANT_DANS]->(e) SET r += {source: rec.source};

// Ecole -[:A_REPONDU_A]-> Action (enquêtes carte scolaire / grève — granularité école)
UNWIND $records AS rec
MATCH (s:Ecole {code_uai: rec.sourceId}) MATCH (e:Action {id_action: rec.targetId})
MERGE (s)-[r:A_REPONDU_A]->(e) SET r += {date: date(rec.date), nb_repondants: rec.nb_repondants};

// Campagne -[:CAMPAGNE_SUR_THEME]-> Theme
UNWIND $records AS rec
MATCH (s:Campagne {id_campagne: rec.sourceId}) MATCH (e:Theme {nom: rec.targetId})
MERGE (s)-[:CAMPAGNE_SUR_THEME]->(e);

// Campagne -[:CAMPAGNE_POUR_ELECTION]-> Election
UNWIND $records AS rec
MATCH (s:Campagne {id_campagne: rec.sourceId}) MATCH (e:Election {id_election: rec.targetId})
MERGE (s)-[:CAMPAGNE_POUR_ELECTION]->(e);

// Contact -[:A_VOTE_A]-> Election
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Election {id_election: rec.targetId})
MERGE (s)-[r:A_VOTE_A]->(e) SET r += {a_vote: rec.a_vote, canal: rec.canal, college: rec.college};

// Election -[:ELECTION_ELIT]-> InstanceElue
UNWIND $records AS rec
MATCH (s:Election {id_election: rec.sourceId}) MATCH (e:InstanceElue {nom: rec.targetId})
MERGE (s)-[:ELECTION_ELIT]->(e);

// Metier -[:VOTE_POUR]-> InstanceElue
UNWIND $records AS rec
MATCH (s:Metier {code: rec.sourceId}) MATCH (e:InstanceElue {nom: rec.targetId})
MERGE (s)-[r:VOTE_POUR]->(e) SET r += {college: rec.college};

// Contact -[:DANS_SEGMENT]-> Segment
UNWIND $records AS rec
MATCH (s:Contact {id_contact: rec.sourceId}) MATCH (e:Segment {id_segment: rec.targetId})
MERGE (s)-[r:DANS_SEGMENT]->(e) SET r += {affecte_le: date(rec.affecte_le)};
