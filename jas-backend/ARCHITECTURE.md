# Backend Architecture & Implementation Guide

## 🏗️ Architecture Overview

The Judgment-to-Action backend v2.0 follows a **modular service-oriented architecture** with clear separation of concerns.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FastAPI Routes                            │
│  /upload  /process  /actions  /dashboard                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                   Service Layer                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Ingestion   │  │ OCR Service  │  │ Preprocessing        │   │
│  │ - Upload    │  │ - Extract    │  │ - Clean Text         │   │
│  │ - Metadata  │  │ - Fallback   │  │ - Normalize          │   │
│  │ - Track     │  │ - Logging    │  │ - Split Sentences    │   │
│  └─────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                   │
│  ┌──────────────────────────────────────┐                       │
│  │      Pipeline Orchestrator            │                       │
│  │  Coordinates all services             │                       │
│  │  Manages workflow execution           │                       │
│  └──────────────────────────────────────┘                       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────────┐
│                   Data Layer                                     │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │Database │  │Documents │  │Actions   │  │Metadata  │         │
│  │Models   │  │Storage   │  │Storage   │  │Tracking  │         │
│  └─────────┘  └──────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 Module Structure

### 1. **Configuration (`app/config.py`)**
- Centralized settings management
- Environment variable loading
- Default configurations

```python
from app.config import settings

# Access any setting
print(settings.TESSERACT_CMD)
print(settings.DOCUMENTS_DIR)
```

### 2. **Logging (`app/logger.py`)**
- Consistent logging across services
- Timestamp and level tracking
- Stdout output

```python
from app.logger import setup_logger

logger = setup_logger(__name__)
logger.info("Processing document")
logger.error("An error occurred")
```

### 3. **Database (`app/db.py`)**

Two main models:

#### Document Model
```python
class Document(Base):
    id: str (UUID)
    filename: str
    file_path: str
    upload_time: datetime
    status: str  # uploaded, processing, processed, failed
    extracted_text: str (optional)
    error_message: str (optional)
```

#### Action Model
```python
class Action(Base):
    id: int
    document_id: str (FK)
    type: str  # COMPLIANCE, APPEAL, etc.
    task: str
    deadline: str (optional, YYYY-MM-DD)
    status: str  # PENDING, APPROVED, REJECTED
    confidence: str (float)
    evidence: str
    created_at: datetime
```

### 4. **Schemas (`app/schemas.py`)**
Pydantic models for API validation and documentation.

---

## 🔄 Service Layer

### 1. **Ingestion Service** (`app/services/ingestion.py`)

Handles document upload and metadata management.

**Key Functions:**
```python
# Save uploaded file and create DB record
ingestion_service.save_document(
    file_content: bytes,
    filename: str
) -> Tuple[document_id, success, message]

# Retrieve document path
ingestion_service.get_document_path(document_id) -> Tuple[path, exists]

# Update document status
ingestion_service.update_document_status(
    document_id,
    status,
    extracted_text=None,
    error_message=None
) -> bool
```

### 2. **OCR Service** (`app/services/ocr_service.py`)

Handles text extraction from PDFs with fallback logic.

**Key Features:**
- Tries text-based extraction first
- Falls back to OCR for scanned pages
- Handles errors gracefully
- Configurable Tesseract path

**Key Functions:**
```python
# Extract text from PDF
ocr_service.extract_text(file_path) -> Tuple[text, success]

# Private: OCR single page
ocr_service._ocr_page(page, page_num) -> str
```

### 3. **Preprocessing Service** (`app/services/preprocessing.py`)

Cleans and normalizes extracted text.

**Pipeline Steps:**
1. Remove multiple newlines
2. Normalize whitespace
3. Remove special characters
4. Remove headers/footers
5. Split into sentences

**Key Functions:**
```python
# Individual steps
preprocessing_service.clean_text(text) -> str
preprocessing_service.remove_headers_footers(text) -> str
preprocessing_service.split_into_sentences(text) -> List[str]

# Complete pipeline
preprocessing_service.preprocess_pipeline(text) -> List[str]
```

### 4. **Pipeline Orchestrator** (`app/services/pipeline.py`)

Coordinates the complete workflow.

**Workflow:**
```
1. Load document from DB
2. Extract text via OCR
3. Preprocess text
4. Detect actions
5. Save results
```

**Key Functions:**
```python
# Main processing function
pipeline_orchestrator.process_document(document_id) -> Dict

# Helper: Save actions to DB
pipeline_orchestrator._save_actions(document_id, actions) -> int
```

---

## 🔌 Integration Points

### Rules Engine (`app/rules.py`)

Action detection logic. Called by orchestrator.

```python
# Called in pipeline
actions = detect_actions(sentences)

# Returns list of detected actions with:
# - type: COMPLIANCE, APPEAL, etc.
# - task: Action description
# - deadline: Extracted deadline
# - confidence: Confidence score
# - evidence: Original sentence
```

---

## 🚀 Request Flow

### Upload → Process → Detect Flow

```
1. User uploads PDF via POST /upload
   └─> IngestionService.save_document()
       - Save file to disk
       - Create Document record (status: "uploaded")
       - Return document_id

2. User triggers processing via POST /process/{document_id}
   └─> PipelineOrchestrator.process_document()
       
       2a. Update status: "processing"
       
       2b. OCRService.extract_text()
           - pdfplumber: Try text extraction
           - Fallback: pytesseract for scanned pages
           - Logging: Track each step
       
       2c. PreprocessingService.preprocess_pipeline()
           - Clean text
           - Remove noise
           - Split into sentences
       
       2d. RulesEngine.detect_actions()
           - Analyze sentences
           - Extract actions & deadlines
       
       2e. PipelineOrchestrator._save_actions()
           - Save to Action table
           - Update Document status: "processed"
       
       └─> Return results with actions

3. User reviews actions via POST /actions/{id}/review
   └─> Update Action status: APPROVED/REJECTED
```

---

## 💾 Database Schema

### Documents Table
```sql
CREATE TABLE documents (
    id VARCHAR PRIMARY KEY,
    filename VARCHAR,
    file_path VARCHAR,
    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR DEFAULT 'uploaded',
    extracted_text TEXT,
    error_message VARCHAR
);
```

### Actions Table
```sql
CREATE TABLE actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id VARCHAR,
    type VARCHAR,
    task TEXT,
    deadline VARCHAR,
    status VARCHAR DEFAULT 'PENDING',
    confidence VARCHAR,
    evidence TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔐 Error Handling Strategy

### Three-Tier Error Handling

**Tier 1: Service Level**
- Try-except in each service
- Log errors with context
- Return (data, success) tuples

**Tier 2: Orchestrator Level**
- Catch service errors
- Update document status to "failed"
- Store error message

**Tier 3: API Level**
- HTTPException for client errors
- 400: Validation errors
- 404: Resource not found
- 500: Processing errors

**Example Flow:**
```python
try:
    # Service logic
    text, success = ocr_service.extract_text(path)
    if not success:
        # Orchestrator handles
        ingestion_service.update_document_status(
            document_id, 
            "failed",
            error_message="OCR extraction failed"
        )
except Exception as e:
    # API responds
    raise HTTPException(
        status_code=500,
        detail=str(e)
    )
```

---

## 🧪 Testing Strategy

### Unit Tests (Recommended Structure)
```python
# test/services/test_ocr_service.py
def test_extract_text_text_based_pdf():
    text, success = ocr_service.extract_text("path/to/pdf")
    assert success
    assert len(text) > 0

def test_extract_text_scanned_pdf():
    # Test fallback to OCR
    pass

# test/services/test_preprocessing.py
def test_clean_text():
    assert preprocessing_service.clean_text("text  with   spaces") == "text with spaces"

def test_split_into_sentences():
    sentences = preprocessing_service.split_into_sentences("Hello. World.")
    assert len(sentences) == 2
```

### Integration Tests
```python
def test_full_pipeline():
    # Upload → Process → Verify
    document_id = "test-doc-id"
    result = pipeline_orchestrator.process_document(document_id)
    assert result["success"]
    assert len(result["actions"]) > 0
```

---

## 📊 Monitoring & Logging

All services log key events:

**Info Level:**
- Document uploads
- Processing start/completion
- Database operations

**Debug Level:**
- Individual service operations
- Sentence processing
- File operations

**Error Level:**
- Processing failures
- OCR errors
- Database issues

**View Logs:**
```bash
# Real-time
tail -f logs/app.log

# Filter by level
grep ERROR logs/app.log
grep "document_id" logs/app.log
```

---

## 🔧 Configuration Management

### Environment Variables

```bash
# .env file (create from .env.example)

# Database
DATABASE_URL=sqlite:///./test.db

# OCR
TESSERACT_CMD=/usr/bin/tesseract

# Storage
DOCUMENTS_DIR=data/documents

# API
MAX_UPLOAD_SIZE_MB=50
MAX_FILES_PER_UPLOAD=5

# Logging
LOG_LEVEL=INFO
```

### Runtime Configuration
```python
from app.config import settings

# Access
print(settings.DATABASE_URL)
print(settings.MAX_UPLOAD_SIZE_MB)

# Directories auto-created
# settings.__init__() creates DOCUMENTS_DIR
```

---

## 🚨 Production Considerations

### Before Deploying

1. **Database**
   - Switch from SQLite to PostgreSQL
   - Set `DATABASE_URL` environment variable
   - Run migrations

2. **File Storage**
   - Use cloud storage (S3, GCS, Azure Blob)
   - Modify `ingestion.py` to upload to cloud
   - Keep local temp storage minimal

3. **OCR**
   - Ensure Tesseract installed on server
   - Set correct `TESSERACT_CMD` path
   - Consider async processing for large files

4. **Logging**
   - Send logs to centralized service (Sentry, ELK)
   - Set `LOG_LEVEL=WARNING` or `ERROR`

5. **Security**
   - Enable CORS properly (not `["*"]`)
   - Add authentication/authorization
   - Validate file types strictly
   - Scan uploads for malware

6. **Performance**
   - Add caching layer (Redis)
   - Implement async processing
   - Use worker queue (Celery)
   - Add database indexes

---

## 📚 Glossary

| Term | Definition |
|------|-----------|
| **Document** | Uploaded PDF file with metadata |
| **Status** | Document lifecycle: uploaded → processing → processed |
| **OCR** | Optical Character Recognition (extract text from images) |
| **Action** | Extracted task/compliance item from document |
| **Pipeline** | Complete processing workflow |
| **Sentence** | Preprocessed unit of text |

---

## 🔄 Version History

### v2.0.0 (Current)
✅ Service-oriented architecture
✅ Multi-file upload
✅ Document metadata tracking
✅ Modular services
✅ Comprehensive logging
✅ Environment configuration

### v1.0.0 (Deprecated)
- Single file processing
- Basic OCR
- Hardcoded paths

---

## 📞 Troubleshooting

### Issue: "Tesseract not found"
**Solution:** Set `TESSERACT_CMD` in `.env` or install Tesseract

### Issue: "Database locked"
**Solution:** Close other connections, enable WAL mode in SQLite

### Issue: "File too large"
**Solution:** Increase `MAX_UPLOAD_SIZE_MB` or split document

### Issue: "No text extracted"
**Solution:** Check if PDF is scanned, verify Tesseract installation

---

## 🤝 Contributing

When adding features:
1. Create service in `app/services/`
2. Use dependency injection
3. Add logging
4. Write type hints
5. Document changes
6. Add tests

---

## 📖 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Pydantic](https://pydantic-ai.readthedocs.io/)
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
