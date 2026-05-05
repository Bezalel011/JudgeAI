# Judgment-to-Action API v2.0 Documentation

## Overview

The Judgment-to-Action API is a robust FastAPI backend for processing PDF documents, extracting text through OCR, and detecting actionable items from judgment documents.

**Key Features:**
- Multi-file upload support
- Metadata tracking and status management
- OCR-based text extraction with fallback logic
- Text preprocessing and normalization
- Intelligent action detection
- Comprehensive API with filtering and sorting

---

## Installation & Setup

### Prerequisites
- Python 3.8+
- Tesseract OCR installed on system
- SQLite or PostgreSQL database

### Windows Setup
```bash
# Install Tesseract
# Download from: https://github.com/UB-Mannheim/tesseract/wiki

# Clone and setup project
cd JudgeAI/jas-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Configuration
```bash
# Copy the template
copy .env.example .env

# Edit .env with your settings
# Important: Set TESSERACT_CMD path correctly
```

### Run the API
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## API Endpoints

### Health & Info

#### GET `/`
Home endpoint - API status
```json
{
  "message": "Judgment-to-Action API v2.0 running",
  "status": "operational",
  "version": "2.0.0"
}
```

#### GET `/health`
Health check
```json
{
  "status": "healthy"
}
```

---

### Document Management

#### POST `/upload`
Upload a single PDF document

**Request:**
```
Content-Type: multipart/form-data
Body: file (PDF file)
```

**Response:** `200 OK`
```json
{
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "judgment_2024.pdf",
  "status": "uploaded",
  "message": "Document judgment_2024.pdf uploaded successfully",
  "upload_time": "2024-05-05T10:30:45"
}
```

**Errors:**
- `400`: Invalid file type (only PDF supported) or file too large
- `500`: Server error

---

#### POST `/upload-batch`
Upload multiple PDF documents (max 5 files)

**Request:**
```
Content-Type: multipart/form-data
Body: files[] (multiple PDF files)
```

**Response:** `200 OK`
```json
{
  "total_uploaded": 3,
  "documents": [
    {
      "document_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "doc1.pdf",
      "status": "uploaded",
      "message": "Document doc1.pdf uploaded successfully",
      "upload_time": "2024-05-05T10:30:45"
    }
  ],
  "failed_uploads": [
    {
      "filename": "doc2.txt",
      "error": "Only PDF files supported"
    }
  ],
  "message": "Uploaded 3 file(s)"
}
```

---

#### GET `/document/{document_id}`
Get document status and metadata

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "judgment.pdf",
  "file_path": "data/documents/550e8400-e29b-41d4-a716-446655440000.pdf",
  "upload_time": "2024-05-05T10:30:45",
  "status": "processed",
  "extracted_text": "The court hereby...",
  "error_message": null
}
```

**Statuses:**
- `uploaded`: File uploaded, awaiting processing
- `processing`: Currently being processed
- `processed`: Successfully processed
- `failed`: Processing failed

---

### Document Processing

#### POST `/process/{document_id}`
Trigger processing pipeline for a document

Processing Steps:
1. Load file from storage
2. Run OCR extraction (text-based + scanned PDFs)
3. Preprocess text (clean, normalize, split)
4. Detect actions
5. Store results

**Request:**
```
POST /process/550e8400-e29b-41d4-a716-446655440000
```

**Response:** `200 OK`
```json
{
  "success": true,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Document processed successfully",
  "sentence_count": 45,
  "action_count": 12,
  "actions": [
    {
      "type": "COMPLIANCE",
      "task": "Shall file response within 30 days",
      "deadline": "2024-06-04",
      "confidence": 0.95,
      "evidence": "Shall file response within 30 days"
    },
    {
      "type": "APPEAL",
      "task": "Consider filing appeal",
      "deadline": null,
      "confidence": 0.8,
      "evidence": "Liberty to appeal within 60 days"
    }
  ]
}
```

**Errors:**
- `404`: Document not found
- `500`: Processing failed

---

### Action Management

#### GET `/actions`
Get all detected actions with optional filtering

**Query Parameters:**
- `document_id` (optional): Filter by specific document
- `status_filter` (optional): Filter by status (PENDING, APPROVED, REJECTED)

**Request:**
```
GET /actions
GET /actions?document_id=550e8400-e29b-41d4-a716-446655440000
GET /actions?status_filter=PENDING
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "document_id": "550e8400-e29b-41d4-a716-446655440000",
    "type": "COMPLIANCE",
    "task": "File response within 30 days",
    "deadline": "2024-06-04",
    "status": "PENDING",
    "confidence": "0.95",
    "evidence": "The court orders...",
    "created_at": "2024-05-05T10:35:20"
  }
]
```

---

#### GET `/actions/{action_id}`
Get a specific action by ID

**Response:** `200 OK`
```json
{
  "id": 1,
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "COMPLIANCE",
  "task": "File response within 30 days",
  "deadline": "2024-06-04",
  "status": "PENDING",
  "confidence": "0.95",
  "evidence": "The court orders...",
  "created_at": "2024-05-05T10:35:20"
}
```

---

#### POST `/actions/{action_id}/review`
Update action status (approve/reject)

**Request:**
```
POST /actions/1/review?status=APPROVED
```

Valid statuses: `PENDING`, `APPROVED`, `REJECTED`

**Response:** `200 OK`
```json
{
  "success": true,
  "message": "Action 1 updated to APPROVED"
}
```

**Errors:**
- `400`: Invalid status value
- `404`: Action not found
- `500`: Update failed

---

### Analytics & Dashboard

#### GET `/dashboard`
Get comprehensive dashboard statistics

**Response:** `200 OK`
```json
{
  "total_documents": 25,
  "processed_documents": 20,
  "processing_documents": 2,
  "failed_documents": 3,
  "total_actions": 156,
  "pending_actions": 89,
  "approved_actions": 54,
  "rejected_actions": 13
}
```

---

## Data Models

### Document
```python
{
  "id": "UUID",
  "filename": "string",
  "file_path": "string",
  "upload_time": "datetime",
  "status": "uploaded|processing|processed|failed",
  "extracted_text": "string (optional)",
  "error_message": "string (optional)"
}
```

### Action
```python
{
  "id": "integer",
  "document_id": "UUID",
  "type": "COMPLIANCE|APPEAL|...",
  "task": "string",
  "deadline": "YYYY-MM-DD (optional)",
  "status": "PENDING|APPROVED|REJECTED",
  "confidence": "float",
  "evidence": "string",
  "created_at": "datetime"
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (wrong file type, oversized file, etc.)
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side processing error

---

## Configuration

Environment variables (in `.env`):

```bash
# Database
DATABASE_URL=sqlite:///./test.db

# OCR (Tesseract path)
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Storage
DOCUMENTS_DIR=data/documents

# API Limits
MAX_UPLOAD_SIZE_MB=50
MAX_FILES_PER_UPLOAD=5

# Logging
LOG_LEVEL=INFO
```

---

## Usage Examples

### Python (requests)
```python
import requests

# Upload a document
with open("judgment.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    document_id = response.json()["document_id"]

# Process the document
response = requests.post(f"http://localhost:8000/process/{document_id}")
actions = response.json()["actions"]

# Get dashboard stats
response = requests.get("http://localhost:8000/dashboard")
stats = response.json()
```

### cURL
```bash
# Upload
curl -X POST -F "file=@judgment.pdf" http://localhost:8000/upload

# Process
curl -X POST http://localhost:8000/process/{document_id}

# Get actions
curl http://localhost:8000/actions

# Update action status
curl -X POST "http://localhost:8000/actions/1/review?status=APPROVED"
```

---

## Project Structure

```
jas-backend/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration & settings
│   ├── logger.py              # Logging setup
│   ├── main.py                # FastAPI app & routes
│   ├── db.py                  # Database models
│   ├── schemas.py             # Pydantic models
│   ├── extract.py             # Legacy OCR (deprecated)
│   ├── utils.py               # Utility functions
│   ├── rules.py               # Action detection logic
│   └── services/
│       ├── __init__.py
│       ├── ingestion.py       # Document upload & storage
│       ├── ocr_service.py     # OCR extraction
│       ├── preprocessing.py   # Text cleaning & normalization
│       └── pipeline.py        # Pipeline orchestration
├── data/
│   └── documents/             # Uploaded PDFs
├── .env.example               # Environment template
├── requirements.txt           # Dependencies
└── test.db                    # SQLite database
```

---

## Improvements from v1.0

✅ Multi-file upload support
✅ Document metadata tracking
✅ Status management (uploaded → processing → processed)
✅ Modular service architecture
✅ Environment-based configuration
✅ Comprehensive logging
✅ Improved error handling
✅ Dependency injection pattern
✅ Type hints throughout
✅ Batch processing support

---

## Support & Troubleshooting

### Tesseract not found
- Install Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
- Set correct path in `.env`: `TESSERACT_CMD=...`

### Database errors
- Ensure `data/documents/` directory exists
- Check file permissions
- For PostgreSQL, verify connection string

### Memory issues with large PDFs
- Increase available RAM
- Reduce `MAX_UPLOAD_SIZE_MB` in `.env`
- Process documents sequentially

---

## License

This project is part of the JudgeAI initiative.
