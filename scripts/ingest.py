"""
Full ingest pipeline: PDF → tree structure → flatten → insert to DB.

Usage:
    python scripts/ingest.py data/Blood-Donation-2024.pdf
    python scripts/ingest.py data/Some-Other-Doc.pdf --model gpt-4o-2024-11-20
"""

import argparse
import json
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from pageindex import config, page_index_main
from scripts.flatten_structure import flatten_tree
from scripts.load_to_db import DB_CONFIG, CREATE_TABLE, INSERT_SQL


def parse_pdf(pdf_path: str, model: str) -> dict:
    """Step 1: Parse PDF into tree structure."""
    print(f"\n[1/3] Parsing PDF → tree structure...")
    opt = config(
        model=model,
        if_add_node_id="yes",
        if_add_node_summary="yes",
        if_add_node_text="yes",
    )
    tree = page_index_main(pdf_path, opt)
    return tree


def flatten(tree: dict) -> list[dict]:
    """Step 2: Flatten tree into rows."""
    print(f"[2/3] Flattening tree...")
    rows = flatten_tree(tree["structure"], tree["doc_name"])
    print(f"       {len(rows)} nodes flattened")
    return rows


def insert_to_db(rows: list[dict]) -> None:
    """Step 3: Insert rows into PostgreSQL."""
    print(f"[3/3] Inserting into database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute(CREATE_TABLE)
    conn.commit()

    for row in rows:
        cur.execute(INSERT_SQL, row)
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM nodes WHERE doc_name = %s", (rows[0]["doc_name"],))
    count = cur.fetchone()[0]
    print(f"       {count} nodes in database for '{rows[0]['doc_name']}'")

    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest PDF: parse → flatten → DB")
    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--model", default="gpt-4o-2024-11-20", help="LLM model for parsing")
    parser.add_argument("--skip-parse", action="store_true", help="Skip parsing, use existing structure.json")
    args = parser.parse_args()

    pdf_name = os.path.splitext(os.path.basename(args.pdf_path))[0]
    output_dir = "./results"
    structure_file = f"{output_dir}/{pdf_name}_structure.json"

    if args.skip_parse:
        # Load existing structure
        if not os.path.exists(structure_file):
            print(f"No existing structure file: {structure_file}")
            sys.exit(1)
        print(f"\n[1/3] Skipping parse, loading {structure_file}")
        with open(structure_file) as f:
            tree = json.load(f)
    else:
        # Parse PDF
        tree = parse_pdf(args.pdf_path, args.model)
        os.makedirs(output_dir, exist_ok=True)
        with open(structure_file, "w", encoding="utf-8") as f:
            json.dump(tree, f, indent=2)
        print(f"       Saved to {structure_file}")

    # Flatten and insert
    rows = flatten(tree)
    insert_to_db(rows)

    print(f"\nDone! Document '{tree['doc_name']}' is searchable.")


if __name__ == "__main__":
    main()
