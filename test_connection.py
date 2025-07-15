from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"

driver = GraphDatabase.driver(uri, auth=(user, password))

def connect():
    with driver.session() as session:
        greeting = session.run("RETURN 'Hello' AS message").single()
        print(greeting['message'])

connect()
driver.close()