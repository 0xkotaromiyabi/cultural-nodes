"""Curation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import shutil
import tempfile
from datetime import datetime

from app.core.auth import get_current_user, require_curator, User
from app.core.knowledge_store import get_knowledge_store, KnowledgeStore
from app.ingestion.pipeline import get_pipeline

router = APIRouter(prefix="/api/curation", tags=["Curation"])

# --- Models ---

class SubmissionCreate(BaseModel):
    title: str
    source_type: str = Field(..., description="community/academic/media/archival")
    content: Optional[str] = None
    raw_url: Optional[str] = None
    category: str = "general"

class SubmissionResponse(BaseModel):
    id: int
    title: str
    source_type: str
    status: str
    submitted_by: str
    created_at: str

class CuratorAction(BaseModel):
    note: Optional[str] = None

# --- Helpers ---

def get_store() -> KnowledgeStore:
    return get_knowledge_store()

# --- Endpoints ---

@router.post("/submit", response_model=SubmissionResponse)
async def submit_knowledge(
    submission: SubmissionCreate,
    user: User = Depends(get_current_user),
    store: KnowledgeStore = Depends(get_store)
):
    """Submit knowledge (text/url) for curation."""
    
    # Validate input
    if not submission.content and not submission.raw_url:
        raise HTTPException(status_code=400, detail="Either content or raw_url is required")
    
    data = submission.dict()
    data["submitted_by"] = user.id
    
    submission_id = store.add_submission(data)
    
    # Return response (fetch back to get dates)
    saved = store.get_submission_by_id(submission_id)
    return SubmissionResponse(**saved)

@router.post("/submit/file", response_model=SubmissionResponse)
async def submit_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    source_type: str = Form(...),
    category: str = Form("general"),
    user: User = Depends(get_current_user),
    store: KnowledgeStore = Depends(get_store)
):
    """Submit file for curation."""
    
    # Validate file type
    allowed_extensions = [".pdf", ".md", ".markdown", ".txt"]
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Allowed: {allowed_extensions}")

    # Save to temp/staging area
    staging_dir = "./knowledge_base/staging"
    os.makedirs(staging_dir, exist_ok=True)
    
    # Create unique filename to avoid collisions in staging
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(staging_dir, safe_filename)
    
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
        
    data = {
        "title": title,
        "source_type": source_type,
        "filename": file.filename,
        "file_path": file_path,
        "category": category,
        "submitted_by": user.id
    }
    
    submission_id = store.add_submission(data)
    saved = store.get_submission_by_id(submission_id)
    return SubmissionResponse(**saved)

@router.get("/submissions", response_model=List[SubmissionResponse])
async def list_submissions(
    status: Optional[str] = None,
    user: User = Depends(require_curator),
    store: KnowledgeStore = Depends(get_store)
):
    """List submissions (Curator only)."""
    submissions = store.get_submissions(status=status)
    return [SubmissionResponse(**s) for s in submissions]

@router.post("/submissions/{id}/approve")
async def approve_submission(
    id: int,
    action: CuratorAction,
    background_tasks: BackgroundTasks,
    user: User = Depends(require_curator),
    store: KnowledgeStore = Depends(get_store)
):
    """Approve submission and trigger ingestion."""
    
    submission = store.get_submission_by_id(id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    if submission["status"] != "pending":
        raise HTTPException(status_code=400, detail=f"Submission is already {submission['status']}")
    
    # Update status
    store.update_submission_status(id, "approved", user.id, action.note)
    
    # Trigger Ingestion
    background_tasks.add_task(process_ingestion, submission)
    
    return {"status": "approved", "message": "Submission approved and ingestion queued"}

@router.post("/submissions/{id}/reject")
async def reject_submission(
    id: int,
    action: CuratorAction,
    user: User = Depends(require_curator),
    store: KnowledgeStore = Depends(get_store)
):
    """Reject submission."""
    
    submission = store.get_submission_by_id(id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    store.update_submission_status(id, "rejected", user.id, action.note)
    
    # If it was a file, maybe clean up staging file? 
    # Keeping it for now for audit/later review if needed.
    
    return {"status": "rejected"}

# --- Background Task ---

def process_ingestion(submission: dict):
    """Background task to ingest approved content."""
    try:
        pipeline = get_pipeline(verbose=True)
        source_type = submission["source_type"]
        category = submission["category"]
        title = submission["title"]
        
        # Determine target directory
        if source_type in ["community", "academic", "media", "archival"]:
             target_dir = f"./knowledge_base/{source_type}"
             if source_type == "community":
                 target_dir += "/transcript" # Defaulting for now
        else:
             target_dir = "./knowledge_base/general"
             
        os.makedirs(target_dir, exist_ok=True)
        
        # 1. Handle File
        if submission.get("file_path"):
            src_path = submission["file_path"]
            filename = submission["filename"]
            dst_path = os.path.join(target_dir, filename)
            
            # Move from staging to permanent
            if os.path.exists(src_path):
                shutil.move(src_path, dst_path)
                pipeline.ingest_file(dst_path, category=category)
                print(f"[Ingest] File {filename} ingested successfully.")
            else:
                print(f"[Ingest] Error: Staging file missing for {submission['id']}")
                
        # 2. Handle Text
        elif submission.get("content"):
            filename = f"{title.replace(' ', '-').lower()}.txt"
            dst_path = os.path.join(target_dir, filename)
            
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(submission["content"])
                
            pipeline.ingest_file(dst_path, category=category)
            print(f"[Ingest] Text {title} ingested successfully.")
            
        # 3. Handle URL
        elif submission.get("raw_url"):
            pipeline.ingest_url(submission["raw_url"], category=category)
            print(f"[Ingest] URL {submission['raw_url']} ingested successfully.")
            
    except Exception as e:
        print(f"[Ingest] Failed to process submission {submission['id']}: {e}")
