from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import get_db
from models import ResearchQuestion, Paper
from schemas import ReportResponse
from services.report_service import ReportService
import os

router = APIRouter()
report_service = ReportService()

@router.get("/generate-report", response_model=ReportResponse)
async def generate_report(
    question_id: str = Query(..., description="Research question ID"),
    format: str = Query("csv", description="Report format: csv, xlsx, docx, or pdf"),
    min_score: float = Query(0.0, description="Minimum score filter for papers"),
    include_all: bool = Query(False, description="Include all papers regardless of extraction status"),
    db: Session = Depends(get_db)
):
    """
    Generate a downloadable report in CSV, XLSX, DOCX, or PDF format
    """
    try:
        # Get research question
        research_question = db.query(ResearchQuestion).filter(
            ResearchQuestion.id == question_id
        ).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Get papers based on filters
        query = db.query(Paper).filter(Paper.question_id == question_id)
        
        if min_score > 0:
            query = query.filter(Paper.score >= min_score)
        
        if not include_all:
            # Only include papers with either screening or extraction data
            query = query.filter(
                (Paper.screening_json.isnot(None)) | (Paper.extracted_data.isnot(None))
            )
        
        papers = query.order_by(Paper.score.desc()).all()
        
        if not papers:
            raise HTTPException(status_code=404, detail="No papers found matching criteria")
        
        # Prepare question data
        question_data = {
            'id': research_question.id,
            'original_text': research_question.original_text,
            'rephrased_text': research_question.rephrased_text,
            'pico_json': research_question.pico_json or {}
        }
        
        # Prepare papers data
        papers_data = []
        for paper in papers:
            paper_data = {
                'pmid': paper.pmid,
                'title': paper.title,
                'authors': paper.authors,
                'publication_date': paper.publication_date,
                'doi': paper.doi,
                'abstract': paper.abstract,
                'pdf_link': paper.pdf_link,
                'mesh_terms': paper.mesh_terms,
                'score': paper.score,
                'screening_json': paper.screening_json,
                'extracted_data': paper.extracted_data
            }
            papers_data.append(paper_data)
        
        # Generate report based on format
        format_lower = format.lower()
        if format_lower == 'xlsx':
            filename = report_service.generate_excel_report(question_data, papers_data)
        elif format_lower == 'docx':
            filename = report_service.generate_word_report(question_data, papers_data)
        elif format_lower == 'pdf':
            filename = report_service.generate_pdf_report(question_data, papers_data)
        else:  # Default to CSV
            filename = report_service.generate_csv_report(question_data, papers_data)
        
        # Return URL (in a real deployment, this would be a proper URL)
        report_url = f"/api/download-report/{filename}"
        
        return ReportResponse(report_url=report_url)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

@router.get("/download-report/{filename}")
async def download_report(filename: str):
    """
    Download a generated report file
    """
    try:
        filepath = report_service.get_report_path(filename)
        
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Report file not found")
        
        # Determine media type based on file extension
        if filename.endswith('.csv'):
            media_type = "text/csv"
        elif filename.endswith('.xlsx'):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif filename.endswith('.docx'):
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        elif filename.endswith('.pdf'):
            media_type = "application/pdf"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")

@router.get("/reports")
async def list_reports():
    """
    List all generated reports
    """
    try:
        reports = report_service.list_reports()
        return {"reports": reports}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")

@router.delete("/reports/{filename}")
async def delete_report(filename: str):
    """
    Delete a report file
    """
    try:
        success = report_service.delete_report(filename)
        if success:
            return {"message": f"Report {filename} deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Report file not found")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")

@router.get("/report-preview/{question_id}")
async def preview_report_data(
    question_id: str,
    min_score: float = Query(0.0, description="Minimum score filter"),
    limit: int = Query(10, description="Number of papers to preview"),
    db: Session = Depends(get_db)
):
    """
    Preview report data before generating the actual report
    """
    try:
        # Get research question
        research_question = db.query(ResearchQuestion).filter(
            ResearchQuestion.id == question_id
        ).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Get papers for preview
        query = db.query(Paper).filter(Paper.question_id == question_id)
        
        if min_score > 0:
            query = query.filter(Paper.score >= min_score)
        
        papers = query.order_by(Paper.score.desc()).limit(limit).all()
        
        # Count totals
        total_papers = db.query(Paper).filter(Paper.question_id == question_id).count()
        screened_papers = db.query(Paper).filter(
            Paper.question_id == question_id,
            Paper.screening_json.isnot(None)
        ).count()
        extracted_papers = db.query(Paper).filter(
            Paper.question_id == question_id,
            Paper.extracted_data.isnot(None)
        ).count()
        
        # Format preview data
        preview_data = []
        for paper in papers:
            data = {
                'pmid': paper.pmid,
                'title': paper.title[:100] + '...' if paper.title and len(paper.title) > 100 else paper.title,
                'score': paper.score,
                'has_screening': paper.screening_json is not None,
                'has_extraction': paper.extracted_data is not None,
                'publication_date': paper.publication_date
            }
            preview_data.append(data)
        
        return {
            'question': {
                'id': research_question.id,
                'original_text': research_question.original_text,
                'rephrased_text': research_question.rephrased_text
            },
            'statistics': {
                'total_papers': total_papers,
                'screened_papers': screened_papers,
                'extracted_papers': extracted_papers,
                'papers_above_threshold': len([p for p in papers if p.score >= min_score])
            },
            'preview_data': preview_data,
            'filters': {
                'min_score': min_score,
                'preview_limit': limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating report preview: {str(e)}")