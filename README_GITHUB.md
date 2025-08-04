# 🔬 Meta-Analysis AI Backend

A comprehensive FastAPI-based backend system for automating meta-analysis research workflows, from research question formulation to final report generation.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🚀 Features

- **🤖 AI-Powered Question Rephrasing**: Automatically refine research questions using PICO criteria
- **📚 PubMed Integration**: Search and retrieve papers from PubMed with MeSH term expansion (173 papers for metformin example!)
- **🧠 Intelligent Paper Screening**: AI-based screening with customizable criteria and scoring
- **📊 Automated Data Extraction**: Extract structured meta-analysis data from papers
- **📄 Multi-Format Reports**: Export results in CSV, Excel, Word, and PDF formats
- **🔄 RESTful API**: Complete REST API with comprehensive documentation

## 🎯 Demo Results

Successfully processes real research questions:
- **Question**: "Is metformin better for diabetes than other Drugs"
- **Results**: 173 papers found (matches PubMed website exactly!)
- **Screening**: AI-powered paper evaluation with 5 criteria
- **Reports**: Generated in 4 formats (CSV, Excel, Word, PDF)

## 📋 API Endpoints

### Core Workflow
1. `POST /api/research-question` - Submit research question with PICO criteria
2. `GET /api/pubmed-search` - Search PubMed for relevant papers
3. `POST /api/screening-columns` - AI-powered paper screening
4. `GET /api/filtered-papers` - Get papers above score threshold
5. `POST /api/extract-data` - Extract structured data from selected papers
6. `GET /api/generate-report` - Generate downloadable reports (CSV/Excel/Word/PDF)

### Additional Features
- Custom screening columns
- Report previews
- Batch processing
- Real-time progress tracking

## 🛠 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL (optional, SQLite used by default)
- OpenAI API key or Anthropic API key (optional, has fallback mode)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/meta-analysis-ai-backend.git
   cd meta-analysis-ai-backend
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if you want AI features
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Test the API**
   ```bash
   # Visit http://localhost:8000/docs for interactive documentation
   curl http://localhost:8000/health
   ```

## 🧪 Usage Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Create research question (set use_ai_rephrasing=False for full results)
payload = {
    "question": "Is metformin better for diabetes than other Drugs",
    "pico": {
        "population": "Adults",
        "intervention": "Metformin",
        "comparison": "Other diabetes drugs",
        "outcome": "HbA1c levels"
    }
}

response = requests.post(f"{BASE_URL}/api/research-question", 
                       json=payload,
                       params={"use_ai_rephrasing": False})
question_id = response.json()["question_id"]

# 2. Search PubMed
papers = requests.get(f"{BASE_URL}/api/pubmed-search", 
                     params={"question_id": question_id, "max_results": 200})

# 3. Screen papers
screening = requests.post(f"{BASE_URL}/api/screening-columns", 
                         json={"question_id": question_id, "papers": papers.json()["papers"][:10]})

# 4. Generate reports
for format in ["csv", "xlsx", "docx", "pdf"]:
    report = requests.get(f"{BASE_URL}/api/generate-report", 
                         params={"question_id": question_id, "format": format})
    print(f"{format.upper()}: {report.json()['report_url']}")
```

## 🏗 Architecture

```
├── main.py                 # FastAPI application entry point
├── database.py            # Database configuration (SQLite/PostgreSQL)
├── models.py              # SQLAlchemy database models
├── schemas.py             # Pydantic request/response schemas
├── routers/               # API route handlers
│   ├── research_questions.py
│   ├── pubmed_search.py
│   ├── screening.py
│   ├── extraction.py
│   └── reports.py
├── services/              # Business logic services
│   ├── ai_service.py      # AI/LLM integration (OpenAI/Anthropic)
│   ├── pubmed_service.py  # PubMed API integration
│   └── report_service.py  # Report generation (CSV/Excel/Word/PDF)
└── utils/                 # Utility functions
    ├── logging_config.py
    └── error_handlers.py
```

## 📊 Report Formats

The system generates comprehensive reports in multiple formats:

- **📊 CSV**: Raw data for statistical analysis
- **📈 Excel**: Multi-sheet workbook with summary, screening, and extracted data
- **📝 Word**: Formatted document with tables, sections, and references
- **📄 PDF**: Professional report with styled layouts

## 🔧 Configuration

### Environment Variables

```bash
# Database (optional - uses SQLite by default)
DATABASE_URL=postgresql://username:password@localhost/meta_analysis_db

# AI Services (optional - has fallback mode)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# PubMed API
NCBI_EMAIL=your_email@example.com

# Security
SECRET_KEY=your_secret_key_here
```

### Key Parameters

- `use_ai_rephrasing=False`: Get full PubMed results (recommended)
- `use_ai_rephrasing=True`: Get refined AI-enhanced search
- `max_results`: Control number of papers retrieved
- `min_score`: Filter papers by screening score

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Testing

The repository includes comprehensive test scripts:

```bash
# Test complete workflow with metformin example
python test_metformin_173_papers.py

# Compare with direct PubMed search
python test_search_comparison.py

# Test all report formats
python test_all_formats.py
```

## 🚀 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Set up PostgreSQL database
- [ ] Configure environment variables
- [ ] Set up reverse proxy (nginx)
- [ ] Enable HTTPS
- [ ] Configure logging and monitoring
- [ ] Set up backup strategy

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 **Documentation**: Check `/docs` endpoint when running
- 🐛 **Issues**: Report bugs via GitHub Issues
- 💬 **Discussions**: Use GitHub Discussions for questions

## 🎯 Roadmap

- [ ] User authentication and multi-tenancy
- [ ] Advanced statistical analysis
- [ ] Integration with reference managers (Zotero, EndNote)
- [ ] Real-time collaboration features
- [ ] Advanced visualization tools
- [ ] Mobile app support

## 🏆 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [PubMed E-utilities](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- AI integration with OpenAI and Anthropic
- Report generation with python-docx and reportlab

---

**Made with ❤️ for the research community**