from typing import Any, Dict, List, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from pydantic import BaseModel

from .ask import (
    generate_cypher,
    generate_natural_language_answer,
    run_query,
)
from .graph import get_graph, schema_string
from .config import OPENAI_API_KEY, OPENAI_MODEL
from langchain_openai import ChatOpenAI


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    cypher: str
    results: Union[List[Any], Dict[str, Any], str]


app = FastAPI(title="Payer KG Chat", version="0.1.0")

# Allow all origins for local development; tighten for production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def validate_env() -> None:
    if not OPENAI_API_KEY:
        # Fail-fast to surface configuration issues at boot.
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")


def _safe_serialize_results(rows: Any) -> Union[List[Any], Dict[str, Any], str]:
    try:
        # Most often rows is a list of dicts from Neo4jGraph.query
        if isinstance(rows, list):
            serialized: List[Any] = []
            for item in rows:
                try:
                    if isinstance(item, dict):
                        serialized.append(item)
                    else:
                        serialized.append(getattr(item, "data", item))
                except Exception:
                    serialized.append(str(item))
            return serialized
        if isinstance(rows, dict):
            return rows
        return str(rows)
    except Exception:
        return str(rows)


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        graph = get_graph()
        schema = schema_string(graph)

        llm = ChatOpenAI(model=OPENAI_MODEL, temperature=1)

        cypher = generate_cypher(llm, schema, req.message)
        rows = run_query(cypher, graph)
        answer = generate_natural_language_answer(llm, req.message, rows)

        return ChatResponse(
            answer=answer,
            cypher=cypher,
            results=_safe_serialize_results(rows),
        )
    except Exception as exc:  # Surface errors to client in a controlled way
        raise HTTPException(status_code=500, detail=str(exc))


BASE_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = BASE_DIR / "web"


@app.get("/")
def root() -> FileResponse:
    index_file = WEB_DIR / "index.html"
    return FileResponse(index_file)


# Serve static frontend assets
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")


