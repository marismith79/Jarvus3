import argparse
import io
import datetime as dt
import json
import re
from typing import Iterable, List, Optional

import requests
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from .config import OPENAI_MODEL
from .graph import get_graph, schema_string


SYSTEM_PROMPT_INGEST = """You are an expert Neo4j data engineer updating a payer policy knowledge graph.

Given the schema and the raw text content of a policy web page, produce Cypher write statements that:

- ONLY use labels, relationship types, and properties present in the schema.
- Are idempotent and safe: prefer MERGE for nodes/relationships; use SET to update properties.
- Include provenance for updated nodes/relationships, at minimum `url` and `retrieved_at` ISO datetime.
- Capture policy identifiers, titles, effective dates, and coverage decisions for CPT/HCPCS codes related to prior authorization.
- DO NOT delete data. If you need to inactivate, set a `deleted_on` timestamp property instead, if such a property exists in the schema.
- Keep statements concise. If multiple statements are needed, separate them with semicolons.

Output ONLY the Cypher statements. Do not include explanations.

Schema:
{schema}
"""

USER_PROMPT_INGEST = (
    "Source URL: {url}\n\nExtracted Text (may be truncated):\n" "{text}\n"
)


def _extract_text_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n")
    # Normalize whitespace and truncate very long pages to keep prompt size manageable
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]


def fetch_text_from_url(url: str, timeout: int = 30) -> str:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    content_type = resp.headers.get("Content-Type", "").lower()
    if "text/html" in content_type or url.lower().endswith((".html", ".htm")):
        return _extract_text_from_html(resp.text)
    if "application/pdf" in content_type or url.lower().endswith(".pdf"):
        try:
            from pypdf import PdfReader  # Lazy import

            reader = PdfReader(io.BytesIO(resp.content))  # type: ignore[name-defined]
            pages_text = []
            for page in reader.pages[:20]:  # Hard cap to avoid giant prompts
                pages_text.append(page.extract_text() or "")
            text = "\n".join(pages_text)
            return text[:8000]
        except Exception:
            # Fallback: return bytes length notice
            return f"[PDF content length: {len(resp.content)} bytes]"
    # Default: treat as text
    return resp.text[:8000]


def generate_update_cypher(llm: ChatOpenAI, schema: str, text: str, url: str) -> str:
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_INGEST),
            ("human", USER_PROMPT_INGEST),
        ]
    )
    msg = prompt.format_messages(schema=schema, text=text, url=url)
    resp = llm.invoke(msg)
    content = resp.content.strip()
    return _extract_cypher_block(content)


CODE_BLOCK_RE = re.compile(
    r"```(?:cypher|CYPHER)?\s*([\s\S]*?)```", re.IGNORECASE | re.MULTILINE
)


def _extract_cypher_block(text: str) -> str:
    match = CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def _split_statements(cypher: str) -> List[str]:
    # Simple splitter on semicolons not inside backticks or quotes
    statements: List[str] = []
    buf = []
    in_single = False
    in_double = False
    in_backtick = False
    for ch in cypher:
        if ch == "'" and not in_double and not in_backtick:
            in_single = not in_single
        elif ch == '"' and not in_single and not in_backtick:
            in_double = not in_double
        elif ch == "`" and not in_single and not in_double:
            in_backtick = not in_backtick
        if ch == ";" and not in_single and not in_double and not in_backtick:
            s = "".join(buf).strip()
            if s:
                statements.append(s)
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        statements.append(tail)
    return statements


def run_update_statements(statements: Iterable[str]) -> None:
    graph = get_graph()
    for stmt in statements:
        if not stmt:
            continue
        graph.query(stmt)


def ingest_urls(urls: List[str], model: Optional[str] = None) -> None:
    graph = get_graph()
    schema = schema_string(graph)
    llm = ChatOpenAI(model=model or OPENAI_MODEL, temperature=0)
    now_iso = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    for url in urls:
        text = fetch_text_from_url(url)
        # Append a standard footer with retrieval time to help LLM set provenance
        footer = f"\n\n[Provenance] url={url} retrieved_at={now_iso}"
        cypher = generate_update_cypher(llm, schema, text + footer, url)
        statements = _split_statements(cypher)
        run_update_statements(statements)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest payer policy pages and update the Neo4j knowledge graph"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", action="append", dest="urls", help="Policy page URL")
    group.add_argument(
        "--urls-file",
        type=str,
        help="Path to a text file with one URL per line",
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Override OPENAI_MODEL for ingestion"
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    urls: List[str] = []
    if args.urls:
        urls = list(args.urls)
    elif args.urls_file:
        with open(args.urls_file, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    ingest_urls(urls, model=args.model)


if __name__ == "__main__":
    main()


