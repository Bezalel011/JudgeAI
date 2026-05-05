import axios from "./api";

// Upload single PDF file (v2.0 API)
export async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await axios.post("/upload", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// Upload multiple PDF files (v2.0 API - batch)
export async function uploadBatch(files) {
  const fd = new FormData();
  files.forEach((file) => {
    fd.append("files", file);
  });
  const res = await axios.post("/upload-batch", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// Process a document (v2.0 API)
export async function processDocument(documentId) {
  const res = await axios.post(`/process/${documentId}`);
  return res.data;
}

export async function getActions() {
  const res = await axios.get("/actions");
  // backend may return either an array or { actions: [] }
  return Array.isArray(res.data) ? res.data : res.data.actions ?? [];
}

export async function reviewAction(id, status) {
  const res = await axios.post(`/review/${id}?status=${status}`);
  return res.data;
}

export async function getActionHistory(id) {
  const res = await axios.get(`/actions/${id}/history`);
  return res.data;
}

export async function getDashboard() {
  const res = await axios.get("/dashboard");
  const data = res.data || {};
  return {
    ...data,
    pending: data.pending ?? data.pending_actions ?? 0,
    approved: data.approved ?? data.approved_actions ?? 0,
    rejected: data.rejected ?? data.rejected_actions ?? 0,
  };
}
