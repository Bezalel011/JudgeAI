import axios from "./api";

export async function uploadFile(file) {
  const fd = new FormData();
  fd.append("file", file);
  const res = await axios.post("/process", fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });
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

export async function getDashboard() {
  const res = await axios.get("/dashboard");
  return res.data;
}
