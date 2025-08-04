from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PICOCriteria(BaseModel):
    population: Optional[str] = None
    intervention: Optional[str] = None
    comparison: Optional[str] = None
    outcome: Optional[str] = None

class ResearchQuestionRequest(BaseModel):
    question: str = Field(..., description="The research question")
    pico: Optional[PICOCriteria] = None

class ResearchQuestionResponse(BaseModel):
    question_id: str
    rephrased_question: str
    original_question: str
    pico_suggestions: Optional[Dict[str, Any]] = None

class PaperBase(BaseModel):
    pmid: str
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: Optional[str] = None
    publication_date: Optional[str] = None
    doi: Optional[str] = None
    mesh_terms: Optional[List[str]] = None
    pdf_link: Optional[str] = None

class PaperResponse(PaperBase):
    pass

class PubMedSearchResponse(BaseModel):
    papers: List[PaperResponse]
    total_count: int
    query_translation: str

class ScreeningRequest(BaseModel):
    question_id: str
    papers: List[Dict[str, Any]]

class ScreenedPaper(BaseModel):
    pmid: str
    study_design: str
    intervention: str
    population: str
    outcomes: str
    treatment_characteristics: str
    score: float

class ScreeningResponse(BaseModel):
    screened_papers: List[ScreenedPaper]

class FilteredPaperResponse(BaseModel):
    pmid: str
    score: float
    title: Optional[str] = None
    abstract: Optional[str] = None
    pdf_link: Optional[str] = None

class DataExtractionRequest(BaseModel):
    paper_ids: List[str]

class ExtractedData(BaseModel):
    pmid: str
    study_design: Optional[str] = None
    patient_characteristics: Optional[str] = None
    treatment_characteristics: Optional[str] = None
    intervention: Optional[str] = None
    comparison: Optional[str] = None
    outcomes: Optional[str] = None

class DataExtractionResponse(BaseModel):
    extracted_data: List[ExtractedData]

class ReportResponse(BaseModel):
    report_url: str