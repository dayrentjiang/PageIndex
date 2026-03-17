from fastapi import APIRouter, Query

from backend.models.node import SearchResponse
from backend.services.search_service import search_nodes, get_all_nodes

router = APIRouter()


@router.get("/api/search", response_model=SearchResponse)
def search(q: str = Query(..., min_length=1, description="Search query"), limit: int = Query(10, ge=1, le=50)):
    results = search_nodes(query=q, limit=limit)
    return SearchResponse(query=q, total=len(results), results=results)


@router.get("/api/nodes")
def list_nodes():
    nodes = get_all_nodes()
    return {"total": len(nodes), "nodes": nodes}
