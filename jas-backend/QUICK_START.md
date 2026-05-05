# Quick Start Guide - Backend v2.0

## ⚡ 5-Minute Setup

### Step 1: Install Requirements
```bash
cd jas-backend
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
copy .env.example .env
# Edit .env - make sure TESSERACT_CMD path is correct for your system
```

### Step 3: Run Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Open API Documentation
```
http://localhost:8000/docs
```

---

## 🧪 Quick Test

### Using Python
```python
import requests

# Upload a document
with open("sample.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": f}
    )
    doc_id = response.json()["document_id"]

# Process it
response = requests.post(f"http://localhost:8000/process/{doc_id}")
print(response.json())
```

### Using cURL
```bash
# Upload
curl -F "file=@sample.pdf" http://localhost:8000/upload

# Process
curl -X POST http://localhost:8000/process/{document_id}

# Get dashboard
curl http://localhost:8000/dashboard
```

---

## 📁 Project Structure

```
jas-backend/
├── app/
│   ├── main.py              → FastAPI routes
│   ├── db.py                → Database models
│   ├── config.py            → Configuration
│   ├── logger.py            → Logging
│   ├── schemas.py           → API schemas
│   ├── services/
│   │   ├── ingestion.py     → Upload handling
│   │   ├── ocr_service.py   → Text extraction
│   │   ├── preprocessing.py → Text cleaning
│   │   └── pipeline.py      → Orchestration
│   ├── rules.py             → Action detection
│   └── extract.py           → (Deprecated)
├── data/
│   └── documents/           → Uploaded files
├── .env.example             → Configuration template
├── requirements.txt         → Dependencies
├── API_DOCUMENTATION.md     → Full API docs
├── ARCHITECTURE.md          → System design
└── IMPLEMENTATION_SUMMARY.md → What was built
```

---

## 🔄 API Workflow

### 1️⃣ Upload Document
```
POST /upload
Content-Type: multipart/form-data
Body: file

Response: 200 OK
{
  "document_id": "uuid...",
  "filename": "judgment.pdf",
  "status": "uploaded"
}
```

### 2️⃣ Process Document
```
POST /process/{document_id}

Response: 200 OK
{
  "success": true,
  "actions": [
    {
      "type": "COMPLIANCE",
      "task": "File response within 30 days",
      "deadline": "2024-06-04",
      "confidence": 0.95
    }
  ]
}
```

### 3️⃣ Review Actions
```
POST /actions/{action_id}/review?status=APPROVED

Response: 200 OK
{
  "success": true,
  "message": "Action updated"
}
```

---

## ⚙️ Configuration

Edit `.env`:

```bash
# Database (default: SQLite)
DATABASE_URL=sqlite:///./test.db

# Tesseract path (IMPORTANT - set this!)
# Windows
TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# Linux
TESSERACT_CMD=/usr/bin/tesseract

# Document storage
DOCUMENTS_DIR=data/documents

# API limits
MAX_UPLOAD_SIZE_MB=50
MAX_FILES_PER_UPLOAD=5

# Logging
LOG_LEVEL=INFO
```

---

## 🐛 Troubleshooting

### "Tesseract not found"
- Install: https://github.com/UB-Mannheim/tesseract/wiki
- Check: `TESSERACT_CMD` in `.env` is correct

### "Port already in use"
```bash
# Use different port
uvicorn app.main:app --port 8001
```

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "Database locked"
- Close other connections
- Try again in a few seconds

---

## 📚 Documentation

- **Full API Reference:** See `API_DOCUMENTATION.md`
- **System Architecture:** See `ARCHITECTURE.md`
- **Implementation Details:** See `IMPLEMENTATION_SUMMARY.md`
- **Interactive Docs:** http://localhost:8000/docs

---

## 🚀 What's New in v2.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Multi-file upload | ❌ | ✅ |
| Document tracking | ❌ | ✅ |
| Status lifecycle | ❌ | ✅ |
| Environment config | ❌ | ✅ |
| Comprehensive logging | ❌ | ✅ |
| Error handling | Basic | Advanced |
| API endpoints | 4 | 12+ |

---

## ✅ Validation Checklist

- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] `.env` configured with Tesseract path
- [ ] Server runs: `uvicorn app.main:app --reload`
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Can upload PDF: `curl -F "file=@test.pdf" http://localhost:8000/upload`
- [ ] Can process: `curl -X POST http://localhost:8000/process/{id}`

---

## 💡 Tips

- **Interactive Testing:** Use http://localhost:8000/docs (Swagger UI)
- **Alternative Docs:** http://localhost:8000/redoc (ReDoc)
- **Log Viewing:** Check console output for detailed logs
- **Database:** SQLite file created at `test.db`
- **Uploads:** Files stored in `data/documents/` directory

---

## 📞 Need Help?

1. Check `.env` configuration
2. Review `API_DOCUMENTATION.md`
3. Check `ARCHITECTURE.md` for system design
4. View logs in terminal output
5. See troubleshooting in `ARCHITECTURE.md`

---

**Version:** 2.0.0  
**Last Updated:** May 5, 2026
