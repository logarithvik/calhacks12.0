from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os

from app.database import get_db
from app.models.models import User, Trial
from app.models.schemas import TrialCreate, TrialResponse, TrialWithContent
from app.routes.auth import get_current_user
from app.utils.file_utils import save_upload_file, extract_text_from_pdf, get_file_extension
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/trials", tags=["trials"])


@router.get("/", response_model=List[TrialWithContent])
async def get_trials(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all trials for the current user"""
    trials = db.query(Trial).filter(Trial.user_id == current_user.id).all()
    return trials


@router.get("/{trial_id}", response_model=TrialWithContent)
async def get_trial(
    trial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific trial by ID"""
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    return trial


@router.post("/", response_model=TrialResponse)
async def create_trial(
    title: str = Form(...),
    protocol_file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new trial and upload protocol file.
    
    This endpoint:
    1. Creates a trial record
    2. Saves the uploaded PDF
    3. Returns trial info (processing happens in background via agent endpoints)
    """
    
    # Validate file if provided
    file_path = None
    original_filename = None
    
    if protocol_file:
        # Check file extension
        file_ext = get_file_extension(protocol_file.filename)
        if file_ext not in ['pdf', 'txt']:
            raise HTTPException(
                status_code=400,
                detail="Only PDF and TXT files are supported"
            )
        
        # Save file
        original_filename = protocol_file.filename
        file_path = os.path.join(
            settings.upload_dir,
            f"trial_{current_user.id}_{protocol_file.filename}"
        )
        await save_upload_file(protocol_file, file_path)
    
    # Create trial record
    new_trial = Trial(
        title=title,
        protocol_file_path=file_path,
        original_filename=original_filename,
        status="uploaded",
        user_id=current_user.id
    )
    
    db.add(new_trial)
    db.commit()
    db.refresh(new_trial)
    
    return new_trial


@router.delete("/{trial_id}")
async def delete_trial(
    trial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a trial"""
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Delete associated file if exists
    if trial.protocol_file_path and os.path.exists(trial.protocol_file_path):
        os.remove(trial.protocol_file_path)
    
    db.delete(trial)
    db.commit()
    
    return {"message": "Trial deleted successfully"}


@router.get("/{trial_id}/protocol-text")
async def get_protocol_text(
    trial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract and return the raw text from the protocol file"""
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    if not trial.protocol_file_path or not os.path.exists(trial.protocol_file_path):
        raise HTTPException(status_code=404, detail="Protocol file not found")
    
    try:
        # Extract text based on file type
        file_ext = get_file_extension(trial.protocol_file_path)
        
        if file_ext == 'pdf':
            text = extract_text_from_pdf(trial.protocol_file_path)
        elif file_ext == 'txt':
            with open(trial.protocol_file_path, 'r') as f:
                text = f.read()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        return {
            "trial_id": trial_id,
            "text": text,
            "filename": trial.original_filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")
