import argparse
import json
from dataclasses import dataclass
from typing import Dict, List, Optional

from .graph import get_graph


@dataclass
class Metric:
    name: str
    cypher: str
    description: str


DEFAULT_METRICS: List[Metric] = [
    Metric(
        name="node_count",
        description="Total nodes in the graph",
        cypher="RETURN count(*) AS value",
    ),
    Metric(
        name="policy_nodes",
        description="Number of Policy nodes",
        cypher="MATCH (p:Policy) RETURN count(p) AS value",
    ),
    Metric(
        name="coverage_decisions",
        description="Number of POLICY_DECISION relationships",
        cypher="MATCH ()-[r:POLICY_DECISION]->() RETURN count(r) AS value",
    ),
    Metric(
        name="provenance_coverage",
        description="Share of nodes with provenance fields (url and retrieved_at)",
        cypher=(
            "MATCH (n) WITH count(n) AS total MATCH (n) "
            "WHERE exists(n.url) AND exists(n.retrieved_at) "
            "RETURN total AS total, count(n) AS with_prov, toFloat(count(n))/total AS value"
        ),
    ),
]


def run_metric(metric: Metric) -> Dict[str, object]:
    graph = get_graph()
    rows = graph.query(metric.cypher)
    # Expect single row with key 'value' (and optionally other keys)
    result: Dict[str, object] = {"name": metric.name, "description": metric.description}
    if rows:
        row = rows[0]
        if isinstance(row, dict):
            result.update(row)
        else:
            result["value"] = row
    return result


def run_all(metrics: Optional[List[Metric]] = None) -> List[Dict[str, object]]:
    metrics = metrics or DEFAULT_METRICS
    return [run_metric(m) for m in metrics]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate KG quality metrics")
    parser.add_argument(
        "--format",
        choices=["json", "table"],
        default="json",
        help="Output format",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    results = run_all()
    if args.format == "json":
        print(json.dumps(results, indent=2))
    else:
        # Minimal table view
        widths = {
            "name": max(len("name"), *(len(str(r.get("name", ""))) for r in results)),
            "value": max(len("value"), *(len(str(r.get("value", ""))) for r in results)),
        }
        header = f"{ 'name'.ljust(widths['name']) }  { 'value'.ljust(widths['value']) }"
        print(header)
        print("-" * len(header))
        for r in results:
            name = str(r.get("name", "")).ljust(widths["name"]) 
            value = str(r.get("value", "")).ljust(widths["value"]) 
            print(f"{name}  {value}")


if __name__ == "__main__":
    main()


