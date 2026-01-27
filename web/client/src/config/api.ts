// API Configuration - dynamically determines the backend URL
// In development: uses localhost
// In production (Electron): uses localhost:3001

const isDev = !!(typeof window !== 'undefined' && window.location.hostname === 'localhost');

const API_CONFIG = {
  BASE_URL: isDev ? 'http://localhost:5173' : 'http://localhost:3001',
  API_ENDPOINT: isDev ? 'http://localhost:3001/api' : 'http://localhost:3001/api',
};

export default API_CONFIG;
