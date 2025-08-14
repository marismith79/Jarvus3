from langchain_community.graphs import Neo4jGraph
from .config import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, NEO4J_DATABASE

def get_graph() -> Neo4jGraph:
    return Neo4jGraph(
        url=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE,
    )

def schema_string(graph: Neo4jGraph) -> str:
    """
    Returns a compact schema string that the LLM will condition on.
    """
    # Support both property-style and method-style implementations across versions
    schema_attr = getattr(graph, "get_schema", None)
    if callable(schema_attr):
        return schema_attr()
    if schema_attr is not None:
        return schema_attr
    # Fallback to the public API used by some versions
    schema_method = getattr(graph, "refresh_schema", None)
    if callable(schema_method):
        schema_method()
        value = getattr(graph, "schema", None)
        if value is not None:
            return value
    # Last resort
    return ""
