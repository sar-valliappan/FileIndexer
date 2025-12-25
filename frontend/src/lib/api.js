import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const indexDirectory = async (directory) => {
  const response = await api.post('/api/index', { directory });
  return response.data;
};

export const getIndexingStatus = async () => {
  const response = await api.get('/api/index/status');
  return response.data;
};

export const searchFiles = async (query, nResults = 10) => {
  const response = await api.post('/api/search', {
    query,
    n_results: nResults,
  });
  return response.data;
};

export const openFile = async (filePath) => {
  const response = await api.post('/api/open-file', null, {
    params: { file_path: filePath },
  });
  return response.data;
};

export const getIndexedFiles = async () => {
  const response = await api.get('/api/files');
  return response.data;
};