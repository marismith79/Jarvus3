from .graph import get_graph, schema_string

def main():
    graph = get_graph()
    print("\n=== Neo4j Schema (labels / rels / properties) ===\n")
    print(schema_string(graph))
    print("\n=================================================\n")

if __name__ == "__main__":
    main()
