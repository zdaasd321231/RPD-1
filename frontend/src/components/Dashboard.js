import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  Cpu, 
  HardDrive, 
  Wifi, 
  MemoryStick, 
  Activity,
  Users,
  Shield,
  AlertTriangle,
  CheckCircle,
  Server,
  Globe,
  Zap,
  RefreshCw
} from 'lucide-react';
import { dashboardAPI } from '../utils/api';
import { toast } from 'sonner';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [loading, setLoading] = useState(true);

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      const [statsData, metricsData, sessionsData] = await Promise.all([
        dashboardAPI.getStats(),
        dashboardAPI.getCurrentMetrics(),
        dashboardAPI.getActiveSessions()
      ]);

      setStats(statsData);
      setMetrics(metricsData);
      setSessions(sessionsData.sessions || []);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  // Real-time updates
  useEffect(() => {
    loadDashboardData();

    const interval = setInterval(() => {
      loadDashboardData();
    }, 30000); // Update every 30 seconds

    return () => clearInterval(interval);
  }, []);

  const refreshData = () => {
    setLoading(true);
    loadDashboardData();
  };

  if (loading && !stats) {
    return (
      <div className="p-6 space-y-6 min-h-screen">
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-2 border-purple-400 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </div>
    );
  }

  const getStatusColor = (value, thresholds) => {
    if (value >= thresholds.danger) return 'text-red-400';
    if (value >= thresholds.warning) return 'text-yellow-400';
    return 'text-green-400';
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };


  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Панель управления</h1>
          <p className="text-gray-400">Мониторинг системы и активных подключений</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="text-sm text-gray-400">
            Обновлено: {lastUpdate.toLocaleTimeString()}
          </div>
          <Button
            onClick={refreshData}
            variant="outline"
            size="sm"
            className="border-purple-500/20 text-purple-400 hover:bg-purple-500/10"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Обновить
          </Button>
        </div>
      </div>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-200">Процессор</CardTitle>
            <Cpu className="h-4 w-4 text-purple-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white mb-2">
              {metrics ? Math.round(metrics.cpu_usage) : 0}%
            </div>
            <Progress 
              value={metrics ? metrics.cpu_usage : 0} 
              className="mb-2"
              style={{'--progress-foreground': (metrics?.cpu_usage || 0) > 80 ? 'rgb(248 113 113)' : (metrics?.cpu_usage || 0) > 60 ? 'rgb(251 191 36)' : 'rgb(34 197 94)'}}
            />
            <p className="text-xs text-gray-400">
              {metrics?.cpu_temperature ? `${metrics.cpu_temperature}°C` : 'Temp: N/A'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-200">Память</CardTitle>
            <MemoryStick className="h-4 w-4 text-blue-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white mb-2">
              {metrics ? Math.round((metrics.memory_used / metrics.memory_total) * 100) : 0}%
            </div>
            <Progress 
              value={metrics ? (metrics.memory_used / metrics.memory_total) * 100 : 0} 
              className="mb-2"
            />
            <p className="text-xs text-gray-400">
              {metrics ? `${formatBytes(metrics.memory_used * 1024 * 1024)} / ${formatBytes(metrics.memory_total * 1024 * 1024)}` : 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-200">Диск</CardTitle>
            <HardDrive className="h-4 w-4 text-green-400" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-white mb-2">
              {metrics ? Math.round((metrics.disk_used / metrics.disk_total) * 100) : 0}%
            </div>
            <Progress 
              value={metrics ? (metrics.disk_used / metrics.disk_total) * 100 : 0} 
              className="mb-2"
            />
            <p className="text-xs text-gray-400">
              {metrics ? `${metrics.disk_used}GB / ${metrics.disk_total}GB` : 'N/A'}
            </p>
          </CardContent>
        </Card>

        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-200">Сеть</CardTitle>
            <Wifi className="h-4 w-4 text-cyan-400" />
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-white mb-2">
              ↑ {metrics ? metrics.network_upload_speed.toFixed(1) : '0.0'} KB/s
            </div>
            <div className="text-lg font-bold text-white mb-2">
              ↓ {metrics ? metrics.network_download_speed.toFixed(1) : '0.0'} KB/s
            </div>
            <p className="text-xs text-gray-400">
              Отправлено: {metrics ? metrics.network_total_sent : '0'}GB
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Active Sessions and System Status */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Users className="w-5 h-5 mr-2 text-purple-400" />
              Активные сессии
            </CardTitle>
            <CardDescription className="text-gray-400">
              Текущие подключения к системе
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {sessions.map((session) => (
                <div key={session.id} className="flex items-center justify-between p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                  <div className="flex items-center space-x-3">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <div>
                      <p className="text-white font-medium">{session.session_type}</p>
                      <p className="text-gray-400 text-sm">{session.ip_address} • {session.country || 'Unknown'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-white text-sm">
                      {session.duration_seconds ? Math.floor(session.duration_seconds / 60) : 0}m
                    </p>
                    <p className="text-gray-400 text-xs">
                      {session.bandwidth_used || 0} MB/s
                    </p>
                  </div>
                </div>
              ))}
              
              {sessions.length === 0 && (
                <div className="text-center py-4">
                  <Users className="w-12 h-12 text-gray-600 mx-auto mb-2" />
                  <p className="text-gray-400">Нет активных сессий</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Shield className="w-5 h-5 mr-2 text-green-400" />
              Статус системы
            </CardTitle>
            <CardDescription className="text-gray-400">
              Состояние служб и безопасности
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { name: 'RDP Сервер', status: 'active', icon: Server },
                { name: 'Веб-панель', status: 'active', icon: Globe },
                { name: 'Файловый сервер', status: 'active', icon: HardDrive },
                { name: 'VPN Туннель', status: 'active', icon: Shield },
                { name: 'Мониторинг', status: 'active', icon: Activity }
              ].map((service) => (
                <div key={service.name} className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg border border-green-500/20">
                  <div className="flex items-center space-x-3">
                    <service.icon className="w-4 h-4 text-green-400" />
                    <span className="text-white">{service.name}</span>
                  </div>
                  <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Работает
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <Zap className="w-5 h-5 mr-2 text-yellow-400" />
            Быстрые действия
          </CardTitle>
          <CardDescription className="text-gray-400">
            Управление системой одним кликом
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button 
              variant="outline" 
              className="h-20 flex-col space-y-2 border-purple-500/20 hover:bg-purple-500/10 text-white"
            >
              <Monitor className="w-6 h-6 text-purple-400" />
              <span>Открыть RDP</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-20 flex-col space-y-2 border-blue-500/20 hover:bg-blue-500/10 text-white"
            >
              <Users className="w-6 h-6 text-blue-400" />
              <span>Сессии</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-20 flex-col space-y-2 border-green-500/20 hover:bg-green-500/10 text-white"
            >
              <HardDrive className="w-6 h-6 text-green-400" />
              <span>Файлы</span>
            </Button>
            
            <Button 
              variant="outline" 
              className="h-20 flex-col space-y-2 border-red-500/20 hover:bg-red-500/10 text-white"
            >
              <AlertTriangle className="w-6 h-6 text-red-400" />
              <span>Перезагрузка</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;