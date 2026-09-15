import json
from pathlib import Path
from neo4j import GraphDatabase


# ============================================================
# CONFIGURATION
# ============================================================

GRAPH_FILE = Path("graph_data.json")

URI = "bolt://127.0.0.1:7687"
USERNAME = "neo4j"

# IMPORTANT:
# Replace this with the password you created for your
# ResumeKnowledgeGraph database.
PASSWORD = "Kavi@0607"


# ============================================================
# LOAD GRAPH JSON
# ============================================================

def load_graph():

    with open(
        GRAPH_FILE,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ============================================================
# CLEAN PROPERTIES
# ============================================================

def clean_properties(properties):

    if not properties:
        return {}

    cleaned = {}

    for key, value in properties.items():

        # Neo4j doesn't accept None as a property value
        if value is None:
            continue

        # Convert lists to strings if necessary
        if isinstance(value, list):

            value = [
                str(v)
                for v in value
                if v is not None
            ]

        # Convert dictionaries to JSON strings
        elif isinstance(value, dict):

            value = json.dumps(
                value,
                ensure_ascii=False
            )

        cleaned[key] = value

    return cleaned


# ============================================================
# CREATE NODE
# ============================================================

def create_node(
    tx,
    node
):

    node_id = node["id"]
    label = node["label"]
    properties = clean_properties(
        node.get("properties", {})
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Labels cannot safely be passed as normal parameters.
    # They are validated before being inserted.
    # --------------------------------------------------------

    safe_label = "".join(
        c
        for c in label
        if c.isalnum() or c == "_"
    )

    query = f"""
    MERGE (n:{safe_label} {{id: $id}})
    SET n += $properties
    """

    tx.run(
        query,
        id=node_id,
        properties=properties
    )


# ============================================================
# CREATE RELATIONSHIP
# ============================================================

def create_relationship(
    tx,
    relationship
):

    source = relationship["source"]
    target = relationship["target"]
    rel_type = relationship["type"]

    # --------------------------------------------------------
    # Sanitize relationship type
    # --------------------------------------------------------

    safe_type = "".join(
        c
        for c in rel_type
        if c.isalnum() or c == "_"
    )

    properties = clean_properties(
        relationship.get(
            "properties",
            {}
        )
    )

    query = f"""
    MATCH (a {{id: $source}})
    MATCH (b {{id: $target}})
    MERGE (a)-[r:{safe_type}]->(b)
    SET r += $properties
    """

    tx.run(
        query,
        source=source,
        target=target,
        properties=properties
    )


# ============================================================
# MAIN IMPORT
# ============================================================

def main():

    print("=" * 70)
    print("NEO4J GRAPH LOADER")
    print("=" * 70)

    # --------------------------------------------------------
    # Check graph file
    # --------------------------------------------------------

    if not GRAPH_FILE.exists():

        print(
            f"\nERROR: {GRAPH_FILE} not found."
        )

        return

    graph = load_graph()

    nodes = graph.get(
        "nodes",
        []
    )

    relationships = graph.get(
        "relationships",
        []
    )

    print()
    print(
        f"Graph file       : {GRAPH_FILE.resolve()}"
    )

    print(
        f"Nodes to import  : {len(nodes)}"
    )

    print(
        f"Relationships    : {len(relationships)}"
    )

    # --------------------------------------------------------
    # Connect
    # --------------------------------------------------------

    print()
    print(
        "Connecting to Neo4j..."
    )

    try:

        driver = GraphDatabase.driver(
            URI,
            auth=(
                USERNAME,
                PASSWORD
            )
        )

        driver.verify_connectivity()

        print(
            "Connection successful!"
        )

    except Exception as e:

        print(
            "\nERROR connecting to Neo4j:"
        )

        print(e)

        return

    # ========================================================
    # IMPORT
    # ========================================================

    try:

        with driver.session(
            database="neo4j"
        ) as session:

            # ------------------------------------------------
            # Create nodes
            # ------------------------------------------------

            print()
            print(
                "Importing nodes..."
            )

            for index, node in enumerate(
                nodes,
                start=1
            ):

                session.execute_write(
                    create_node,
                    node
                )

                if (
                    index % 25 == 0
                    or index == len(nodes)
                ):

                    print(
                        f"  Nodes: "
                        f"{index}/{len(nodes)}"
                    )

            # ------------------------------------------------
            # Create relationships
            # ------------------------------------------------

            print()
            print(
                "Importing relationships..."
            )

            successful_relationships = 0

            for index, relationship in enumerate(
                relationships,
                start=1
            ):

                try:

                    session.execute_write(
                        create_relationship,
                        relationship
                    )

                    successful_relationships += 1

                except Exception as e:

                    print(
                        f"\n  Relationship error "
                        f"#{index}: {e}"
                    )

                if (
                    index % 25 == 0
                    or index == len(relationships)
                ):

                    print(
                        f"  Relationships: "
                        f"{index}/{len(relationships)}"
                    )

        # ====================================================
        # VERIFY
        # ====================================================

        print()
        print(
            "=" * 70
        )

        print(
            "VERIFYING NEO4J"
        )

        print(
            "=" * 70
        )

        with driver.session(
            database="neo4j"
        ) as session:

            node_result = session.run(
                "MATCH (n) RETURN count(n) AS count"
            )

            node_count = (
                node_result.single()["count"]
            )

            relationship_result = session.run(
                """
                MATCH ()-[r]->()
                RETURN count(r) AS count
                """
            )

            relationship_count = (
                relationship_result.single()["count"]
            )

        print()
        print(
            f"Neo4j nodes         : {node_count}"
        )

        print(
            f"Neo4j relationships  : {relationship_count}"
        )

        print()
        print(
            f"JSON nodes           : {len(nodes)}"
        )

        print(
            f"JSON relationships    : {len(relationships)}"
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        print()

        if (
            node_count == len(nodes)
            and relationship_count == successful_relationships
        ):

            print(
                "SUCCESS: Graph imported correctly!"
            )

        else:

            print(
                "WARNING: Neo4j counts do not "
                "exactly match the JSON."
            )

        print()

    finally:

        driver.close()

    print(
        "=" * 70
    )

    print(
        "NEO4J IMPORT COMPLETE"
    )

    print(
        "=" * 70
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()