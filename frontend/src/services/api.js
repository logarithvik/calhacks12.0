import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ===== Auth API =====
export const authAPI = {
  register: async (userData) => {
    const response = await api.post(`${API_BASE_URL}/api/auth/register`, userData);
    return response.data;
  },

  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response.data;
  },
};

// ===== Trials API =====
export const trialsAPI = {
  getAll: async () => {
    const response = await api.get('/api/trials/');
    return response.data;
  },

  getById: async (id) => {
    const response = await api.get(`/api/trials/${id}`);
    return response.data;
  },

  create: async (title, protocolFile) => {
    const formData = new FormData();
    formData.append('title', title);
    if (protocolFile) {
      formData.append('protocol_file', protocolFile);
    }
    
    const response = await api.post('/api/trials/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  delete: async (id) => {
    const response = await api.delete(`/api/trials/${id}`);
    return response.data;
  },

  getProtocolText: async (id) => {
    const response = await api.get(`/api/trials/${id}/protocol-text`);
    return response.data;
  },
};

// ===== Generation API =====
export const generationAPI = {
  generateSummary: async (trialId) => {
    const response = await api.post(`/api/generate/summary/${trialId}`);
    return response.data;
  },

  generateVideo: async (trialId) => {
    const response = await api.post(`/api/generate/video/${trialId}`);
    return response.data;
  },

  getContentData: async (contentId) => {
    const response = await api.get(`/api/generate/content/${contentId}/data`);
    return response.data;
  },

  updateSummary: async (contentId, text) => {
    const response = await api.put(`/api/generate/content/${contentId}`, {
      content_text: text
    });
    return response.data;
  },
};

export default api;
