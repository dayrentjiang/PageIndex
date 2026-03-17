import psycopg2
import psycopg2.extras

from backend.config import DB_CONFIG
from backend.models.node import NodeResult

SEARCH_SQL = """
    SELECT
        node_id, doc_name, title, summary, text,
        start_page, end_page, parent_node_id, depth,
        ts_rank(fts_vector, query) AS rank
    FROM nodes, plainto_tsquery('english', %(query)s) query
    WHERE fts_vector @@ query
    ORDER BY rank DESC
    LIMIT %(limit)s;
"""


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def search_nodes(query: str, limit: int = 10) -> list[NodeResult]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cur.execute(SEARCH_SQL, {"query": query, "limit": limit})
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [NodeResult(**row) for row in rows]


ALL_NODES_SQL = """
    SELECT
        node_id, doc_name, title, summary, text,
        start_page, end_page, parent_node_id, depth,
        0.0 AS rank
    FROM nodes
    ORDER BY node_id;
"""


def get_all_nodes() -> list[NodeResult]:
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(ALL_NODES_SQL)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [NodeResult(**row) for row in rows]
