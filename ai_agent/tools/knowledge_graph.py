"""
Tool for kg.query action
Connects to a real Neo4j database.
"""
import os
from neo4j import GraphDatabase

def query_neo4j(query: str, params: dict = None) -> dict:
    """
    Executes a Cypher query against a Neo4j database using credentials from environment variables.
    """
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        raise ValueError("NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set in .env file")

    driver = None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            print(f"Executing KG Query: {query} with params: {params}")
            result = session.run(query, params or {})
            
            # Convert records to a list of dictionaries
            records = [record.data() for record in result]
            count = len(records)
            
            return {"rows": records, "count": count}
    except Exception as e:
        print(f"Error connecting to or querying Neo4j: {e}")
        # Return a structured error to the agent
        return {"error": str(e), "count": 0, "rows": []}
    finally:
        if driver:
            driver.close()