import os, sys
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from .graph import get_graph, schema_string
from .config import OPENAI_API_KEY, OPENAI_MODEL

SYSTEM_PROMPT = """You are an expert at translating questions into Cypher for a payer policy knowledge graph.
Only use labels and relationships present in the schema below.

IMPORTANT:
- Use exact label and relationship names.
- Prefer MATCH (...) WHERE ... patterns.
- If the question asks about coverage for a CPT code, query relationships of type POLICY_DECISION and return the 'status' property.
- When appropriate, include useful properties like 'provenance' or 'deleted_on'.
- RETURN concise fields.

Schema:
{schema}
"""

USER_PROMPT = "{question}"

def generate_cypher(llm, schema: str, question: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", USER_PROMPT),
    ])
    msg = prompt.format_messages(schema=schema, question=question)
    resp = llm.invoke(msg)
    return resp.content.strip()

def run_query(cypher: str, graph):
    try:
        return graph.query(cypher)
    except Exception as e:
        print("Cypher failed:\n", cypher)
        raise e

def generate_natural_language_answer(llm, question: str, results):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant that answers user questions based on structured query results."),
        ("human", "Question: {question}\n\nQuery results:\n{results}\n\nPlease provide a clear, concise answer in natural language.")
    ])
    msg = prompt.format_messages(question=question, results=results)
    resp = llm.invoke(msg)
    return resp.content.strip()

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.ask 'your natural language question'")
        raise SystemExit(1)

    if not OPENAI_API_KEY:
        print("Missing OPENAI_API_KEY in environment.")
        raise SystemExit(1)

    question = sys.argv[1]
    graph = get_graph()
    schema = schema_string(graph)

    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=1)

    # Step 1: Generate Cypher
    cypher = generate_cypher(llm, schema, question)
    print("\n--- Generated Cypher ---\n" + cypher + "\n")

    # Step 2: Run Cypher
    rows = run_query(cypher, graph)
    print("--- Structured Results ---")
    for r in rows:
        print(r)

    # Step 3: Convert to Natural Language
    nl_answer = generate_natural_language_answer(llm, question, rows)
    print("\n--- Natural Language Answer ---\n" + nl_answer)

if __name__ == "__main__":
    main()
