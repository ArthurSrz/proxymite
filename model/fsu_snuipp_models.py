"""
Modèles Pydantic — FSU-SNUipp : adhésion & base électorale (schéma en français).

Nœuds + relations générés depuis le data model Neo4j. Chaque classe de nœud porte
un `node_label` ; chaque classe de relation porte le pattern (start)-[:TYPE]->(end)
et les clés des nœuds source/cible.
"""

from pydantic import BaseModel
from datetime import datetime, date
from typing import ClassVar, Optional


# --------------------------------------------------------------------------- #
# NŒUDS
# --------------------------------------------------------------------------- #

class Contact(BaseModel):
    """Personnel des écoles (~150 000) : électeur potentiel et cible de communication."""
    node_label: ClassVar[str] = "Contact"

    id_contact: str
    id_snupers: Optional[str] = None        # identifiant SNUPers (socle de jointure)
    email: Optional[str] = None
    telephone: Optional[str] = None         # clé de rapprochement
    prenom: Optional[str] = None
    nom: Optional[str] = None
    date_naissance: Optional[date] = None   # clé de rapprochement
    statut_adhesion: Optional[str] = None   # adherent | ancien_adherent | jamais_adherent | inconnu
    cycle_carriere: Optional[str] = None    # entrant | milieu | fin_carriere | retraite
    grade: Optional[str] = None             # SNUPers
    anciennete: Optional[int] = None        # années d'ancienneté (SNUPers)
    type_affectation: Optional[str] = None  # titulaire | remplacant | ... (SNUPers)
    score_proximite: Optional[float] = None
    score_engagement: Optional[float] = None
    score_interet: Optional[float] = None
    propension_vote: Optional[float] = None  # probabilité estimée de voter (réserve de voix)
    qualite_donnee: Optional[float] = None
    methode_rapprochement: Optional[str] = None  # directe | probabiliste
    consentement_email: Optional[bool] = None
    source: Optional[str] = None
    cree_le: Optional[datetime] = None

    corps: Optional[str] = None             # depuis idCorps SNUPers (PEHCLA, PEEX00...)
    genre: Optional[str] = None             # M | F
    degre: Optional[str] = None             # 1d | 2d


class CercleProximite(BaseModel):
    """Cercle de proximité : section, adherent, sympathisant, contact."""
    node_label: ClassVar[str] = "CercleProximite"

    nom: str                        # section | adherent | sympathisant | contact
    rang: Optional[int] = None      # 1=section ... 4=contact
    role_attendu: Optional[str] = None


class ObjectifAction(BaseModel):
    """Objectif d'action — proximité multidimensionnelle (CR kick-off)."""
    node_label: ClassVar[str] = "ObjectifAction"

    nom: str                        # voter | voter_orga | adherer | mobiliser | relayer | volontaire
    description: Optional[str] = None


class Metier(BaseModel):
    """Métier / fonction (premier degré)."""
    node_label: ClassVar[str] = "Metier"

    code: str
    libelle: Optional[str] = None   # Professeur des écoles, AESH, PsyEN, Directeur, AED...
    categorie: Optional[str] = None  # enseignant | non_enseignant


class Adhesion(BaseModel):
    """Adhésion annuelle : historique et cotisation."""
    node_label: ClassVar[str] = "Adhesion"

    id_adhesion: str
    annee: Optional[int] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    statut: Optional[str] = None     # active | lapsed
    cotisation_payee: Optional[bool] = None
    montant: Optional[float] = None


class Ecole(BaseModel):
    """École — plus petit échelon : base adhérente et réserve de voix la plus fine."""
    node_label: ClassVar[str] = "Ecole"

    code_uai: str                    # identifiant UAI/RNE
    nom: Optional[str] = None
    type_ecole: Optional[str] = None  # maternelle | elementaire | primaire
    effectif: Optional[int] = None
    nb_adherents: Optional[int] = None
    latitude: Optional[float] = None  # open data EN
    longitude: Optional[float] = None  # open data EN
    source: Optional[str] = None      # open_data_EN | local


class Inconnu(BaseModel):
    """Nœud synthétique matérialisant un ETP inconnu du syndicat (open data effectifs EN).

    1 Inconnu = 1 ETP arrondi. Le pool d'Inconnus d'un établissement représente les
    enseignants que le syndicat n'a pas encore identifiés. Lors de la réconciliation avec
    les contacts réels (SNUPers), des Inconnus sont supprimés pour maintenir l'invariant :
    effectif == count(Contact TRAVAILLE_DANS) + count(Inconnu TRAVAILLE_DANS).
    """
    node_label: ClassVar[str] = "Inconnu"

    id_inconnu: str                          # "{uai}#{index}"
    corps: Optional[str] = None              # Professeur des écoles | Agrégés | Certifiés | ...
    genre: Optional[str] = None              # F | H (réparti depuis la marginale femmes)
    tranche_age: Optional[str] = None        # moins_35 | 35_50 | 50_plus | inconnu
    tranche_anciennete: Optional[str] = None # moins_2 | 2_5 | 5_8 | 8_plus | inconnu
    type_affectation: Optional[str] = None   # titulaire | non_titulaire
    degre: Optional[str] = None              # 1d | 2d
    annee_rentree: Optional[int] = None      # 2024
    source: Optional[str] = None             # effectifs_EN_2024


class Etablissement(BaseModel):
    """Établissement (open data EN, 1er + 2nd degré) — nœud parapluie de la maille la plus fine.

    Généralise `Ecole` pour couvrir collèges/lycées (FSU = 1er + 2nd degré). Les nœuds de degré 1d
    portent AUSSI le label `:Ecole` (compat. avec la maille premier degré existante).
    `effectif = round(etp_enseignants)` = count(Contact) + count(Inconnu) rattachés (invariant).
    """
    node_label: ClassVar[str] = "Etablissement"

    code_uai: str                     # identifiant UAI/RNE (clé)
    nom: Optional[str] = None
    type_etablissement: Optional[str] = None  # Ecole | Collège | Lycée | EREA
    secteur: Optional[str] = None     # Public | Privé
    commune: Optional[str] = None
    code_postal: Optional[str] = None
    code_departement: Optional[str] = None
    libelle_departement: Optional[str] = None
    code_academie: Optional[str] = None
    libelle_academie: Optional[str] = None
    code_region: Optional[str] = None
    libelle_region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    degre: Optional[str] = None       # 1d | 2d
    nb_eleves: Optional[int] = None
    effectif: Optional[int] = None    # round(etp_enseignants) = count(Contact) + count(Inconnu)
    nb_contacts_reels: Optional[int] = None    # cache : count(Contact TRAVAILLE_DANS)
    nb_contacts_derives: Optional[int] = None  # cache : count(Inconnu TRAVAILLE_DANS)
    depassement: Optional[int] = None          # nb_reels - effectif quand réels > ETP
    source: Optional[str] = None      # open_data_EN


class Circonscription(BaseModel):
    """Circonscription (IEN) — regroupement d'écoles."""
    node_label: ClassVar[str] = "Circonscription"

    code_circo: str
    nom: Optional[str] = None
    effectif: Optional[int] = None
    nom_ien: Optional[str] = None
    date_maj: Optional[date] = None   # vigilance redécoupages (open data parfois obsolète)
    source: Optional[str] = None      # open_data_EN | local


class Newsletter(BaseModel):
    """Newsletter nationale (Brevo) ou départementale (Brevo départemental)."""
    node_label: ClassVar[str] = "Newsletter"

    nom: str
    niveau: Optional[str] = None      # nationale | departementale
    outil: Optional[str] = None       # brevo | brevo_departemental


class Sollicitation(BaseModel):
    """Relance enregistrée dans les outils de campagne (SNUTELLA) : appel, SMS, email."""
    node_label: ClassVar[str] = "Sollicitation"

    id_sollicitation: str
    canal: Optional[str] = None       # appel | sms | email
    date: Optional[date] = None
    issue: Optional[str] = None       # decroche | repondeur | deja_vote | refus | ...
    outil: Optional[str] = None       # snutella | autre


class Section(BaseModel):
    """Section départementale (101) — coeur de la machine militante."""
    node_label: ClassVar[str] = "Section"

    code_section: str
    nom: Optional[str] = None
    est_drom: Optional[bool] = None
    nb_adherents: Optional[int] = None
    nb_elus_2022: Optional[int] = None


class Departement(BaseModel):
    """Département : maille géographique et réservoir électoral."""
    node_label: ClassVar[str] = "Departement"

    code_dept: str
    nom: Optional[str] = None
    est_drom: Optional[bool] = None
    effectif: Optional[int] = None


class Academie(BaseModel):
    """Académie / regroupement régional."""
    node_label: ClassVar[str] = "Academie"

    nom: str
    code_academie: Optional[str] = None
    region: Optional[str] = None
    effectif: Optional[int] = None    # rollup : somme des effectifs des départements


class Region(BaseModel):
    """Région administrative (19) — niveau géographique le plus haut (open data EN)."""
    node_label: ClassVar[str] = "Region"

    code_region: str
    nom: Optional[str] = None
    effectif: Optional[int] = None    # rollup : somme des effectifs des académies


class Theme(BaseModel):
    """Centre d'intérêt / sujet de préoccupation."""
    node_label: ClassVar[str] = "Theme"

    nom: str                        # conditions_travail, remuneration, inclusion, carte_scolaire...
    categorie: Optional[str] = None
    est_prioritaire: Optional[bool] = None


class Action(BaseModel):
    """Action de mobilisation (pétition, enquête, sondage, manifestation...)."""
    node_label: ClassVar[str] = "Action"

    id_action: str
    nom: Optional[str] = None
    date: Optional[date] = None
    canal: Optional[str] = None


class TypeAction(BaseModel):
    """Type d'action : petition | enquete | sondage | manifestation | greve | reunion."""
    node_label: ClassVar[str] = "TypeAction"

    nom: str
    poids_engagement: Optional[float] = None


class Campagne(BaseModel):
    """Campagne email/SMS — source de collecte et vecteur d'exposition."""
    node_label: ClassVar[str] = "Campagne"

    id_campagne: str
    nom: Optional[str] = None
    date_envoi: Optional[date] = None
    canal: Optional[str] = None      # email | sms
    type: Optional[str] = None       # mobilisation | communication_continue | electorale


class Election(BaseModel):
    """Élection professionnelle (ex : 2022, décembre 2026)."""
    node_label: ClassVar[str] = "Election"

    id_election: str
    nom: Optional[str] = None
    annee: Optional[int] = None
    date: Optional[date] = None
    perimetre: Optional[str] = None


class InstanceElue(BaseModel):
    """Instance représentative élue (CSA, CAPN, CAPD, CCP AESH...)."""
    node_label: ClassVar[str] = "InstanceElue"

    nom: str
    niveau: Optional[str] = None     # national | academique | departemental
    sieges: Optional[int] = None


class Segment(BaseModel):
    """Segment stratégique activable (proximité / intérêt / croisé)."""
    node_label: ClassVar[str] = "Segment"

    id_segment: str
    nom: Optional[str] = None
    axe: Optional[str] = None        # proximite | interet | croise
    priorite: Optional[int] = None
    taille_estimee: Optional[int] = None
    regle: Optional[str] = None


# --------------------------------------------------------------------------- #
# RELATIONS  (sourceId = clé du nœud départ, targetId = clé du nœud arrivée)
# --------------------------------------------------------------------------- #

class ExerceMetier(BaseModel):
    relationship_type: ClassVar[str] = "EXERCE_METIER"
    pattern: ClassVar[str] = "(:Contact)-[:EXERCE_METIER]->(:Metier)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Metier.code


class DansCercle(BaseModel):
    relationship_type: ClassVar[str] = "DANS_CERCLE"
    pattern: ClassVar[str] = "(:Contact)-[:DANS_CERCLE]->(:CercleProximite)"
    sourceId: str   # Contact.id_contact
    targetId: str   # CercleProximite.nom
    depuis: Optional[date] = None
    score: Optional[float] = None
    version: Optional[str] = None   # version de la méthode de calcul (traçabilité, prudence n°3)


class APropension(BaseModel):
    """Propension d'un contact pour un objectif d'action (score par objectif)."""
    relationship_type: ClassVar[str] = "A_PROPENSION"
    pattern: ClassVar[str] = "(:Contact)-[:A_PROPENSION]->(:ObjectifAction)"
    sourceId: str   # Contact.id_contact
    targetId: str   # ObjectifAction.nom
    score: Optional[float] = None
    calcule_le: Optional[date] = None


class AAdhesion(BaseModel):
    relationship_type: ClassVar[str] = "A_ADHESION"
    pattern: ClassVar[str] = "(:Contact)-[:A_ADHESION]->(:Adhesion)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Adhesion.id_adhesion


class AdhesionDansSection(BaseModel):
    relationship_type: ClassVar[str] = "ADHESION_DANS_SECTION"
    pattern: ClassVar[str] = "(:Adhesion)-[:ADHESION_DANS_SECTION]->(:Section)"
    sourceId: str   # Adhesion.id_adhesion
    targetId: str   # Section.code_section


class RattacheA(BaseModel):
    relationship_type: ClassVar[str] = "RATTACHE_A"
    pattern: ClassVar[str] = "(:Contact)-[:RATTACHE_A]->(:Section)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Section.code_section


class TravailleDans(BaseModel):
    """Partagée par Contact et Inconnu : (:Contact|Inconnu)-[:TRAVAILLE_DANS]->(:Etablissement)."""
    relationship_type: ClassVar[str] = "TRAVAILLE_DANS"
    pattern: ClassVar[str] = "(:Contact|Inconnu)-[:TRAVAILLE_DANS]->(:Etablissement)"
    sourceId: str   # Contact.id_contact ou Inconnu.id_inconnu
    targetId: str   # Etablissement.code_uai
    depuis: Optional[date] = None    # contacts réels
    source: Optional[str] = None     # effectifs_EN_2024 | snupers
    quotite: Optional[float] = None  # 1.0 (Inconnu) ou réelle (Contact)
    annee: Optional[int] = None      # 2024


class EcoleDansCirco(BaseModel):
    relationship_type: ClassVar[str] = "ECOLE_DANS_CIRCO"
    pattern: ClassVar[str] = "(:Ecole)-[:ECOLE_DANS_CIRCO]->(:Circonscription)"
    sourceId: str   # Ecole.code_uai
    targetId: str   # Circonscription.code_circo


class CircoDansDepartement(BaseModel):
    relationship_type: ClassVar[str] = "CIRCO_DANS_DEPARTEMENT"
    pattern: ClassVar[str] = "(:Circonscription)-[:CIRCO_DANS_DEPARTEMENT]->(:Departement)"
    sourceId: str   # Circonscription.code_circo
    targetId: str   # Departement.code_dept


class SectionCouvre(BaseModel):
    relationship_type: ClassVar[str] = "SECTION_COUVRE"
    pattern: ClassVar[str] = "(:Section)-[:SECTION_COUVRE]->(:Departement)"
    sourceId: str   # Section.code_section
    targetId: str   # Departement.code_dept


class DansDepartement(BaseModel):
    """Établissement rattaché à son département (open data EN ; pas de circonscription dans la source)."""
    relationship_type: ClassVar[str] = "DANS_DEPARTEMENT"
    pattern: ClassVar[str] = "(:Etablissement)-[:DANS_DEPARTEMENT]->(:Departement)"
    sourceId: str   # Etablissement.code_uai
    targetId: str   # Departement.code_dept
    source: Optional[str] = None


class DepartementDansAcademie(BaseModel):
    relationship_type: ClassVar[str] = "DEPARTEMENT_DANS_ACADEMIE"
    pattern: ClassVar[str] = "(:Departement)-[:DEPARTEMENT_DANS_ACADEMIE]->(:Academie)"
    sourceId: str   # Departement.code_dept
    targetId: str   # Academie.nom
    source: Optional[str] = None


class AcademieDansRegion(BaseModel):
    relationship_type: ClassVar[str] = "ACADEMIE_DANS_REGION"
    pattern: ClassVar[str] = "(:Academie)-[:ACADEMIE_DANS_REGION]->(:Region)"
    sourceId: str   # Academie.nom
    targetId: str   # Region.code_region
    source: Optional[str] = None


class InteressePar(BaseModel):
    relationship_type: ClassVar[str] = "INTERESSE_PAR"
    pattern: ClassVar[str] = "(:Contact)-[:INTERESSE_PAR]->(:Theme)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Theme.nom
    poids: Optional[float] = None
    source: Optional[str] = None


class AParticipeA(BaseModel):
    relationship_type: ClassVar[str] = "A_PARTICIPE_A"
    pattern: ClassVar[str] = "(:Contact)-[:A_PARTICIPE_A]->(:Action)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Action.id_action
    date: Optional[date] = None
    role: Optional[str] = None


class DeType(BaseModel):
    relationship_type: ClassVar[str] = "DE_TYPE"
    pattern: ClassVar[str] = "(:Action)-[:DE_TYPE]->(:TypeAction)"
    sourceId: str   # Action.id_action
    targetId: str   # TypeAction.nom


class ActionSurTheme(BaseModel):
    relationship_type: ClassVar[str] = "ACTION_SUR_THEME"
    pattern: ClassVar[str] = "(:Action)-[:ACTION_SUR_THEME]->(:Theme)"
    sourceId: str   # Action.id_action
    targetId: str   # Theme.nom


class DansCampagne(BaseModel):
    relationship_type: ClassVar[str] = "DANS_CAMPAGNE"
    pattern: ClassVar[str] = "(:Action)-[:DANS_CAMPAGNE]->(:Campagne)"
    sourceId: str   # Action.id_action
    targetId: str   # Campagne.id_campagne


class CiblePar(BaseModel):
    relationship_type: ClassVar[str] = "CIBLE_PAR"
    pattern: ClassVar[str] = "(:Contact)-[:CIBLE_PAR]->(:Campagne)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Campagne.id_campagne
    envoye: Optional[bool] = None
    ouvert: Optional[bool] = None
    clique: Optional[bool] = None
    converti: Optional[bool] = None  # conversion observée
    date_envoi: Optional[date] = None


class CampagneSurTheme(BaseModel):
    relationship_type: ClassVar[str] = "CAMPAGNE_SUR_THEME"
    pattern: ClassVar[str] = "(:Campagne)-[:CAMPAGNE_SUR_THEME]->(:Theme)"
    sourceId: str   # Campagne.id_campagne
    targetId: str   # Theme.nom


class CampagnePourElection(BaseModel):
    relationship_type: ClassVar[str] = "CAMPAGNE_POUR_ELECTION"
    pattern: ClassVar[str] = "(:Campagne)-[:CAMPAGNE_POUR_ELECTION]->(:Election)"
    sourceId: str   # Campagne.id_campagne
    targetId: str   # Election.id_election


class AVoteA(BaseModel):
    relationship_type: ClassVar[str] = "A_VOTE_A"
    pattern: ClassVar[str] = "(:Contact)-[:A_VOTE_A]->(:Election)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Election.id_election
    a_vote: Optional[bool] = None
    canal: Optional[str] = None
    college: Optional[str] = None


class ElectionElit(BaseModel):
    relationship_type: ClassVar[str] = "ELECTION_ELIT"
    pattern: ClassVar[str] = "(:Election)-[:ELECTION_ELIT]->(:InstanceElue)"
    sourceId: str   # Election.id_election
    targetId: str   # InstanceElue.nom


class VotePour(BaseModel):
    relationship_type: ClassVar[str] = "VOTE_POUR"
    pattern: ClassVar[str] = "(:Metier)-[:VOTE_POUR]->(:InstanceElue)"
    sourceId: str   # Metier.code
    targetId: str   # InstanceElue.nom
    college: Optional[str] = None


class DansSegment(BaseModel):
    relationship_type: ClassVar[str] = "DANS_SEGMENT"
    pattern: ClassVar[str] = "(:Contact)-[:DANS_SEGMENT]->(:Segment)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Segment.id_segment
    affecte_le: Optional[date] = None


class AbonneA(BaseModel):
    relationship_type: ClassVar[str] = "ABONNE_A"
    pattern: ClassVar[str] = "(:Contact)-[:ABONNE_A]->(:Newsletter)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Newsletter.nom
    depuis: Optional[date] = None


class EmisePar(BaseModel):
    """Newsletter départementale émise par une section."""
    relationship_type: ClassVar[str] = "EMISE_PAR"
    pattern: ClassVar[str] = "(:Newsletter)-[:EMISE_PAR]->(:Section)"
    sourceId: str   # Newsletter.nom
    targetId: str   # Section.code_section


class ViaNewsletter(BaseModel):
    relationship_type: ClassVar[str] = "VIA_NEWSLETTER"
    pattern: ClassVar[str] = "(:Campagne)-[:VIA_NEWSLETTER]->(:Newsletter)"
    sourceId: str   # Campagne.id_campagne
    targetId: str   # Newsletter.nom


class ARecu(BaseModel):
    relationship_type: ClassVar[str] = "A_RECU"
    pattern: ClassVar[str] = "(:Contact)-[:A_RECU]->(:Sollicitation)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Sollicitation.id_sollicitation


class RelanceDansCampagne(BaseModel):
    relationship_type: ClassVar[str] = "RELANCE_DANS_CAMPAGNE"
    pattern: ClassVar[str] = "(:Sollicitation)-[:RELANCE_DANS_CAMPAGNE]->(:Campagne)"
    sourceId: str   # Sollicitation.id_sollicitation
    targetId: str   # Campagne.id_campagne


class MilitantDans(BaseModel):
    """Militant connu dans une circonscription (déclaratif section)."""
    relationship_type: ClassVar[str] = "MILITANT_DANS"
    pattern: ClassVar[str] = "(:Contact)-[:MILITANT_DANS]->(:Circonscription)"
    sourceId: str   # Contact.id_contact
    targetId: str   # Circonscription.code_circo
    source: Optional[str] = None


class ARepondu(BaseModel):
    """Réponse d'une ÉCOLE à une enquête (carte scolaire, grève) — granularité école."""
    relationship_type: ClassVar[str] = "A_REPONDU_A"
    pattern: ClassVar[str] = "(:Ecole)-[:A_REPONDU_A]->(:Action)"
    sourceId: str   # Ecole.code_uai
    targetId: str   # Action.id_action
    date: Optional[date] = None
    nb_repondants: Optional[int] = None
