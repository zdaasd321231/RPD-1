import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  Trash2,
  Play,
  Pause,
  RefreshCw,
  AlertCircle,
  Info,
  AlertTriangle,
  XCircle,
  CheckCircle,
  Clock,
  Server,
  Shield,
  Activity
} from 'lucide-react';
import { mockLogs } from '../utils/mockData';
import { toast } from 'sonner';

const LogsViewer = () => {
  const [logs, setLogs] = useState(mockLogs);
  const [filteredLogs, setFilteredLogs] = useState(mockLogs);
  const [searchTerm, setSearchTerm] = useState('');
  const [levelFilter, setLevelFilter] = useState('ALL');
  const [sourceFilter, setSourceFilter] = useState('ALL');
  const [isAutoRefresh, setIsAutoRefresh] = useState(true);
  const [selectedLog, setSelectedLog] = useState(null);
  const logsEndRef = useRef(null);

  // Simulate real-time log updates
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      const newLog = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        level: ['INFO', 'WARNING', 'ERROR'][Math.floor(Math.random() * 3)],
        source: ['RDP_SERVER', 'AUTH_SERVICE', 'FILE_MANAGER', 'SYSTEM'][Math.floor(Math.random() * 4)],
        message: [
          'Connection established successfully',
          'File transfer completed',
          'Authentication attempt from new IP',
          'System health check completed',
          'Bandwidth usage updated'
        ][Math.floor(Math.random() * 5)],
        details: { random: true }
      };

      setLogs(prev => [newLog, ...prev.slice(0, 99)]); // Keep last 100 logs
    }, 5000);

    return () => clearInterval(interval);
  }, [isAutoRefresh]);

  // Filter logs based on search and filters
  useEffect(() => {
    let filtered = logs;

    if (searchTerm) {
      filtered = filtered.filter(log => 
        log.message.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.source.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    if (levelFilter !== 'ALL') {
      filtered = filtered.filter(log => log.level === levelFilter);
    }

    if (sourceFilter !== 'ALL') {
      filtered = filtered.filter(log => log.source === sourceFilter);
    }

    setFilteredLogs(filtered);
  }, [logs, searchTerm, levelFilter, sourceFilter]);

  // Scroll to bottom when new logs arrive
  useEffect(() => {
    if (isAutoRefresh) {
      logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, isAutoRefresh]);

  const getLevelIcon = (level) => {
    switch (level) {
      case 'ERROR':
        return <XCircle className="w-4 h-4 text-red-400" />;
      case 'WARNING':
        return <AlertTriangle className="w-4 h-4 text-yellow-400" />;
      case 'INFO':
        return <Info className="w-4 h-4 text-blue-400" />;
      default:
        return <CheckCircle className="w-4 h-4 text-green-400" />;
    }
  };

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'WARNING':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'INFO':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      default:
        return 'bg-green-500/20 text-green-400 border-green-500/30';
    }
  };

  const getSourceIcon = (source) => {
    switch (source) {
      case 'RDP_SERVER':
        return <Server className="w-4 h-4 text-purple-400" />;
      case 'AUTH_SERVICE':
        return <Shield className="w-4 h-4 text-green-400" />;
      case 'SYSTEM':
        return <Activity className="w-4 h-4 text-blue-400" />;
      default:
        return <FileText className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('ru-RU');
  };

  const clearLogs = () => {
    setLogs([]);
    toast.success('Логи очищены');
  };

  const exportLogs = () => {
    const dataStr = JSON.stringify(filteredLogs, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `logs_${new Date().toISOString().split('T')[0]}.json`;
    link.click();
    toast.success('Логи экспортированы');
  };

  const uniqueSources = [...new Set(logs.map(log => log.source))];

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Просмотр логов</h1>
          <p className="text-gray-400">Мониторинг событий системы в реальном времени</p>
        </div>
        <div className="flex items-center space-x-4">
          <Badge className={`${isAutoRefresh ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'} border-current/30`}>
            <Activity className="w-3 h-3 mr-1" />
            {isAutoRefresh ? 'Обновление' : 'Пауза'}
          </Badge>
          <span className="text-gray-400 text-sm">
            Всего логов: {logs.length}
          </span>
        </div>
      </div>

      {/* Controls */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-64">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Поиск по логам..."
                  className="pl-10 bg-black/50 border-gray-600 text-white"
                />
              </div>
            </div>

            <select
              value={levelFilter}
              onChange={(e) => setLevelFilter(e.target.value)}
              className="px-3 py-2 bg-black/50 border border-gray-600 rounded-md text-white focus:border-purple-500"
            >
              <option value="ALL">Все уровни</option>
              <option value="ERROR">Ошибки</option>
              <option value="WARNING">Предупреждения</option>
              <option value="INFO">Информация</option>
            </select>

            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="px-3 py-2 bg-black/50 border border-gray-600 rounded-md text-white focus:border-purple-500"
            >
              <option value="ALL">Все источники</option>
              {uniqueSources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>

            <Button
              onClick={() => setIsAutoRefresh(!isAutoRefresh)}
              variant="outline"
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              {isAutoRefresh ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
              {isAutoRefresh ? 'Пауза' : 'Возобновить'}
            </Button>

            <Button
              onClick={exportLogs}
              variant="outline"
              className="border-blue-600 text-blue-400 hover:bg-blue-600/10"
            >
              <Download className="w-4 h-4 mr-2" />
              Экспорт
            </Button>

            <Button
              onClick={clearLogs}
              variant="destructive"
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Очистить
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Log Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {['ERROR', 'WARNING', 'INFO', 'ALL'].map(level => {
          const count = level === 'ALL' 
            ? logs.length 
            : logs.filter(log => log.level === level).length;
          
          return (
            <Card key={level} className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">
                      {level === 'ALL' ? 'Всего' : level}
                    </p>
                    <p className="text-2xl font-bold text-white">{count}</p>
                  </div>
                  {getLevelIcon(level)}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Log List */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <FileText className="w-5 h-5 mr-2 text-purple-400" />
            Журнал событий
            <Badge className="ml-2 bg-purple-500/20 text-purple-400 border-purple-500/30">
              {filteredLogs.length}
            </Badge>
          </CardTitle>
          <CardDescription className="text-gray-400">
            Отфильтровано {filteredLogs.length} из {logs.length} записей
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="max-h-[500px] overflow-y-auto space-y-2">
            {filteredLogs.map((log) => (
              <div
                key={log.id}
                onClick={() => setSelectedLog(selectedLog?.id === log.id ? null : log)}
                className="p-3 rounded-lg border border-gray-700 hover:border-purple-500/40 cursor-pointer transition-colors bg-black/30"
              >
                <div className="flex items-start space-x-3">
                  <div className="flex items-center space-x-2 flex-shrink-0">
                    {getLevelIcon(log.level)}
                    {getSourceIcon(log.source)}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <Badge className={getLevelColor(log.level)}>
                        {log.level}
                      </Badge>
                      <Badge variant="secondary" className="bg-gray-500/20 text-gray-400 border-gray-500/30">
                        {log.source}
                      </Badge>
                      <span className="text-xs text-gray-500 flex items-center">
                        <Clock className="w-3 h-3 mr-1" />
                        {formatTimestamp(log.timestamp)}
                      </span>
                    </div>
                    
                    <p className="text-white text-sm">{log.message}</p>
                    
                    {selectedLog?.id === log.id && log.details && (
                      <div className="mt-3 p-3 bg-gray-800/50 rounded border border-gray-600">
                        <h4 className="text-white font-semibold mb-2">Детали события:</h4>
                        <pre className="text-gray-300 text-xs overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
            
            {filteredLogs.length === 0 && (
              <div className="text-center py-8">
                <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <p className="text-gray-400">
                  {logs.length === 0 ? 'Нет логов' : 'Нет логов, соответствующих фильтрам'}
                </p>
              </div>
            )}
            
            <div ref={logsEndRef} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LogsViewer;