from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File
import shutil

from app.extract import pdf_to_text
from app.utils import split_sentences
from app.rules import detect_actions
from app.db import SessionLocal, Action

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 🔹 Home Route
@app.get("/")
def home():
    return {"message": "Judgment-to-Action API running"}


# 🔹 Process PDF
@app.post("/process")
async def process(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"

    # Save uploaded file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 1: Extract text
    text = pdf_to_text(file_path)

    # Step 2: Split sentences
    sentences = split_sentences(text)

    # Step 3: Detect actions
    actions = detect_actions(sentences)

    # Step 4: Save to database
    db = SessionLocal()

    try:
        for a in actions:
            db_action = Action(
                type=a["type"],
                task=a["task"],
                deadline=a.get("deadline"),
                status="PENDING"
            )
            db.add(db_action)

        db.commit()

    except Exception as e:
        print("Database Error:", e)

    finally:
        db.close()

    # Step 5: Return response
    return {"actions": actions}


# 🔹 Get all actions
@app.get("/actions")
def get_actions():
    db = SessionLocal()
    actions = db.query(Action).all()
    db.close()
    return actions


# 🔹 Review action (approve / reject)
@app.post("/review/{action_id}")
def review_action(action_id: int, status: str):
    db = SessionLocal()
    action = db.query(Action).filter(Action.id == action_id).first()

    if action:
        action.status = status
        db.commit()

    db.close()

    return {"message": "Action updated successfully"}


# 🔥 🔹 Dashboard API (SUMMARY)
@app.get("/dashboard")
def dashboard():
    db = SessionLocal()

    total = db.query(Action).count()
    pending = db.query(Action).filter(Action.status == "PENDING").count()
    approved = db.query(Action).filter(Action.status == "APPROVED").count()
    rejected = db.query(Action).filter(Action.status == "REJECTED").count()

    db.close()

    return {
        "total_actions": total,
        "pending": pending,
        "approved": approved,
        "rejected": rejected
    }


# 🔥 🔹 Filter API (BY STATUS)
@app.get("/actions/filter")
def filter_actions(status: str):
    db = SessionLocal()
    actions = db.query(Action).filter(Action.status == status).all()
    db.close()
    return actions