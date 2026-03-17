import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.search import router as search_router

app = FastAPI(title="PageIndex Search API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)

# Serve PDFs from data/ folder
data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(data_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=data_dir), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}
