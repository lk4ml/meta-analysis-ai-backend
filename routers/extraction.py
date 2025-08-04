from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Paper
from schemas import DataExtractionRequest, DataExtractionResponse, ExtractedData, FilteredPaperResponse
from services.ai_service import AIService
from typing import List

router = APIRouter()
ai_service = AIService()

@router.get("/filtered-papers", response_model=List[FilteredPaperResponse])
async def get_filtered_papers(
    question_id: str = Query(..., description="Research question ID"),
    min_score: float = Query(4.0, description="Minimum score threshold"),
    db: Session = Depends(get_db)
):
    """
    Retrieve filtered papers above scoring threshold
    """
    try:
        # Get papers with scores above threshold
        papers = db.query(Paper).filter(
            Paper.question_id == question_id,
            Paper.score >= min_score,
            Paper.screening_json.isnot(None)
        ).order_by(Paper.score.desc()).all()
        
        if not papers:
            return []
        
        # Convert to response format
        filtered_papers = []
        for paper in papers:
            filtered_paper = FilteredPaperResponse(
                pmid=paper.pmid,
                score=paper.score,
                title=paper.title,
                abstract=paper.abstract,
                pdf_link=paper.pdf_link
            )
            filtered_papers.append(filtered_paper)
        
        return filtered_papers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving filtered papers: {str(e)}")

@router.post("/extract-data", response_model=DataExtractionResponse)
async def extract_data_from_papers(
    request: DataExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract structured meta-analysis data from selected papers
    """
    try:
        # Get papers by PMIDs
        papers = db.query(Paper).filter(Paper.pmid.in_(request.paper_ids)).all()
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found with provided IDs")
        
        # Prepare papers data for AI extraction
        papers_data = []
        for paper in papers:
            paper_data = {
                'pmid': paper.pmid,
                'title': paper.title,
                'abstract': paper.abstract,
                'authors': paper.authors,
                'publication_date': paper.publication_date
            }
            papers_data.append(paper_data)
        
        # Extract data using AI service
        extracted_results = ai_service.extract_data(papers_data)
        
        # Store extracted data in database
        for result in extracted_results:
            paper = db.query(Paper).filter(Paper.pmid == result['pmid']).first()
            if paper:
                paper.extracted_data = {
                    'study_design': result.get('study_design'),
                    'patient_characteristics': result.get('patient_characteristics'),
                    'treatment_characteristics': result.get('treatment_characteristics'),
                    'intervention': result.get('intervention'),
                    'comparison': result.get('comparison'),
                    'outcomes': result.get('outcomes')
                }
        
        db.commit()
        
        # Convert to response format
        extracted_data_list = []
        for result in extracted_results:
            extracted_data = ExtractedData(
                pmid=result['pmid'],
                study_design=result.get('study_design'),
                patient_characteristics=result.get('patient_characteristics'),
                treatment_characteristics=result.get('treatment_characteristics'),
                intervention=result.get('intervention'),
                comparison=result.get('comparison'),
                outcomes=result.get('outcomes')
            )
            extracted_data_list.append(extracted_data)
        
        return DataExtractionResponse(extracted_data=extracted_data_list)
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error extracting data: {str(e)}")

@router.get("/extracted-data/{question_id}")
async def get_extracted_data(
    question_id: str,
    min_score: float = Query(0.0, description="Minimum score filter"),
    db: Session = Depends(get_db)
):
    """
    Get all extracted data for a research question
    """
    try:
        # Get papers with extracted data
        query = db.query(Paper).filter(
            Paper.question_id == question_id,
            Paper.extracted_data.isnot(None)
        )
        
        if min_score > 0:
            query = query.filter(Paper.score >= min_score)
        
        papers = query.order_by(Paper.score.desc()).all()
        
        if not papers:
            return {"message": "No extracted data found", "data": []}
        
        # Format extracted data
        extracted_data_list = []
        for paper in papers:
            extracted_data = paper.extracted_data or {}
            data_entry = {
                "pmid": paper.pmid,
                "title": paper.title,
                "score": paper.score,
                "extracted_data": {
                    "study_design": extracted_data.get('study_design'),
                    "patient_characteristics": extracted_data.get('patient_characteristics'),
                    "treatment_characteristics": extracted_data.get('treatment_characteristics'),
                    "intervention": extracted_data.get('intervention'),
                    "comparison": extracted_data.get('comparison'),
                    "outcomes": extracted_data.get('outcomes')
                }
            }
            extracted_data_list.append(data_entry)
        
        return {
            "question_id": question_id,
            "total_papers": len(extracted_data_list),
            "min_score_filter": min_score,
            "data": extracted_data_list
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving extracted data: {str(e)}")

@router.delete("/extracted-data/{pmid}")
async def delete_extracted_data(pmid: str, db: Session = Depends(get_db)):
    """
    Delete extracted data for a specific paper
    """
    try:
        paper = db.query(Paper).filter(Paper.pmid == pmid).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        paper.extracted_data = None
        db.commit()
        
        return {"message": f"Extracted data deleted for paper {pmid}"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting extracted data: {str(e)}")