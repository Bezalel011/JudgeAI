import sqlite3, json, os
DB = os.path.join(os.path.dirname(__file__), 'test.db')
if not os.path.exists(DB):
    print('test.db not found at', DB)
    raise SystemExit(1)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Print columns
cur.execute("PRAGMA table_info(actions);")
cols = cur.fetchall()
print('actions table columns:')
for c in cols:
    print(c)

# Query last 10 actions
cur.execute("SELECT id, document_id, type, task, department, priority, confidence, evidence_text, evidence_page, evidence_index, evidence_start, evidence_end, created_at FROM actions ORDER BY id DESC LIMIT 10;")
rows = cur.fetchall()
print('\nlast actions:')
for r in rows:
    print(json.dumps({
        'id': r[0], 'document_id': r[1], 'type': r[2], 'task': r[3],
        'department': r[4], 'priority': r[5], 'confidence': r[6],
        'evidence_text': r[7], 'evidence_page': r[8], 'evidence_index': r[9], 'evidence_start': r[10], 'evidence_end': r[11],
        'created_at': r[12]
    }, default=str))

conn.close()