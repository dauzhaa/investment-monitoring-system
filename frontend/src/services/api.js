import axios from 'axios';

const api = axios.create({
  baseURL: 'http://77.95.201.98/api/v1',
  withCredentials: true,
});


api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');

    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default api;