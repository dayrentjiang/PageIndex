"""
Flatten the nested tree structure JSON into a flat list of node rows
ready for database insertion.

Usage:
    python scripts/flatten_structure.py results/Blood-Donation-2024_structure.json
"""

import json
import sys
from pathlib import Path


def flatten_tree(structure: list, doc_name: str, parent_node_id: str | None = None, depth: int = 0) -> list[dict]:
    """Recursively flatten the nested tree into a flat list of rows."""
    rows = []
    for node in structure:
        row = {
            "node_id": node["node_id"],
            "doc_name": doc_name,
            "title": node.get("title", ""),
            "summary": node.get("summary", ""),
            "text": node.get("text", ""),
            "start_page": node.get("start_index"),
            "end_page": node.get("end_index"),
            "parent_node_id": parent_node_id,
            "depth": depth,
        }
        rows.append(row)

        if "nodes" in node:
            rows.extend(flatten_tree(node["nodes"], doc_name, node["node_id"], depth + 1))

    return rows


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/flatten_structure.py <structure.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    with open(input_path) as f:
        data = json.load(f)

    doc_name = data["doc_name"]
    rows = flatten_tree(data["structure"], doc_name)

    output_path = input_path.with_name(input_path.stem + "_flat.json")
    with open(output_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"Flattened {len(rows)} nodes → {output_path}")


if __name__ == "__main__":
    main()
