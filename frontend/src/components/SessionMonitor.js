import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  Users, 
  Monitor, 
  Globe, 
  Clock, 
  MapPin, 
  Wifi,
  WifiOff,
  Ban,
  AlertTriangle,
  Activity,
  Eye,
  Trash2
} from 'lucide-react';
import { mockActiveSessions, mockConnectionHistory } from '../utils/mockData';
import { toast } from 'sonner';

const SessionMonitor = () => {
  const [activeSessions, setActiveSessions] = useState(mockActiveSessions);
  const [connectionHistory, setConnectionHistory] = useState(mockConnectionHistory);
  const [selectedSession, setSelectedSession] = useState(null);

  // Simulate real-time session updates
  useEffect(() => {
    const interval = setInterval(() => {
      setActiveSessions(prev => prev.map(session => ({
        ...session,
        bandwidth: Math.max(0.1, session.bandwidth + (Math.random() - 0.5) * 0.5)
      })));
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getSessionIcon = (type) => {
    switch (type) {
      case 'RDP':
        return <Monitor className="w-5 h-5 text-purple-400" />;
      case 'Web Panel':
        return <Globe className="w-5 h-5 text-blue-400" />;
      default:
        return <Activity className="w-5 h-5 text-gray-400" />;
    }
  };

  const getSessionDuration = (startTime) => {
    const now = new Date();
    const start = new Date(startTime);
    const diffMs = now - start;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffHours > 0) {
      return `${diffHours}ч ${diffMins % 60}м`;
    }
    return `${diffMins}м`;
  };

  const terminateSession = (sessionId) => {
    setActiveSessions(prev => prev.filter(session => session.id !== sessionId));
    toast.success('Сессия завершена');
  };

  const blockIP = (ip) => {
    toast.success(`IP адрес ${ip} заблокирован`);
  };

  const getCountryFlag = (country) => {
    const flags = {
      'Russia': '🇷🇺',
      'USA': '🇺🇸',
      'Germany': '🇩🇪',
      'France': '🇫🇷',
      'China': '🇨🇳'
    };
    return flags[country] || '🌍';
  };

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Мониторинг сессий</h1>
          <p className="text-gray-400">Отслеживание активных подключений и истории</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <Activity className="w-3 h-3 mr-1" />
            {activeSessions.length} активных
          </Badge>
        </div>
      </div>

      {/* Active Sessions */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <Users className="w-5 h-5 mr-2 text-purple-400" />
            Активные сессии
          </CardTitle>
          <CardDescription className="text-gray-400">
            Текущие подключения к системе в реальном времени
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {activeSessions.map((session) => (
              <div
                key={session.id}
                className="p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-lg border border-purple-500/20 hover:border-purple-500/40 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="flex items-center space-x-2">
                      {getSessionIcon(session.type)}
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    </div>
                    
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-white font-semibold">{session.type}</h3>
                        <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
                          Активна
                        </Badge>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-400 mt-1">
                        <div className="flex items-center space-x-1">
                          <MapPin className="w-3 h-3" />
                          <span>{getCountryFlag(session.country)} {session.ip}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>{getSessionDuration(session.startTime)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Activity className="w-3 h-3" />
                          <span>{session.bandwidth.toFixed(1)} MB/s</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedSession(session)}
                      className="border-gray-600 text-gray-300 hover:bg-gray-700"
                    >
                      <Eye className="w-4 h-4" />
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => blockIP(session.ip)}
                      className="border-yellow-600 text-yellow-400 hover:bg-yellow-600/10"
                    >
                      <Ban className="w-4 h-4" />
                    </Button>
                    
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => terminateSession(session.id)}
                      className="bg-red-600 hover:bg-red-700"
                    >
                      <WifiOff className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {selectedSession?.id === session.id && (
                  <div className="mt-4 p-4 bg-black/30 rounded-lg border border-gray-600">
                    <h4 className="text-white font-semibold mb-2">Детали сессии</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-400">ID сессии:</span>
                        <p className="text-white font-mono">{session.id}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Город:</span>
                        <p className="text-white">{session.city}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Начало сессии:</span>
                        <p className="text-white">{new Date(session.startTime).toLocaleString('ru-RU')}</p>
                      </div>
                      <div>
                        <span className="text-gray-400">Статус:</span>
                        <Badge className="bg-green-500/20 text-green-400 border-green-500/30 mt-1">
                          {session.status}
                        </Badge>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}

            {activeSessions.length === 0 && (
              <div className="text-center py-8">
                <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">Нет активных сессий</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Connection History */}
      <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <Clock className="w-5 h-5 mr-2 text-blue-400" />
            История подключений
          </CardTitle>
          <CardDescription className="text-gray-400">
            Журнал завершенных сессий и подключений
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-gray-600">
                <tr className="text-left">
                  <th className="pb-3 text-gray-300">Тип</th>
                  <th className="pb-3 text-gray-300">IP адрес</th>
                  <th className="pb-3 text-gray-300">Страна</th>
                  <th className="pb-3 text-gray-300">Начало</th>
                  <th className="pb-3 text-gray-300">Окончание</th>
                  <th className="pb-3 text-gray-300">Длительность</th>
                  <th className="pb-3 text-gray-300">Статус</th>
                  <th className="pb-3 text-gray-300"></th>
                </tr>
              </thead>
              <tbody>
                {connectionHistory.map((connection) => (
                  <tr key={connection.id} className="border-b border-gray-700 hover:bg-gray-700/20">
                    <td className="py-3">
                      <div className="flex items-center space-x-2">
                        {getSessionIcon(connection.type)}
                        <span className="text-white">{connection.type}</span>
                      </div>
                    </td>
                    <td className="py-3 text-gray-300 font-mono">{connection.ip}</td>
                    <td className="py-3 text-gray-300">
                      {getCountryFlag(connection.country)} {connection.country}
                    </td>
                    <td className="py-3 text-gray-400 text-sm">
                      {new Date(connection.startTime).toLocaleString('ru-RU')}
                    </td>
                    <td className="py-3 text-gray-400 text-sm">
                      {new Date(connection.endTime).toLocaleString('ru-RU')}
                    </td>
                    <td className="py-3 text-gray-300">{connection.duration}</td>
                    <td className="py-3">
                      <Badge 
                        className={
                          connection.status === 'completed' 
                            ? 'bg-green-500/20 text-green-400 border-green-500/30'
                            : 'bg-red-500/20 text-red-400 border-red-500/30'
                        }
                      >
                        {connection.status === 'completed' ? 'Завершена' : 'Прервана'}
                      </Badge>
                    </td>
                    <td className="py-3">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-gray-400 hover:text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-black/40 border-green-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Активные сессии</p>
                <p className="text-2xl font-bold text-white">{activeSessions.length}</p>
              </div>
              <Users className="w-8 h-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Всего подключений</p>
                <p className="text-2xl font-bold text-white">{connectionHistory.length + activeSessions.length}</p>
              </div>
              <Activity className="w-8 h-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">RDP сессии</p>
                <p className="text-2xl font-bold text-white">
                  {activeSessions.filter(s => s.type === 'RDP').length}
                </p>
              </div>
              <Monitor className="w-8 h-8 text-purple-400" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-black/40 border-yellow-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Средняя длительность</p>
                <p className="text-2xl font-bold text-white">1ч 15м</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-400" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default SessionMonitor;