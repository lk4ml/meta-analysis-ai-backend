from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import ResearchQuestion, Paper
from schemas import ScreeningRequest, ScreeningResponse, ScreenedPaper
from services.ai_service import AIService
from typing import List, Dict, Any
import json

router = APIRouter()
ai_service = AIService()

@router.post("/screening-columns", response_model=ScreeningResponse)
async def screen_papers(
    request: ScreeningRequest,
    db: Session = Depends(get_db)
):
    """
    Generate AI-screening columns for each paper
    """
    try:
        # Get research question from database
        research_question = db.query(ResearchQuestion).filter(
            ResearchQuestion.id == request.question_id
        ).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Use the rephrased question for screening context
        screening_context = research_question.rephrased_text or research_question.original_text
        
        # Screen papers using AI service
        screened_results = ai_service.screen_papers(request.papers, screening_context)
        
        # Update papers in database with screening results
        for screening_result in screened_results:
            paper = db.query(Paper).filter(
                Paper.question_id == request.question_id,
                Paper.pmid == screening_result['pmid']
            ).first()
            
            if paper:
                # Store screening results and score
                paper.screening_json = {
                    "study_design": screening_result.get('study_design'),
                    "intervention": screening_result.get('intervention'),
                    "population": screening_result.get('population'),
                    "outcomes": screening_result.get('outcomes'),
                    "treatment_characteristics": screening_result.get('treatment_characteristics')
                }
                paper.score = screening_result.get('score', 0.0)
        
        db.commit()
        
        # Convert to response format
        screened_papers = []
        for result in screened_results:
            screened_paper = ScreenedPaper(
                pmid=result['pmid'],
                study_design=result.get('study_design', 'Maybe'),
                intervention=result.get('intervention', 'Maybe'),
                population=result.get('population', 'Maybe'),
                outcomes=result.get('outcomes', 'Maybe'),
                treatment_characteristics=result.get('treatment_characteristics', 'Maybe'),
                score=result.get('score', 0.0)
            )
            screened_papers.append(screened_paper)
        
        return ScreeningResponse(screened_papers=screened_papers)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error screening papers: {str(e)}")

@router.post("/custom-screening-column")
async def create_custom_screening_column(
    question_id: str,
    column_name: str,
    column_criteria: str,
    paper_ids: List[str] = None,
    db: Session = Depends(get_db)
):
    """
    Generate custom AI-based screening column based on user-defined criteria
    """
    try:
        # Get research question
        research_question = db.query(ResearchQuestion).filter(
            ResearchQuestion.id == question_id
        ).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Get papers to screen
        if paper_ids:
            papers = db.query(Paper).filter(
                Paper.question_id == question_id,
                Paper.pmid.in_(paper_ids)
            ).all()
        else:
            papers = db.query(Paper).filter(Paper.question_id == question_id).all()
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found")
        
        # Screen papers with custom criteria
        custom_results = []
        for paper in papers:
            try:
                # Create custom screening prompt
                prompt = f"""
                Based on the following criteria, evaluate this paper:
                
                Criteria: {column_criteria}
                
                Paper Details:
                Title: {paper.title or 'N/A'}
                Abstract: {(paper.abstract or 'N/A')[:1000]}...
                
                Please rate as "Yes", "Maybe", or "No" based on whether the paper meets the criteria.
                Only respond with one word: Yes, Maybe, or No.
                """
                
                # Use AI service (simplified version)
                if ai_service.openai_client:
                    response = ai_service.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=10,
                        temperature=0.1
                    )
                    ai_response = response.choices[0].message.content.strip().upper()
                elif ai_service.anthropic_client:
                    response = ai_service.anthropic_client.messages.create(
                        model="claude-3-sonnet-20240229",
                        max_tokens=10,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    ai_response = response.content[0].text.strip().upper()
                else:
                    ai_response = "MAYBE"  # Fallback
                
                # Ensure valid response
                if ai_response not in ["YES", "MAYBE", "NO"]:
                    ai_response = "MAYBE"
                
                custom_results.append({
                    "pmid": paper.pmid,
                    "title": paper.title,
                    column_name: ai_response
                })
                
            except Exception as e:
                print(f"Error screening paper {paper.pmid}: {e}")
                custom_results.append({
                    "pmid": paper.pmid,
                    "title": paper.title,
                    column_name: "MAYBE"
                })
        
        return {
            "column_name": column_name,
            "criteria": column_criteria,
            "results": custom_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating custom screening column: {str(e)}")

@router.get("/screening-results/{question_id}")
async def get_screening_results(
    question_id: str,
    min_score: float = 0.0,
    db: Session = Depends(get_db)
):
    """
    Get screening results for a research question with optional score filtering
    """
    try:
        # Verify research question exists
        research_question = db.query(ResearchQuestion).filter(
            ResearchQuestion.id == question_id
        ).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Get papers with screening results
        query = db.query(Paper).filter(
            Paper.question_id == question_id,
            Paper.screening_json.isnot(None)
        )
        
        if min_score > 0:
            query = query.filter(Paper.score >= min_score)
        
        papers = query.all()
        
        # Format results
        results = []
        for paper in papers:
            screening_data = paper.screening_json or {}
            result = {
                "pmid": paper.pmid,
                "title": paper.title,
                "score": paper.score,
                "screening": screening_data
            }
            results.append(result)
        
        return {
            "question_id": question_id,
            "total_screened": len(results),
            "min_score_filter": min_score,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving screening results: {str(e)}")