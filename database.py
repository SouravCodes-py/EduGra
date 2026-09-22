import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

def init_db():
    # Load environment variables from a .env file if present
    load_dotenv()
    
    # Initialize the driver
    driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI"), 
        auth=(os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
    )

    # Create constraints
    with driver.session() as session:
        session.run("CREATE CONSTRAINT concept_name_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE")
        session.run("CREATE CONSTRAINT student_id_unique IF NOT EXISTS FOR (s:Student) REQUIRE s.id IS UNIQUE")
        print("Schema created.")

    # Close the driver connection
    driver.close()

if __name__ == "__main__":
    init_db()
