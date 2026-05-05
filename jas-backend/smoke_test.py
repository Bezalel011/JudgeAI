import os
import json

FILE_PATH = os.path.join(os.path.dirname(__file__), 'temp_sample_judgment.pdf')


def run_with_requests():
    import requests
    print('Using requests library for upload')
    with open(FILE_PATH, 'rb') as f:
        files = {'file': (os.path.basename(FILE_PATH), f, 'application/pdf')}
        r = requests.post('http://127.0.0.1:8000/upload', files=files)
    print('Upload status:', r.status_code)
    print('Upload response:', r.text)
    r.raise_for_status()
    data = r.json()
    document_id = data.get('document_id')
    if not document_id:
        raise SystemExit('No document_id returned')

    print('Document ID:', document_id)

    # Trigger processing
    rp = requests.post(f'http://127.0.0.1:8000/process/{document_id}')
    print('Process status:', rp.status_code)
    print('Process response:', rp.text)

    ra = requests.get(f'http://127.0.0.1:8000/actions?document_id={document_id}')
    print('Actions status:', ra.status_code)
    print('Actions response:', ra.text)


def run_with_httpclient():
    import http.client
    import mimetypes
    import uuid

    HOST = '127.0.0.1'
    PORT = 8000

    def encode_multipart(field_name, filename, file_bytes, boundary):
        crlf = b'\r\n'
        part = []
        part.append(f'--{boundary}'.encode('utf-8'))
        part.append(f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"'.encode('utf-8'))
        content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        part.append(f'Content-Type: {content_type}'.encode('utf-8'))
        part.append(b'')
        body = crlf.join(part) + crlf + file_bytes + crlf + f'--{boundary}--'.encode('utf-8') + crlf
        return body

    with open(FILE_PATH, 'rb') as f:
        file_bytes = f.read()

    boundary = '----WebKitFormBoundary' + uuid.uuid4().hex
    body = encode_multipart('file', os.path.basename(FILE_PATH), file_bytes, boundary)
    headers = {
        'Content-Type': f'multipart/form-data; boundary={boundary}',
        'Content-Length': str(len(body))
    }

    conn = http.client.HTTPConnection(HOST, PORT, timeout=60)
    print('Uploading file (http.client)...')
    conn.request('POST', '/upload', body, headers)
    resp = conn.getresponse()
    upload_data = resp.read().decode('utf-8')
    print('Upload status:', resp.status)
    print('Upload response:', upload_data)
    if resp.status >= 400:
        conn.close()
        raise SystemExit('Upload failed')

    data = json.loads(upload_data)
    document_id = data.get('document_id')
    if not document_id:
        conn.close()
        raise SystemExit('No document_id returned')

    print('Document ID:', document_id)

    # Trigger processing
    conn.request('POST', f'/process/{document_id}', headers={'Content-Type': 'application/json'})
    proc_resp = conn.getresponse()
    proc_body = proc_resp.read().decode('utf-8')
    print('Process status:', proc_resp.status)
    print('Process response:', proc_body)

    conn.request('GET', f'/actions?document_id={document_id}')
    acts_resp = conn.getresponse()
    acts_body = acts_resp.read().decode('utf-8')
    print('Actions status:', acts_resp.status)
    print('Actions response:', acts_body)

    conn.close()


if __name__ == '__main__':
    if not os.path.exists(FILE_PATH):
        print('Sample file not found:', FILE_PATH)
        raise SystemExit(1)

    try:
        run_with_requests()
    except Exception as e:
        print('requests not available or failed, falling back to http.client:', e)
        run_with_httpclient()
