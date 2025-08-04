from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ResearchQuestion
from schemas import ResearchQuestionRequest, ResearchQuestionResponse
from services.ai_service import AIService
import uuid

router = APIRouter()
ai_service = AIService()

@router.post("/research-question", response_model=ResearchQuestionResponse)
async def create_research_question(
    request: ResearchQuestionRequest,
    use_ai_rephrasing: bool = False,  # Default to False to avoid restrictive terms
    db: Session = Depends(get_db)
):
    """
    Capture user research question and PICO criteria, then rephrase using AI
    """
    try:
        # Use AI service to rephrase the question only if requested
        pico_dict = request.pico.dict() if request.pico else None
        
        if use_ai_rephrasing:
            ai_result = ai_service.rephrase_research_question(request.question, pico_dict)
        else:
            # Use original question without AI rephrasing to avoid restrictive terms
            ai_result = {
                "rephrased_question": request.question,
                "pico_suggestions": pico_dict,
                "mesh_terms": []
            }
        
        # Create new research question record
        question_id = str(uuid.uuid4())
        research_question = ResearchQuestion(
            id=question_id,
            original_text=request.question,
            rephrased_text=ai_result["rephrased_question"],
            pico_json=ai_result.get("pico_suggestions", pico_dict)
        )
        
        db.add(research_question)
        db.commit()
        db.refresh(research_question)
        
        return ResearchQuestionResponse(
            question_id=question_id,
            rephrased_question=ai_result["rephrased_question"],
            original_question=request.question,
            pico_suggestions=ai_result.get("pico_suggestions")
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing research question: {str(e)}")

@router.get("/research-question/{question_id}")
async def get_research_question(question_id: str, db: Session = Depends(get_db)):
    """
    Get research question by ID
    """
    question = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Research question not found")
    
    return {
        "question_id": question.id,
        "original_text": question.original_text,
        "rephrased_text": question.rephrased_text,
        "pico_json": question.pico_json,
        "created_at": question.created_at
    }