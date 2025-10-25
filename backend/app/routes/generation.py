from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.models.models import User, Trial, GeneratedContent
from app.models.schemas import GeneratedContentResponse
from app.routes.auth import get_current_user
from app.utils.file_utils import extract_text_from_pdf, get_file_extension

# Import AI agents
from app.agents import distill_agent, infographic_agent, video_agent

router = APIRouter(prefix="/api/generate", tags=["generation"])


@router.post("/summary/{trial_id}", response_model=GeneratedContentResponse)
async def generate_summary(
    trial_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a summary from the trial protocol.
    
    This endpoint:
    1. Retrieves the trial and protocol text
    2. Calls the distill_agent to extract structured information
    3. Saves the result to the database
    
    TODO: For production, consider making this async with Celery or similar
    """
    
    # Get trial
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    if not trial.protocol_file_path:
        raise HTTPException(status_code=400, detail="No protocol file uploaded")
    
    try:
        # Extract protocol text
        file_ext = get_file_extension(trial.protocol_file_path)
        
        if file_ext == 'pdf':
            protocol_text = extract_text_from_pdf(trial.protocol_file_path)
        elif file_ext == 'txt':
            with open(trial.protocol_file_path, 'r') as f:
                protocol_text = f.read()
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Update trial status
        trial.status = "processing"
        db.commit()
        
        # ===== CALL DISTILL AGENT =====
        # This is where the AI magic happens!
        agent_input = {
            "protocol_text": protocol_text,
            "trial_id": trial_id
        }
        
        extracted_data = distill_agent.run_agent(agent_input)
        
        # Generate patient-friendly text
        simple_text = distill_agent.simplify_for_patients(extracted_data)
        
        # Save to database
        import json
        
        # Store both structured data and simple text
        content_text = json.dumps({
            "structured_data": extracted_data,
            "simple_summary": simple_text
        })
        
        # Check if summary already exists
        existing_content = db.query(GeneratedContent).filter(
            GeneratedContent.trial_id == trial_id,
            GeneratedContent.content_type == "summary"
        ).first()
        
        if existing_content:
            # Update existing
            existing_content.content_text = content_text
            existing_content.version += 1
            generated_content = existing_content
        else:
            # Create new
            generated_content = GeneratedContent(
                trial_id=trial_id,
                content_type="summary",
                content_text=content_text
            )
            db.add(generated_content)
        
        trial.status = "completed"
        db.commit()
        db.refresh(generated_content)
        
        return generated_content
    
    except Exception as e:
        trial.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")


@router.post("/infographic/{trial_id}", response_model=GeneratedContentResponse)
async def generate_infographic(
    trial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an infographic from trial summary data.
    
    Requires that a summary has already been generated.
    """
    
    # Get trial
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Get existing summary
    summary_content = db.query(GeneratedContent).filter(
        GeneratedContent.trial_id == trial_id,
        GeneratedContent.content_type == "summary"
    ).first()
    
    if not summary_content:
        raise HTTPException(
            status_code=400,
            detail="Please generate a summary first"
        )
    
    try:
        import json
        summary_data = json.loads(summary_content.content_text)
        trial_data = summary_data.get("structured_data", {})
        
        # ===== CALL INFOGRAPHIC AGENT =====
        agent_input = {
            "trial_data": trial_data,
            "trial_id": trial_id,
            "style": "modern"
        }
        
        result = infographic_agent.run_agent(agent_input)
        
        # Save to database
        existing_content = db.query(GeneratedContent).filter(
            GeneratedContent.trial_id == trial_id,
            GeneratedContent.content_type == "infographic"
        ).first()
        
        if existing_content:
            existing_content.file_path = result.get("file_path")
            existing_content.version += 1
            generated_content = existing_content
        else:
            generated_content = GeneratedContent(
                trial_id=trial_id,
                content_type="infographic",
                file_path=result.get("file_path"),
                content_text=json.dumps(result)
            )
            db.add(generated_content)
        
        db.commit()
        db.refresh(generated_content)
        
        return generated_content
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating infographic: {str(e)}")


@router.post("/video/{trial_id}", response_model=GeneratedContentResponse)
async def generate_video(
    trial_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an educational video from trial summary data.
    
    Requires that a summary has already been generated.
    """
    
    # Get trial
    trial = db.query(Trial).filter(
        Trial.id == trial_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not trial:
        raise HTTPException(status_code=404, detail="Trial not found")
    
    # Get existing summary
    summary_content = db.query(GeneratedContent).filter(
        GeneratedContent.trial_id == trial_id,
        GeneratedContent.content_type == "summary"
    ).first()
    
    if not summary_content:
        raise HTTPException(
            status_code=400,
            detail="Please generate a summary first"
        )
    
    try:
        import json
        summary_data = json.loads(summary_content.content_text)
        trial_data = summary_data.get("structured_data", {})
        simple_text = summary_data.get("simple_summary", "")
        
        # ===== CALL VIDEO AGENT =====
        agent_input = {
            "trial_data": trial_data,
            "simple_text": simple_text,
            "trial_id": trial_id,
            "duration": 90  # 90 second video
        }
        
        result = video_agent.run_agent(agent_input)
        
        # Save to database
        existing_content = db.query(GeneratedContent).filter(
            GeneratedContent.trial_id == trial_id,
            GeneratedContent.content_type == "video"
        ).first()
        
        result_json = json.dumps(result)
        
        if existing_content:
            existing_content.file_path = result.get("file_path")
            existing_content.content_text = result_json
            existing_content.version += 1
            generated_content = existing_content
        else:
            generated_content = GeneratedContent(
                trial_id=trial_id,
                content_type="video",
                file_path=result.get("file_path"),
                content_text=result_json
            )
            db.add(generated_content)
        
        db.commit()
        db.refresh(generated_content)
        
        return generated_content
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating video: {str(e)}")


@router.get("/content/{content_id}/data")
async def get_content_data(
    content_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the detailed data for generated content.
    Useful for displaying summaries, video scripts, etc.
    """
    
    content = db.query(GeneratedContent).join(Trial).filter(
        GeneratedContent.id == content_id,
        Trial.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    import json
    
    response = {
        "id": content.id,
        "trial_id": content.trial_id,
        "content_type": content.content_type,
        "version": content.version,
        "is_approved": content.is_approved
    }
    
    # Parse JSON content if available
    if content.content_text:
        try:
            response["data"] = json.loads(content.content_text)
        except:
            response["data"] = {"text": content.content_text}
    
    if content.file_path:
        response["file_path"] = content.file_path
    
    if content.file_url:
        response["file_url"] = content.file_url
    
    return response
