import axios from "axios";

export const axiosInstance = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 30000,
});

axiosInstance.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response && err.response.data) {
      return Promise.reject(new Error(JSON.stringify(err.response.data)));
    }
    return Promise.reject(err);
  }
);

export default axiosInstance;
