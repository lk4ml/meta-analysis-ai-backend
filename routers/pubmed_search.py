from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import ResearchQuestion, Paper
from schemas import PubMedSearchResponse, PaperResponse
from services.pubmed_service import PubMedService
from typing import Optional

router = APIRouter()
pubmed_service = PubMedService()

@router.get("/pubmed-search", response_model=PubMedSearchResponse)
async def search_pubmed(
    question_id: str = Query(..., description="Research question ID"),
    max_results: int = Query(100, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Convert rephrased question into MeSH terms and retrieve PubMed search results
    """
    try:
        # Get research question from database
        research_question = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Use rephrased question for search
        search_query = research_question.rephrased_text or research_question.original_text
        
        # Search PubMed
        query_translation, pmids, total_count = pubmed_service.search_papers(search_query, max_results)
        
        # Fetch paper details
        papers_data = pubmed_service.fetch_paper_details(pmids)
        
        # Store papers in database
        stored_papers = []
        for paper_data in papers_data:
            # Check if paper already exists for this question
            existing_paper = db.query(Paper).filter(
                Paper.question_id == question_id,
                Paper.pmid == paper_data['pmid']
            ).first()
            
            if not existing_paper:
                paper = Paper(
                    question_id=question_id,
                    pmid=paper_data['pmid'],
                    title=paper_data.get('title'),
                    abstract=paper_data.get('abstract'),
                    authors=paper_data.get('authors'),
                    publication_date=paper_data.get('publication_date'),
                    doi=paper_data.get('doi'),
                    mesh_terms=paper_data.get('mesh_terms', []),
                    pdf_link=paper_data.get('pdf_link')
                )
                db.add(paper)
                stored_papers.append(paper)
            else:
                stored_papers.append(existing_paper)
        
        db.commit()
        
        # Convert to response format
        paper_responses = []
        for paper in stored_papers:
            paper_response = PaperResponse(
                pmid=paper.pmid,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                publication_date=paper.publication_date,
                doi=paper.doi,
                mesh_terms=paper.mesh_terms if isinstance(paper.mesh_terms, list) else [],
                pdf_link=paper.pdf_link
            )
            paper_responses.append(paper_response)
        
        return PubMedSearchResponse(
            papers=paper_responses,
            total_count=total_count,
            query_translation=query_translation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error searching PubMed: {str(e)}")

@router.get("/pubmed-search/{question_id}/papers")
async def get_papers_for_question(
    question_id: str,
    skip: int = Query(0, description="Number of papers to skip"),
    limit: int = Query(50, description="Number of papers to return"),
    db: Session = Depends(get_db)
):
    """
    Get paginated papers for a specific research question
    """
    try:
        # Verify research question exists
        research_question = db.query(ResearchQuestion).filter(ResearchQuestion.id == question_id).first()
        if not research_question:
            raise HTTPException(status_code=404, detail="Research question not found")
        
        # Get papers with pagination
        papers = db.query(Paper).filter(Paper.question_id == question_id).offset(skip).limit(limit).all()
        
        # Get total count
        total_count = db.query(Paper).filter(Paper.question_id == question_id).count()
        
        # Convert to response format
        paper_responses = []
        for paper in papers:
            paper_response = PaperResponse(
                pmid=paper.pmid,
                title=paper.title,
                abstract=paper.abstract,
                authors=paper.authors,
                publication_date=paper.publication_date,
                doi=paper.doi,
                mesh_terms=paper.mesh_terms if isinstance(paper.mesh_terms, list) else [],
                pdf_link=paper.pdf_link
            )
            paper_responses.append(paper_response)
        
        return {
            "papers": paper_responses,
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving papers: {str(e)}")