"""
Load flattened structure JSON into PostgreSQL with FTS index.

Usage:
    python scripts/load_to_db.py results/Blood-Donation-2024_structure_flat.json
"""

import json
import sys
from pathlib import Path

import psycopg2

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "pageindex",
    "user": "pageindex",
    "password": "pageindex",
}

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS nodes (
    id SERIAL PRIMARY KEY,
    node_id TEXT NOT NULL,
    doc_name TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    text TEXT NOT NULL DEFAULT '',
    start_page INTEGER,
    end_page INTEGER,
    parent_node_id TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    fts_vector TSVECTOR GENERATED ALWAYS AS (
        setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
        setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
        setweight(to_tsvector('english', coalesce(text, '')), 'C')
    ) STORED,
    UNIQUE(doc_name, node_id)
);

CREATE INDEX IF NOT EXISTS idx_nodes_fts ON nodes USING GIN (fts_vector);
CREATE INDEX IF NOT EXISTS idx_nodes_doc_name ON nodes (doc_name);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes (parent_node_id);
"""

INSERT_SQL = """
INSERT INTO nodes (node_id, doc_name, title, summary, text, start_page, end_page, parent_node_id, depth)
VALUES (%(node_id)s, %(doc_name)s, %(title)s, %(summary)s, %(text)s, %(start_page)s, %(end_page)s, %(parent_node_id)s, %(depth)s)
ON CONFLICT (doc_name, node_id) DO UPDATE SET
    title = EXCLUDED.title,
    summary = EXCLUDED.summary,
    text = EXCLUDED.text,
    start_page = EXCLUDED.start_page,
    end_page = EXCLUDED.end_page,
    parent_node_id = EXCLUDED.parent_node_id,
    depth = EXCLUDED.depth;
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/load_to_db.py <flat.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    with open(input_path) as f:
        rows = json.load(f)

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create table and indexes
    cur.execute(CREATE_TABLE)
    conn.commit()

    # Insert rows
    for row in rows:
        cur.execute(INSERT_SQL, row)
    conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM nodes")
    count = cur.fetchone()[0]
    print(f"Loaded {len(rows)} nodes into database (total rows: {count})")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
