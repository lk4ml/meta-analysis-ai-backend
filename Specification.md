
# 📘 Backend Specification Document – Meta-Analysis AI App

### Version: 1.0  
### Author: Love Tyagi 
### Last Updated:  Aug 2, 2025

---

## 🧭 Overview

This application is designed to streamline the meta-analysis process for researchers by automating question intake, PubMed retrieval, AI-based paper screening, data extraction, and final report generation.

---

## 📐 Functional Scope

The application will support the following key backend functionalities:

1. Capture user-defined research question and PICO criteria  
2. Rephrase the question using AI for better specificity  
3. Retrieve relevant papers from PubMed using MeSH term expansion  
4. Screen papers using AI-generated criteria  
5. Score papers based on relevance  
6. Extract structured data from top papers  
7. Generate and export a final evidence report

---

## ⚙️ Architecture Overview

| Layer       | Technology |
|-------------|------------|
| Framework   | FastAPI, Python ( Backend )
| AI/LLM      | OpenAI, Claude, or open LLMs |
| Database    | PostgreSQL|
| Search API  | PubMed Entrez or E-Utilities |
| File Store  | local filesystem/postgres or memory |

---

## 🔗 API Endpoints Specification

### 1. `POST /research-question`
**Purpose**: Capture user research question and PICO criteria.

**Payload**
```json
{
  "question": "Does Pembrolizumab improve survival in elderly lung cancer patients?",
  "pico": {
    "population": "Elderly lung cancer patients",
    "intervention": "Pembrolizumab",
    "comparison": "Standard chemotherapy",
    "outcome": "Overall survival"
  }
}
```

**Response**
```json
{
  "rephrased_question": "...",
  "question_id": "uuid"
}
```

---

### 2. `GET /pubmed-search?question_id={uuid}`
**Purpose**: Converts rephrased question into MeSH terms and retrieves PubMed search results.

**Response**
```json
{
  "papers": [
    {
      "pmid": "12345678",
      "title": "...",
      "abstract": "...",
      "authors": "...",
      "publication_date": "...",
      "mesh_terms": [...],
      "pdf_link": "..."
    }
  ]
}
```

---

### 3. `POST /screening-columns`
**Purpose**: Generate AI-screening columns for each paper.

**Payload**
```json
{
  "question_id": "uuid",
  "papers": [
    { "pmid": "1234", "title": "...", "abstract": "..." }
  ]
}
```

**Response**
```json
{
  "screened_papers": [
    {
      "pmid": "1234",
      "study_design": "Yes",
      "intervention": "Yes",
      "population": "Yes",
      "outcomes": "Maybe",
      "treatment_characteristics": "No",
      "score": 3.5
    }
  ]
}
```

---

### 4. `GET /filtered-papers?min_score=4.0`
**Purpose**: Retrieve filtered papers above scoring threshold.

**Response**
```json
[
  {
    "pmid": "12345678",
    "score": 4.5,
    "title": "...",
    "abstract": "...",
    "pdf_link": "..."
  }
]
```

---

### 5. `POST /extract-data`
**Purpose**: Extract structured meta-analysis data from selected papers.

**Payload**
```json
{
  "paper_ids": ["12345678", "23456789"]
}
```

**Response**
```json
[
  {
    "pmid": "12345678",
    "study_design": "...",
    "patient_characteristics": "...",
    "treatment_characteristics": "...",
    "intervention": "...",
    "comparison": "...",
    "outcomes": "..."
  }
]
```

---

### 6. `GET /generate-report?question_id={uuid}`
**Purpose**: Generate a downloadable report in CSV or XLSX format.

**Response**
```json
{
  "report_url": "https://yourdomain.com/reports/xyz.csv"
}
```

---

## 🤖 AI & Processing Services

| Component                | Description |
|--------------------------|-------------|
| **Rephrasing Service**   | Uses LLM to rephrase user question with specificity using PICO, if user has provided , if user has not provided any PICO critiera Just generate few options suggesting patient specicifcty, outcomes specificity|
| **PubMed Retrieval Service** | Use pubemd api to transform final question into mesh terms and generate, queries PubMed, and retrieves papers with Paper id, title,abstract, authoers, dates, pubmed id |
| **Paper Screening Engine** | AI-based generation of six columns: Study Design, Intervention, Population, Outcomes, Treatment Characteristics, etc. |
|**AI Generated Column**| A service that allows user to generate AI based columns based upon user needs 
| **Scoring Engine**       | Computes total score based on Yes (1), Maybe (0.5), No (0) |
| **Data Extraction Engine** | Extracts structured meta-data from paper body/PDF or abstract based upon overall scoring threshold decided by user |
| **Report Builder**       | Aggregates final selected paper data into a CSV/XLSX file |

---

## 🗃️ Database Schema (Sample)

### Table: `research_questions`
| Field          | Type      |
|----------------|-----------|
| id             | UUID (PK) |
| user_id        | UUID      |
| original_text  | TEXT      |
| rephrased_text | TEXT      |
| pico_json      | JSONB     |
| created_at     | TIMESTAMP |

### Table: `papers`
| Field               | Type      |
|---------------------|-----------|
| id                  | UUID (PK) |
| question_id         | UUID (FK) |
| pmid                | TEXT      |
| title               | TEXT      |
| abstract            | TEXT      |
| mesh_terms          | TEXT[]    |
| pdf_link            | TEXT      |
| screening_json      | JSONB     |
| score               | FLOAT     |

---

## ✅ Backend Design Considerations

- Use modular services: LLM, PubMed, Scoring, Extraction
- Cache PubMed results with expiry
- Add retry and error handling for external API calls
- Store intermediate results for traceability
- Secure API with auth keys if user accounts are supported
- Use background jobs for PDF processing and report generation
- Well designed use cases that tests out all the services and apis
- Fully fucntional backend that can be used as a demo for tehcincal audience, like input question and generating next steps afterwords. 
---

## 📌 Future Features (Planned)

- PDF upload by users for non-PubMed papers  
- User authentication and history  
- Fine-tuned model for domain-specific screening  
- Visual analytics in reports (forest plots, charts)  
- Integration with Zotero, EndNote

