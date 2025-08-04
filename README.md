# Meta-Analysis AI Backend

A FastAPI-based backend system for automating meta-analysis research workflows, from research question formulation to final report generation.

## 🚀 Features

- **AI-Powered Question Rephrasing**: Automatically refine research questions using PICO criteria
- **PubMed Integration**: Search and retrieve papers from PubMed with MeSH term expansion
- **Intelligent Paper Screening**: AI-based screening with customizable criteria
- **Automated Data Extraction**: Extract structured meta-analysis data from papers
- **Report Generation**: Export results in CSV and Excel formats
- **RESTful API**: Complete REST API with comprehensive documentation

## 📋 API Endpoints

### Core Workflow

1. **POST /api/research-question** - Submit research question with PICO criteria
2. **GET /api/pubmed-search** - Search PubMed for relevant papers
3. **POST /api/screening-columns** - AI-powered paper screening
4. **GET /api/filtered-papers** - Get papers above score threshold
5. **POST /api/extract-data** - Extract structured data from selected papers
6. **GET /api/generate-report** - Generate downloadable reports

### Additional Endpoints

- **GET /api/reports** - List all generated reports
- **GET /api/download-report/{filename}** - Download specific report
- **GET /api/report-preview/{question_id}** - Preview report data
- **POST /api/custom-screening-column** - Create custom screening criteria

## 🛠 Installation

### Prerequisites

- Python 3.8+
- PostgreSQL (optional, SQLite used by default)
- OpenAI API key or Anthropic API key (for AI features)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Meta_claude_Code
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

   Or using uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
DATABASE_URL=postgresql://username:password@localhost/meta_analysis_db
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
NCBI_EMAIL=your_email@example.com
SECRET_KEY=your_secret_key_here
```

### Database Options

- **SQLite** (default): Automatic setup, no configuration needed
- **PostgreSQL**: Uncomment and configure DATABASE_URL for production use

## 🧪 Demo Script

Run the complete workflow demonstration:

```bash
python demo.py
```

This script will:
1. Create a sample research question
2. Search PubMed for papers
3. Screen papers using AI
4. Extract structured data
5. Generate reports in CSV and Excel formats

## 📊 Workflow Example

```python
import requests

# 1. Create research question
response = requests.post("http://localhost:8000/api/research-question", json={
    "question": "Does Pembrolizumab improve survival in elderly lung cancer patients?",
    "pico": {
        "population": "Elderly lung cancer patients",
        "intervention": "Pembrolizumab",
        "comparison": "Standard chemotherapy",
        "outcome": "Overall survival"
    }
})
question_id = response.json()["question_id"]

# 2. Search PubMed
papers = requests.get(f"http://localhost:8000/api/pubmed-search?question_id={question_id}")

# 3. Screen papers
screening = requests.post("http://localhost:8000/api/screening-columns", json={
    "question_id": question_id,
    "papers": papers.json()["papers"][:10]
})

# 4. Generate report
report = requests.get(f"http://localhost:8000/api/generate-report?question_id={question_id}")
```

## 🏗 Architecture

```
├── main.py                 # FastAPI application entry point
├── database.py            # Database configuration
├── models.py              # SQLAlchemy models
├── schemas.py             # Pydantic schemas
├── routers/               # API route handlers
│   ├── research_questions.py
│   ├── pubmed_search.py
│   ├── screening.py
│   ├── extraction.py
│   └── reports.py
├── services/              # Business logic services
│   ├── ai_service.py      # AI/LLM integration
│   ├── pubmed_service.py  # PubMed API integration
│   └── report_service.py  # Report generation
├── utils/                 # Utility functions
│   ├── logging_config.py  # Logging setup
│   └── error_handlers.py  # Error handling
└── demo.py               # Complete workflow demonstration
```

## 📚 API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔧 Development

### Running Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests (when test suite is available)
pytest
```

### Code Formatting

```bash
# Install formatting tools
pip install black isort

# Format code
black .
isort .
```

## 📝 Data Models

### Research Question
- Original and rephrased text
- PICO criteria (Population, Intervention, Comparison, Outcome)
- Timestamp and metadata

### Paper
- PubMed ID, title, abstract, authors
- Publication date, DOI, MeSH terms
- Screening results and scores
- Extracted structured data

## 🤖 AI Integration

The system supports multiple AI providers:

- **OpenAI GPT-3.5/4**: For question rephrasing, screening, and data extraction
- **Anthropic Claude**: Alternative AI provider
- **Fallback Mode**: Basic functionality without AI keys

## 🔒 Security Features

- Input validation using Pydantic schemas
- SQL injection protection via SQLAlchemy ORM
- Error handling and logging
- CORS middleware for web integration

## 📈 Performance

- Efficient database queries with SQLAlchemy
- Batch processing for large paper sets
- Configurable rate limiting for external APIs
- Caching for PubMed results

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
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Run the demo script to verify setup
3. Check logs in the `logs/` directory
4. Review configuration in `.env` file

## 🎯 Future Enhancements

- [ ] User authentication and multi-tenancy
- [ ] Advanced statistical analysis
- [ ] Integration with reference managers
- [ ] Real-time collaboration features
- [ ] Advanced visualization tools