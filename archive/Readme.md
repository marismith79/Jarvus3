## Run the web chat UI

1. Create a `.env` (or export env vars) with your Neo4j and OpenAI config:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=neo4j
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4.1-mini
```

2. Install dependencies into your virtualenv:

```
pip install -r requirements.txt
```

3. Start the server (serves API and static frontend):

```
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

4. Open the UI at `http://localhost:8000` and chat.

---

CLI usage remains available:

- Dump schema:

```
python -m src.dump_schema
```

- Run ad-hoc Cypher:

```
python -m src.run_cypher "MATCH (n) RETURN n LIMIT 5"
```

- Ask a question from terminal:

```
python -m src.ask "What is the coverage decision for CPT 12345?"
```

- Ingest/update KG from payer policy URLs:

```
python -m src.ingest --url "https://insurer.com/policies/PA-1234"
python -m src.ingest --urls-file urls.txt
```

- Evaluate KG quality metrics:

```
python -m src.evaluate --format json
```