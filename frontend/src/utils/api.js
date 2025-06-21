import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance with default configuration
const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('authToken');
      localStorage.removeItem('userData');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API
export const authAPI = {
  login: async (username, password, totpCode = null) => {
    const response = await api.post('/auth/login', {
      username,
      password,
      totp_code: totpCode
    });
    return response.data;
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  setup2FA: async () => {
    const response = await api.post('/auth/setup-2fa');
    return response.data;
  },

  enable2FA: async (totpCode) => {
    const response = await api.post('/auth/enable-2fa', null, {
      params: { totp_code: totpCode }
    });
    return response.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await api.post('/auth/change-password', null, {
      params: { 
        current_password: currentPassword,
        new_password: newPassword 
      }
    });
    return response.data;
  }
};

// Dashboard API
export const dashboardAPI = {
  getStats: async () => {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  getCurrentMetrics: async () => {
    const response = await api.get('/dashboard/metrics/current');
    return response.data;
  },

  getMetricsHistory: async (hours = 24) => {
    const response = await api.get('/dashboard/metrics/history', {
      params: { hours }
    });
    return response.data;
  },

  getActiveSessions: async () => {
    const response = await api.get('/dashboard/sessions/active');
    return response.data;
  },

  getSystemHealth: async () => {
    const response = await api.get('/dashboard/health');
    return response.data;
  },

  getSystemInfo: async () => {
    const response = await api.get('/dashboard/system-info');
    return response.data;
  },

  getTopProcesses: async (limit = 10) => {
    const response = await api.get('/dashboard/processes', {
      params: { limit }
    });
    return response.data;
  }
};

// File Management API
export const filesAPI = {
  listFiles: async (path = '/') => {
    const response = await api.get('/files/list', {
      params: { path }
    });
    return response.data;
  },

  uploadFile: async (file, path = '/', encrypt = true) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', path);
    formData.append('encrypt', encrypt);

    const response = await api.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  downloadFile: async (filePath) => {
    const response = await api.get(`/files/download/${encodeURIComponent(filePath)}`, {
      responseType: 'blob',
    });
    return response;
  },

  deleteFile: async (filePath) => {
    const response = await api.delete('/files/delete', {
      params: { file_path: filePath }
    });
    return response.data;
  },

  createDirectory: async (path) => {
    const response = await api.post('/files/create-directory', null, {
      params: { path }
    });
    return response.data;
  },

  moveFile: async (sourcePath, destPath) => {
    const response = await api.post('/files/move', null, {
      params: { 
        source_path: sourcePath,
        dest_path: destPath 
      }
    });
    return response.data;
  },

  getFileOperations: async (limit = 100) => {
    const response = await api.get('/files/operations', {
      params: { limit }
    });
    return response.data;
  },

  getStorageStats: async () => {
    const response = await api.get('/files/storage-stats');
    return response.data;
  },

  bulkDelete: async (filePaths) => {
    const response = await api.post('/files/bulk-delete', filePaths);
    return response.data;
  },

  searchFiles: async (query, path = '/') => {
    const response = await api.get('/files/search', {
      params: { query, path }
    });
    return response.data;
  }
};

// RDP Management API
export const rdpAPI = {
  createConnection: async (connectionData) => {
    const response = await api.post('/rdp/connections', connectionData);
    return response.data;
  },

  listConnections: async () => {
    const response = await api.get('/rdp/connections');
    return response.data;
  },

  getConnection: async (connectionId) => {
    const response = await api.get(`/rdp/connections/${connectionId}`);
    return response.data;
  },

  terminateConnection: async (connectionId) => {
    const response = await api.delete(`/rdp/connections/${connectionId}`);
    return response.data;
  },

  getConnectionStatus: async (connectionId) => {
    const response = await api.get(`/rdp/connections/${connectionId}/status`);
    return response.data;
  },

  getStatistics: async () => {
    const response = await api.get('/rdp/statistics');
    return response.data;
  },

  takeScreenshot: async (connectionId) => {
    const response = await api.post(`/rdp/connections/${connectionId}/screenshot`);
    return response.data;
  },

  sendKeys: async (connectionId, keys) => {
    const response = await api.post(`/rdp/connections/${connectionId}/send-keys`, null, {
      params: { keys }
    });
    return response.data;
  },

  setClipboard: async (connectionId, content) => {
    const response = await api.post(`/rdp/connections/${connectionId}/clipboard`, null, {
      params: { content }
    });
    return response.data;
  },

  getActiveConnections: async () => {
    const response = await api.get('/rdp/active-connections');
    return response.data;
  }
};

// Session Management API
export const sessionsAPI = {
  getActiveSessions: async () => {
    const response = await api.get('/sessions/active');
    return response.data;
  },

  getSessionHistory: async (limit = 100, days = 30) => {
    const response = await api.get('/sessions/history', {
      params: { limit, days }
    });
    return response.data;
  },

  terminateSession: async (sessionId) => {
    const response = await api.delete(`/sessions/terminate/${sessionId}`);
    return response.data;
  },

  blockIP: async (ipAddress) => {
    const response = await api.post('/sessions/block-ip', null, {
      params: { ip_address: ipAddress }
    });
    return response.data;
  },

  getStatistics: async () => {
    const response = await api.get('/sessions/statistics');
    return response.data;
  },

  getSessionDetails: async (sessionId) => {
    const response = await api.get(`/sessions/${sessionId}`);
    return response.data;
  },

  getSessionsByIP: async (ipAddress, limit = 50) => {
    const response = await api.get(`/sessions/by-ip/${ipAddress}`, {
      params: { limit }
    });
    return response.data;
  }
};

// Logs API
export const logsAPI = {
  getLogs: async (filters = {}) => {
    const response = await api.get('/logs', {
      params: filters
    });
    return response.data;
  },

  getLogLevels: async () => {
    const response = await api.get('/logs/levels');
    return response.data;
  },

  getLogSources: async () => {
    const response = await api.get('/logs/sources');
    return response.data;
  },

  getStatistics: async (days = 7) => {
    const response = await api.get('/logs/statistics', {
      params: { days }
    });
    return response.data;
  },

  clearLogs: async (filters = {}) => {
    const response = await api.delete('/logs/clear', {
      params: filters
    });
    return response.data;
  },

  exportLogs: async (format = 'json', filters = {}) => {
    const response = await api.get('/logs/export', {
      params: { format, ...filters },
      responseType: 'blob'
    });
    return response;
  },

  getRealtimeLogs: async (since = null) => {
    const response = await api.get('/logs/realtime', {
      params: since ? { since } : {}
    });
    return response.data;
  },

  addLogEntry: async (level, source, message, details = null) => {
    const response = await api.post('/logs/add', null, {
      params: { level, source, message, details: JSON.stringify(details) }
    });
    return response.data;
  }
};

// Settings API
export const settingsAPI = {
  getSettings: async () => {
    const response = await api.get('/settings');
    return response.data;
  },

  updateSettings: async (settings) => {
    const response = await api.put('/settings', settings);
    return response.data;
  },

  getSecuritySettings: async () => {
    const response = await api.get('/settings/security');
    return response.data;
  },

  updateSecuritySettings: async (settings) => {
    const response = await api.put('/settings/security', settings);
    return response.data;
  },

  getRDPSettings: async () => {
    const response = await api.get('/settings/rdp');
    return response.data;
  },

  updateRDPSettings: async (settings) => {
    const response = await api.put('/settings/rdp', settings);
    return response.data;
  },

  getFileSettings: async () => {
    const response = await api.get('/settings/files');
    return response.data;
  },

  updateFileSettings: async (settings) => {
    const response = await api.put('/settings/files', settings);
    return response.data;
  },

  getNotificationSettings: async () => {
    const response = await api.get('/settings/notifications');
    return response.data;
  },

  updateNotificationSettings: async (settings) => {
    const response = await api.put('/settings/notifications', settings);
    return response.data;
  },

  getSystemSettings: async () => {
    const response = await api.get('/settings/system');
    return response.data;
  },

  updateSystemSettings: async (settings) => {
    const response = await api.put('/settings/system', settings);
    return response.data;
  },

  resetSettings: async () => {
    const response = await api.post('/settings/reset');
    return response.data;
  },

  backupSettings: async () => {
    const response = await api.get('/settings/backup', {
      responseType: 'blob'
    });
    return response;
  },

  restoreSettings: async (settingsData) => {
    const response = await api.post('/settings/restore', settingsData);
    return response.data;
  }
};

// Health check
export const healthAPI = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  }
};

export default api;