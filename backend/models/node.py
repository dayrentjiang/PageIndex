from pydantic import BaseModel


class NodeResult(BaseModel):
    node_id: str
    doc_name: str
    title: str
    summary: str
    text: str
    start_page: int | None
    end_page: int | None
    parent_node_id: str | None
    depth: int
    rank: float


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[NodeResult]
