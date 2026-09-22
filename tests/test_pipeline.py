import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))
from app.agents.knowledge_extraction.extractor import extract_text
from app.agents.knowledge_extraction.llm_extract import extract_concepts
from app.agents.knowledge_extraction.embeddings import get_embedding
from app.graph.graph_writer import write_concepts
from app.graph.connection import get_driver

def run_test(file_path: str):
    print(f"=== Step 1: Extracting text from {os.path.basename(file_path)} ===")
    text = extract_text(file_path)
    print(f"Extracted {len(text)} characters from {os.path.basename(file_path)}")

    print("\n=== Step 2: Extracting Concepts and Prerequisites via LLM ===")
    data = extract_concepts(text)
    concepts = data.get("concepts", [])
    print(f"Successfully extracted {len(concepts)} concepts!")
    for c in concepts[:5]:
        print(f" - {c['name']} (Prerequisites: {c.get('prerequisites', [])})")

    print("\n=== Step 3: Generating Embeddings ===")
    embeddings = {c["name"]: get_embedding(c["name"]) for c in concepts}
    print(f"Generated embeddings for {len(embeddings)} concepts.")

    print("\n=== Step 4: Writing to Neo4j Knowledge Graph ===")
    write_concepts(data, embeddings, subject="sample")
    print("Concepts and PREREQUISITE_OF edges committed to Neo4j.")

    print("\n=== Step 5: Verifying Graph in Neo4j ===")
    driver = get_driver()
    with driver.session() as session:
        node_count = session.run("MATCH (c:Concept) RETURN count(c) AS count").single()["count"]
        edge_count = session.run("MATCH ()-[r:PREREQUISITE_OF]->() RETURN count(r) AS count").single()["count"]
        print(f"Total Concept Nodes in Neo4j: {node_count}")
        print(f"Total PREREQUISITE_OF Relationships: {edge_count}")

        print("\nGraph Preview (first 10 relationships):")
        records = session.run("""
            MATCH (a:Concept)-[r:PREREQUISITE_OF]->(b:Concept)
            RETURN a.name AS prereq, b.name AS concept
            LIMIT 10
        """)
        for r in records:
            print(f"  ({r['prereq']}) --[:PREREQUISITE_OF]--> ({r['concept']})")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_test(sys.argv[1])
    else:
        print("Usage: python3 tests/test_pipeline.py <path_to_file>")
        print("Example: python3 tests/test_pipeline.py tests/fixtures/sample.pdf")
        sys.exit(1)
