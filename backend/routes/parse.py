import json
import os
import shutil
import subprocess
import sys

from fastapi import APIRouter, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Track parse jobs
jobs: dict[str, dict] = {}


class ParseStatus(BaseModel):
    job_id: str
    status: str  # "processing", "done", "error"
    message: str


def run_parse(job_id: str, pdf_path: str):
    """Run PageIndex parsing in background."""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["message"] = "Parsing PDF into tree structure..."

        result = subprocess.run(
            [
                sys.executable, "run_pageindex.py",
                "--pdf_path", pdf_path,
                "--if-add-node-text", "yes",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        if result.returncode != 0:
            jobs[job_id]["status"] = "error"
            jobs[job_id]["message"] = result.stderr or result.stdout
            return

        jobs[job_id]["status"] = "done"
        jobs[job_id]["message"] = "Tree structure created successfully"

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["message"] = str(e)


@router.post("/api/parse")
async def parse_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """Upload a PDF and start parsing it into a tree structure."""
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(status_code=400, content={"error": "Only PDF files are allowed"})

    os.makedirs(DATA_DIR, exist_ok=True)
    pdf_path = os.path.join(DATA_DIR, file.filename)

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    job_id = file.filename
    jobs[job_id] = {
        "status": "processing",
        "message": "Starting parse...",
    }

    background_tasks.add_task(run_parse, job_id, pdf_path)

    return {"job_id": job_id, "status": "processing", "message": "Parse started"}


@router.get("/api/parse/status/{job_id}")
async def get_parse_status(job_id: str):
    """Poll parse job status."""
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    return jobs[job_id] | {"job_id": job_id}


@router.get("/api/trees")
async def list_trees():
    """List all generated tree structures."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(RESULTS_DIR) if f.endswith("_structure.json")]
    trees = []
    for f in sorted(files):
        path = os.path.join(RESULTS_DIR, f)
        with open(path) as fp:
            data = json.load(fp)
        trees.append({
            "file": f,
            "doc_name": data.get("doc_name", f),
        })
    return {"trees": trees}


@router.get("/api/trees/{doc_name}")
async def get_tree(doc_name: str):
    """Get a specific tree structure by doc name."""
    # Try to find the matching file
    os.makedirs(RESULTS_DIR, exist_ok=True)
    for f in os.listdir(RESULTS_DIR):
        if f.endswith("_structure.json"):
            path = os.path.join(RESULTS_DIR, f)
            with open(path) as fp:
                data = json.load(fp)
            if data.get("doc_name") == doc_name or f == doc_name:
                return data

    return JSONResponse(status_code=404, content={"error": "Tree not found"})
