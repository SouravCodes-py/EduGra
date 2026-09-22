from app.graph.connection import get_driver

def write_concepts(data: dict, embeddings: dict, subject: str = "uploaded"):
    driver = get_driver()
    with driver.session() as session:
        # 1. Merge all concept nodes with their definitions and embeddings
        for concept in data.get("concepts", []):
            name = concept["name"]
            definition = concept.get("definition", "")
            embedding = embeddings.get(name, [])
            session.run("""
                MERGE (c:Concept {name: $name})
                SET c.definition = $definition,
                    c.embedding = $embedding,
                    c.subject = $subject,
                    c.created_at = datetime()
            """, name=name, definition=definition, embedding=embedding, subject=subject)

        # 2. Merge all prerequisite relationships
        for concept in data.get("concepts", []):
            target_name = concept["name"]
            for prereq in concept.get("prerequisites", []):
                prereq_name = prereq.strip()
                if not prereq_name:
                    continue
                session.run("""
                    MERGE (a:Concept {name: $prereq})
                    MERGE (b:Concept {name: $target})
                    MERGE (a)-[r:PREREQUISITE_OF]->(b)
                    ON CREATE SET r.weight = 1.0
                """, prereq=prereq_name, target=target_name)
