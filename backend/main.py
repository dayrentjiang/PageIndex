from fastapi import FastAPI

from backend.routes.search import router as search_router

app = FastAPI(title="PageIndex Search API")

app.include_router(search_router)


@app.get("/health")
def health():
    return {"status": "ok"}
