import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

_driver = None

def get_driver():
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
        password = os.getenv("NEO4J_PASSWORD")
        _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver

def close_driver():
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
