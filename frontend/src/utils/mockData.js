// Mock authentication system
export const mockAuth = {
  users: [
    {
      id: 1,
      username: 'admin',
      password: 'admin123',
      role: 'administrator',
      email: 'admin@rdpstealth.com',
      lastLogin: new Date().toISOString(),
      totpEnabled: true
    }
  ],

  login: async (username, password, totpCode = null) => {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1000));

    const user = mockAuth.users.find(u => u.username === username);
    
    if (!user || user.password !== password) {
      return { success: false, error: 'Invalid credentials' };
    }

    if (user.totpEnabled && !totpCode) {
      return { success: false, requiresTOTP: true };
    }

    if (user.totpEnabled && totpCode !== '123456') {
      return { success: false, error: 'Invalid TOTP code' };
    }

    const token = 'mock_jwt_token_' + Date.now();
    return {
      success: true,
      user: { ...user, password: undefined },
      token
    };
  }
};

// Mock system metrics
export const mockSystemMetrics = {
  cpu: {
    usage: 45,
    cores: 8,
    temperature: 65
  },
  memory: {
    total: 16384,
    used: 8192,
    available: 8192
  },
  disk: {
    total: 1000,
    used: 450,
    available: 550
  },
  network: {
    uploadSpeed: 125.5,
    downloadSpeed: 87.3,
    totalSent: 2.1,
    totalReceived: 15.7
  }
};

// Mock active sessions
export const mockActiveSessions = [
  {
    id: 'rdp_001',
    type: 'RDP',
    ip: '192.168.1.100',
    country: 'Russia',
    city: 'Moscow',
    startTime: new Date(Date.now() - 1800000).toISOString(),
    status: 'active',
    bandwidth: 2.5
  },
  {
    id: 'web_001',
    type: 'Web Panel',
    ip: '10.0.0.1',
    country: 'Russia',
    city: 'St. Petersburg',
    startTime: new Date(Date.now() - 3600000).toISOString(),
    status: 'active',
    bandwidth: 0.1
  }
];

// Mock connection history
export const mockConnectionHistory = [
  {
    id: 1,
    type: 'RDP',
    ip: '192.168.1.100',
    country: 'Russia',
    startTime: new Date(Date.now() - 7200000).toISOString(),
    endTime: new Date(Date.now() - 3600000).toISOString(),
    duration: '1h 0m',
    status: 'completed'
  },
  {
    id: 2,
    type: 'Web Panel',
    ip: '10.0.0.1',
    country: 'Russia',
    startTime: new Date(Date.now() - 86400000).toISOString(),
    endTime: new Date(Date.now() - 82800000).toISOString(),
    duration: '1h 30m',
    status: 'completed'
  }
];

// Mock file system
export const mockFileSystem = {
  currentPath: 'C:\\',
  files: [
    {
      name: 'Users',
      type: 'folder',
      size: null,
      modified: new Date(Date.now() - 86400000).toISOString(),
      permissions: 'rwx'
    },
    {
      name: 'Program Files',
      type: 'folder',
      size: null,
      modified: new Date(Date.now() - 172800000).toISOString(),
      permissions: 'rwx'
    },
    {
      name: 'Windows',
      type: 'folder',
      size: null,
      modified: new Date(Date.now() - 259200000).toISOString(),
      permissions: 'rwx'
    },
    {
      name: 'documents.pdf',
      type: 'file',
      size: 2048576,
      modified: new Date(Date.now() - 3600000).toISOString(),
      permissions: 'rw-'
    },
    {
      name: 'photo.jpg',
      type: 'file',
      size: 5242880,
      modified: new Date(Date.now() - 7200000).toISOString(),
      permissions: 'rw-'
    }
  ]
};

// Mock logs
export const mockLogs = [
  {
    id: 1,
    timestamp: new Date().toISOString(),
    level: 'INFO',
    source: 'RDP_SERVER',
    message: 'New RDP connection established from 192.168.1.100',
    details: { sessionId: 'rdp_001', ip: '192.168.1.100' }
  },
  {
    id: 2,
    timestamp: new Date(Date.now() - 300000).toISOString(),
    level: 'WARNING',
    source: 'AUTH_SERVICE',
    message: 'Failed login attempt from 192.168.1.99',
    details: { ip: '192.168.1.99', username: 'admin' }
  },
  {
    id: 3,
    timestamp: new Date(Date.now() - 600000).toISOString(),
    level: 'INFO',
    source: 'FILE_MANAGER',
    message: 'File uploaded: documents.pdf (2MB)',
    details: { filename: 'documents.pdf', size: 2048576 }
  },
  {
    id: 4,
    timestamp: new Date(Date.now() - 900000).toISOString(),
    level: 'ERROR',
    source: 'SYSTEM',
    message: 'High CPU usage detected: 89%',
    details: { cpuUsage: 89, threshold: 80 }
  }
];