# 🚀 JUDGEAI AUDIT - QUICK REFERENCE & FIX CHECKLIST

## CRITICAL ISSUES AT A GLANCE (Fix Immediately)

### Issue 1: OCR Service Return Type ❌
**Status:** Not Fixed  
**File:** `jas-backend/app/services/ocr_service.py` line 70  
**Current:**
```python
except Exception as e:
    return "", False  # ❌ Returns string instead of list
```
**Should Be:**
```python
except Exception as e:
    return [], False  # ✅ Consistent with success case
```
**Time:** 5 min | **Severity:** CRITICAL | **Impact:** Pipeline crash

---

### Issue 2: PUT /actions/{id} Request Body Format ❌
**Status:** Not Fixed  
**Files:** 
- Backend: `jas-backend/app/main.py` line 457
- Frontend: `frontend/judgement-insight-main/src/services/services.js` line 60

**Current Backend:**
```python
def update_action(
    action_id: int,
    task: str | None = None,  # ← Expects query param, not body
    ...
):
```

**Current Frontend:**
```javascript
const res = await axios.put(`/actions/${id}`, payload);  // ← Sends body
```

**Fix - Add Pydantic Model:**
```python
from pydantic import BaseModel

class ActionUpdateRequest(BaseModel):
    task: Optional[str] = None
    deadline: Optional[str] = None
    department: Optional[str] = None
    priority: Optional[str] = None

@app.put("/actions/{action_id}", response_model=ActionDetailsResponse)
def update_action(
    action_id: int,
    update_data: ActionUpdateRequest
):
    action = db.query(Action).filter(Action.id == action_id).first()
    if not action:
        raise HTTPException(status_code=404)
    
    if update_data.task is not None:
        action.task = update_data.task
    if update_data.deadline is not None:
        action.deadline = update_data.deadline
    if update_data.department is not None:
        action.department = update_data.department
    if update_data.priority is not None:
        action.priority = update_data.priority
    
    action.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(action)
    return ActionDetailsResponse.from_orm(action)
```

**Time:** 15 min | **Severity:** CRITICAL | **Impact:** Update action endpoint fails

---

### Issue 3: Dashboard Field Name Mismatch ❌
**Status:** Workaround Exists (Fragile)  
**Files:**
- Backend: `jas-backend/app/main.py` line 599-640
- Frontend: `frontend/judgement-insight-main/src/services/services.js` line 51-58
- Schema: `jas-backend/app/schemas.py` line 93-102

**Problem:** Backend returns `pending_actions`, `approved_actions` but frontend expects `pending`, `approved`

**Quick Fix (Frontend):** Already working due to fallback logic
```javascript
return {
  ...data,
  pending: data.pending ?? data.pending_actions ?? 0,
  approved: data.approved ?? data.approved_actions ?? 0,
  rejected: data.rejected ?? data.rejected_actions ?? 0,
};
```

**Better Fix (Backend) - Add @computed_field:**
```python
from pydantic import computed_field

class DashboardStats(BaseModel):
    # ... existing fields ...
    pending_actions: int
    approved_actions: int
    rejected_actions: int
    
    @computed_field
    @property
    def pending(self) -> int:
        return self.pending_actions
    
    @computed_field
    @property
    def approved(self) -> int:
        return self.approved_actions
    
    @computed_field
    @property
    def rejected(self) -> int:
        return self.rejected_actions
```

**Time:** 10 min | **Severity:** CRITICAL | **Impact:** Dashboard displays may be incorrect

---

### Issue 4: UploadSection Error Handling ❌
**Status:** Not Fixed  
**File:** `frontend/judgement-insight-main/src/components/court/UploadSection.tsx` line 70-125

**Current Problem:**
```javascript
} catch (e) {
  toast.error(e instanceof Error ? e.message : "Failed to upload files.");
  // ❌ No state cleanup - files remain in dirty state
} finally {
  setLoading(false);
  if (inputRef.current) inputRef.current.value = "";
}
```

**Fix:**
```javascript
} catch (e) {
  toast.error(e instanceof Error ? e.message : "Failed to upload files.");
  setFiles([]);  // ✅ Clear files on error
  if (inputRef.current) inputRef.current.value = "";
} finally {
  setLoading(false);
}
```

**Time:** 5 min | **Severity:** CRITICAL | **Impact:** UI state corruption on errors

---

### Issue 5: Evidence Page Type Conversion ❌
**Status:** Not Fixed  
**Files:**
- Storage: `jas-backend/app/services/pipeline.py` line 238-240
- Retrieval: `jas-backend/app/db.py` line 95-99

**Problem:**
```python
# Stored as string
evidence_page = Column(String, nullable=True)

# But retrieved with int() conversion
@property
def evidence(self):
    return {
        "page": int(self.evidence_page) if self.evidence_page is not None and str(self.evidence_page).isdigit() else self.evidence_page,
        # ❌ Fails if page contains non-numeric characters
    }
```

**Fix:**
```python
@property
def evidence(self):
    page = self.evidence_page
    
    # Smart type handling
    if page is None:
        page_value = None
    elif isinstance(page, str) and page.isdigit():
        page_value = int(page)
    else:
        page_value = str(page) if page is not None else None
    
    return {
        "text": self.evidence_text,
        "page": page_value,
        "sentence_index": self.evidence_index,
        "char_start": self.evidence_start,
        "char_end": self.evidence_end,
    }
```

**Time:** 15 min | **Severity:** CRITICAL | **Impact:** API crashes when returning action details

---

### Issue 6: Duplicate Action Detection ❌
**Status:** Not Fixed  
**File:** `jas-backend/app/services/pipeline.py` line 82-87

**Current:**
```python
existing_actions = db.query(Action).filter(Action.document_id == document_id).first()
if existing_actions:
    logger.warning(f"Document {document_id} already has actions. Skipping reprocessing.")
    db.close()
    return {  # ❌ Just returns without actually creating actions
        "success": True,
        "message": "Document already processed",
        "actions": [],
    }
```

**Fix - Delete Old Actions Before Reprocessing:**
```python
# Check and delete old actions
existing_actions = db.query(Action).filter(Action.document_id == document_id).all()
if existing_actions:
    logger.info(f"Found {len(existing_actions)} old actions for document: {document_id}")
    for action in existing_actions:
        db.delete(action)
    db.commit()
    logger.info(f"Deleted old actions for reprocessing")

# Continue with normal processing (no return here)
```

**Time:** 20 min | **Severity:** CRITICAL | **Impact:** Can create duplicate actions on reprocessing

---

### Issue 7: Input Validation in Preprocessing ❌
**Status:** Not Fixed  
**File:** `jas-backend/app/services/preprocessing.py` line 99-125

**Add Input Validation:**
```python
def preprocess_pipeline(pages: List[Dict[str, str]]) -> List[Dict[str, object]]:
    # ✅ Validate input
    if not isinstance(pages, list):
        logger.error(f"Expected list of pages, got {type(pages)}")
        return []
    
    if not pages:
        logger.warning("No pages provided for preprocessing")
        return []
    
    all_sentences: List[Dict[str, object]] = []

    for page_obj in pages:
        # ✅ Validate each page
        if not isinstance(page_obj, dict):
            logger.warning(f"Skipping invalid page object: {type(page_obj)}")
            continue
        
        page_num = page_obj.get("page")
        page_text = page_obj.get("text", "") or ""
        # ... rest continues
```

**Time:** 15 min | **Severity:** HIGH | **Impact:** Type errors on malformed input

---

## HIGH PRIORITY ISSUES (Fix This Sprint)

### Issue 8: extract.py Deprecated Function ❌
**File:** `jas-backend/app/extract.py` line 31  
**Action:** Either delete or update for new return type  
**Time:** 10 min

### Issue 9: Status Update Return Not Checked ❌
**File:** `jas-backend/app/services/pipeline.py` lines 69, 107, 126, 154, 176  
**Action:** Add `if not success: return error` after each status update  
**Time:** 10 min

---

## MEDIUM PRIORITY (Fix Next Sprint)

| Issue | File | Time | Action |
|-------|------|------|--------|
| Status value capitalization | db.py, ingestion.py | 20 min | Standardize to UPPERCASE |
| UTC vs local time | action_engine.py, alert_service.py | 15 min | Use datetime.utcnow() everywhere |
| Remove unnecessary async | main.py line 249 | 5 min | Remove `async` from process_document |
| Upload field naming | services.js | 10 min | Standardize single/batch to same field name |
| Confidence type consistency | Multiple | 15 min | Decide on float or string, be consistent |

---

## TESTING CHECKLIST

### Before Deployment Test All:

- [ ] **Upload PDF** - Single file upload works
- [ ] **Process Document** - OCR extracts text correctly
- [ ] **View Actions** - Actions display without API crash
- [ ] **Update Action** - Clicking edit and saving updates action
- [ ] **Review Action** - Approve/Reject changes status
- [ ] **View Dashboard** - All counts display correctly
- [ ] **Batch Upload** - Multiple files upload together
- [ ] **Error Scenarios:**
  - [ ] Upload invalid file type
  - [ ] Upload file larger than limit
  - [ ] Process non-existent document
  - [ ] Update action with invalid data
  - [ ] Clear cache and reload

### Backend Unit Tests:

```bash
cd jas-backend
python -m pytest tests/ -v
python qa_validation_test.py
```

### Frontend Unit Tests:

```bash
cd frontend/judgement-insight-main
npm test
```

### Manual End-to-End:

1. Start backend: `python -m app.main`
2. Start frontend: `npm run dev`
3. Upload sample PDF from `data/samples/`
4. Process document
5. Verify actions appear
6. Update an action
7. Review (approve/reject) an action
8. Check dashboard updated

---

## FIX IMPLEMENTATION ORDER

### Phase 1: Critical (Do First)
```
1. Fix OCR return type (5 min)
2. Fix Evidence page conversion (15 min)
3. Fix PUT /actions body format (15 min)
4. Fix UploadSection error handling (5 min)
5. Fix Dashboard fields (10 min)
TEST & VERIFY
```
**Total: 50 minutes**

### Phase 2: High (This Sprint)
```
1. Fix duplicate detection (20 min)
2. Add input validation to preprocessing (15 min)
3. Add status update checks (10 min)
4. Fix/remove extract.py (10 min)
TEST & VERIFY
```
**Total: 55 minutes**

### Phase 3: Medium (Next Sprint)
```
1. Standardize status values (20 min)
2. Fix UTC/local time (15 min)
3. Remove unnecessary async (5 min)
4. Fix field naming (10 min)
5. Type consistency (15 min)
TEST & VERIFY
```
**Total: 65 minutes**

---

## SUMMARY

| Phase | Issues | Time | Testing |
|-------|--------|------|---------|
| Phase 1 (Critical) | 5 | 50 min | 1 hour |
| Phase 2 (High) | 4 | 55 min | 1.5 hours |
| Phase 3 (Medium) | 5 | 65 min | 1 hour |
| **TOTAL** | **14** | **2.5 hours** | **3.5 hours** |

**Total Resolution Time: ~6 hours**

---

**Status:** Ready for Implementation  
**Priority:** URGENT - Fix before next production deployment
