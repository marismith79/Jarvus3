import sys
from .graph import get_graph

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.run_cypher 'MATCH ... RETURN ...'")
        raise SystemExit(1)
    cypher = sys.argv[1]
    graph = get_graph()
    rows = graph.query(cypher)
    print(rows)

if __name__ == "__main__":
    main()
