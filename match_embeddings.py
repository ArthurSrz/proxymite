"""
match_embeddings.py — Matching Contact ↔ Inconnu par embeddings LLM.

Pour chaque école ayant des Contact ET des Inconnu, sérialise les propriétés
de chaque nœud en texte, encode via text-embedding-3-small (OpenRouter),
calcule la similarité cosinus, et crée des relations PROBABLEMENT_IDENTIQUE {score}.

Usage :
    python match_embeddings.py            # toutes les écoles
    python match_embeddings.py 100        # 100 premières écoles (smoke test)
"""

import math
import os
import sys
import time

import numpy as np
import requests
from dotenv import load_dotenv
from neo4j import GraphDatabase

BATCH_EMBED = 500
BATCH_NEO4J = 2000

OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"
MODEL = "openai/text-embedding-3-small"


def serialize_contact(props):
    parts = ["Enseignant·e connu·e du syndicat"]
    if props.get("genre"):
        parts.append(f"genre: {props['genre']}")
    if props.get("corps"):
        parts.append(f"corps: {props['corps']}")
    if props.get("type_affectation"):
        parts.append(f"métier: {props['type_affectation']}")
    if props.get("anciennete") is not None:
        parts.append(f"ancienneté: tranche {props['anciennete']}")
    if props.get("cercle") is not None:
        parts.append(f"cercle: {props['cercle']}")
    return ", ".join(parts)


def serialize_inconnu(props):
    parts = ["Enseignant·e non identifié·e (statistique nationale)"]
    if props.get("genre"):
        parts.append(f"genre: {props['genre']}")
    if props.get("corps"):
        parts.append(f"corps: {props['corps']}")
    if props.get("type_affectation"):
        parts.append(f"affectation: {props['type_affectation']}")
    if props.get("tranche_age"):
        parts.append(f"tranche d'âge: {props['tranche_age']}")
    if props.get("tranche_anciennete"):
        parts.append(f"ancienneté: {props['tranche_anciennete']}")
    return ", ".join(parts)


def get_embeddings(texts, api_key):
    """Appelle OpenRouter pour obtenir les embeddings. Gère le batching."""
    all_embeddings = []
    for i in range(0, len(texts), BATCH_EMBED):
        batch = texts[i:i + BATCH_EMBED]
        for attempt in range(3):
            try:
                resp = requests.post(
                    OPENROUTER_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": MODEL, "input": batch},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()["data"]
                data.sort(key=lambda x: x["index"])
                all_embeddings.extend([d["embedding"] for d in data])
                break
            except Exception as e:
                if attempt < 2:
                    time.sleep(2 ** attempt)
                else:
                    raise
    return all_embeddings


def cosine_sim(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def greedy_match(contacts, inconnus, contact_embs, inconnu_embs):
    """Appariement greedy : pour chaque Contact, trouve l'Inconnu le plus similaire."""
    used = set()
    matches = []
    for ci, c in enumerate(contacts):
        best_score, best_ii = -1, -1
        for ii, inc in enumerate(inconnus):
            if ii in used:
                continue
            score = cosine_sim(contact_embs[ci], inconnu_embs[ii])
            if score > best_score:
                best_score = score
                best_ii = ii
        if best_ii >= 0:
            used.add(best_ii)
            matches.append({
                "contactId": c["id"],
                "inconnuId": inconnus[best_ii]["id"],
                "score": round(best_score, 4),
            })
    return matches


MATCH_CYPHER = """
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.contactId})
MATCH (i:Inconnu {id_inconnu: rec.inconnuId})
MERGE (c)-[r:PROBABLEMENT_IDENTIQUE]->(i)
SET r.score = rec.score
"""

CONTACT_EMB_CYPHER = """
UNWIND $records AS rec
MATCH (c:Contact {id_contact: rec.id})
SET c.embedding = rec.embedding
"""

INCONNU_EMB_CYPHER = """
UNWIND $records AS rec
MATCH (i:Inconnu {id_inconnu: rec.id})
SET i.embedding = rec.embedding
"""


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    load_dotenv()
    uri = os.environ["NEO4J_URI"]
    auth = (os.environ["NEO4J_USERNAME"], os.environ["NEO4J_PASSWORD"])
    db = os.environ.get("NEO4J_DATABASE", "neo4j")
    api_key = os.environ["OPENROUTER_API_KEY"]

    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        print(f"Connecté à {uri} (db={db})")

        # Trouver les écoles avec les deux populations
        result = driver.execute_query("""
            MATCH (c:Contact)-[:TRAVAILLE_DANS]->(e:Etablissement)<-[:TRAVAILLE_DANS]-(i:Inconnu)
            RETURN e.code_uai AS uai,
                   collect(DISTINCT {id: c.id_contact, genre: c.genre, corps: c.corps,
                           type_affectation: c.type_affectation, anciennete: c.anciennete,
                           cercle: c.cercle}) AS contacts,
                   collect(DISTINCT {id: i.id_inconnu, genre: i.genre, corps: i.corps,
                           type_affectation: i.type_affectation, tranche_age: i.tranche_age,
                           tranche_anciennete: i.tranche_anciennete}) AS inconnus
        """, database_=db)

        schools = result.records
        if limit:
            schools = schools[:limit]
        print(f"{len(schools)} écoles avec Contact + Inconnu")

        total_matches = []
        contact_emb_records, inconnu_emb_records = [], []
        total_texts = 0

        for idx, school in enumerate(schools):
            uai = school["uai"]
            contacts = school["contacts"]
            inconnus = school["inconnus"]

            texts_c = [serialize_contact(c) for c in contacts]
            texts_i = [serialize_inconnu(i) for i in inconnus]
            all_texts = texts_c + texts_i
            total_texts += len(all_texts)

            embs = get_embeddings(all_texts, api_key)
            contact_embs = embs[:len(contacts)]
            inconnu_embs = embs[len(contacts):]

            for c, emb in zip(contacts, contact_embs):
                contact_emb_records.append({"id": c["id"], "embedding": emb})
            for inc, emb in zip(inconnus, inconnu_embs):
                inconnu_emb_records.append({"id": inc["id"], "embedding": emb})

            matches = greedy_match(contacts, inconnus, contact_embs, inconnu_embs)
            total_matches.extend(matches)

            if (idx + 1) % 500 == 0 or idx == len(schools) - 1:
                print(f"  {idx + 1}/{len(schools)} écoles, {len(total_matches)} matches, "
                      f"{total_texts} textes encodés", flush=True)

        print(f"\nTotal : {len(total_matches)} paires appariées")

        if total_matches:
            scores = [m["score"] for m in total_matches]
            print(f"Score moyen : {sum(scores)/len(scores):.4f}, "
                  f"min : {min(scores):.4f}, max : {max(scores):.4f}")

            # Écrire les relations dans Neo4j
            print("Écriture des relations PROBABLEMENT_IDENTIQUE...")
            for i in range(0, len(total_matches), BATCH_NEO4J):
                chunk = total_matches[i:i + BATCH_NEO4J]
                driver.execute_query(MATCH_CYPHER, records=chunk, database_=db)
                print(f"  {min(i + BATCH_NEO4J, len(total_matches))}/{len(total_matches)}", end="\r")
            print(f"  {len(total_matches)}/{len(total_matches)} ✓")

            # Écrire les embeddings sur les nœuds
            print("Écriture des embeddings sur les Contact...")
            for i in range(0, len(contact_emb_records), BATCH_NEO4J):
                chunk = contact_emb_records[i:i + BATCH_NEO4J]
                driver.execute_query(CONTACT_EMB_CYPHER, records=chunk, database_=db)
                print(f"  {min(i + BATCH_NEO4J, len(contact_emb_records))}/{len(contact_emb_records)}", end="\r")
            print(f"  {len(contact_emb_records)}/{len(contact_emb_records)} ✓")

            print("Écriture des embeddings sur les Inconnu...")
            for i in range(0, len(inconnu_emb_records), BATCH_NEO4J):
                chunk = inconnu_emb_records[i:i + BATCH_NEO4J]
                driver.execute_query(INCONNU_EMB_CYPHER, records=chunk, database_=db)
                print(f"  {min(i + BATCH_NEO4J, len(inconnu_emb_records))}/{len(inconnu_emb_records)}", end="\r")
            print(f"  {len(inconnu_emb_records)}/{len(inconnu_emb_records)} ✓")

    print("Terminé.")


if __name__ == "__main__":
    main()
