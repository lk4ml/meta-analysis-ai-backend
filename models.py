from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

Base = declarative_base()

class ResearchQuestion(Base):
    __tablename__ = "research_questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # Optional for now
    original_text = Column(Text, nullable=False)
    rephrased_text = Column(Text, nullable=True)
    pico_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    papers = relationship("Paper", back_populates="research_question")

class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question_id = Column(String, ForeignKey("research_questions.id"), nullable=False)
    pmid = Column(String, nullable=False)
    title = Column(Text, nullable=True)
    abstract = Column(Text, nullable=True)
    authors = Column(Text, nullable=True)
    publication_date = Column(String, nullable=True)
    doi = Column(String, nullable=True)
    mesh_terms = Column(JSON, nullable=True)  # Store as JSON array
    pdf_link = Column(String, nullable=True)
    screening_json = Column(JSON, nullable=True)
    score = Column(Float, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    research_question = relationship("ResearchQuestion", back_populates="papers")