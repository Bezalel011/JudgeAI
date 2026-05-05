from app.services.ingestion import ingestion_service
from app.services.ocr_service import ocr_service
from app.services.preprocessing import preprocessing_service
from app.services.nlp_service import get_nlp_service
from app.services.action_engine import get_action_engine

# Find latest document file in data/documents
import os
p = os.path.join(os.path.dirname(__file__), 'data', 'documents')
files = sorted(os.listdir(p)) if os.path.exists(p) else []
if not files:
    print('No documents found in data/documents')
    raise SystemExit(1)

# Use the latest file
fp = os.path.join(p, files[-1])
print('Using file:', fp)

pages, ok = ocr_service.extract_text(fp)
print('OCR success:', ok)
print('Pages:', pages)

sentences = preprocessing_service.preprocess_pipeline(pages)
print('Sentences metadata:', sentences)

full_text = "\n".join([p.get('text','') for p in pages])
nlp = get_nlp_service()
analysis = nlp.analyze_document(full_text, sentences)
print('NLP analysis:', analysis)

engine = get_action_engine()
actions = engine.generate_actions(analysis)
print('Generated actions:', actions)
