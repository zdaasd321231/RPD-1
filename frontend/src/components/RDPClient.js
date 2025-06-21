import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { 
  Monitor, 
  Play, 
  Square, 
  Maximize2, 
  Volume2, 
  VolumeX,
  Settings,
  Info,
  Wifi,
  WifiOff,
  MousePointer,
  Keyboard
} from 'lucide-react';
import { toast } from 'sonner';

const RDPClient = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionInfo, setConnectionInfo] = useState({
    host: '192.168.1.100',
    port: '3389',
    username: 'Administrator',
    password: '',
    quality: 'high'
  });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [stats, setStats] = useState({
    latency: 25,
    bandwidth: 2.5,
    fps: 30,
    resolution: '1920x1080'
  });

  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  // Simulate connection process
  const handleConnect = async () => {
    if (isConnected) {
      setIsConnected(false);
      toast.success('RDP соединение закрыто');
      return;
    }

    setIsConnecting(true);
    
    // Simulate connection steps
    const steps = [
      'Проверка подключения к хосту...',
      'Установка VPN туннеля...',
      'Аутентификация пользователя...',
      'Инициализация RDP сессии...',
      'Настройка качества видео...',
      'Подключение успешно!'
    ];

    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 800));
      toast.info(steps[i]);
    }

    setIsConnected(true);
    setIsConnecting(false);
    toast.success('RDP подключение установлено');
    
    // Start drawing mock desktop
    drawMockDesktop();
  };

  // Draw mock Windows desktop
  const drawMockDesktop = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = 1920;
    canvas.height = 1080;

    // Draw gradient background
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height);
    gradient.addColorStop(0, '#1e3a8a');
    gradient.addColorStop(1, '#1e40af');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw taskbar
    ctx.fillStyle = '#1f2937';
    ctx.fillRect(0, canvas.height - 60, canvas.width, 60);

    // Draw start button
    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(10, canvas.height - 50, 120, 40);
    ctx.fillStyle = 'white';
    ctx.font = '16px Arial';
    ctx.fillText('Пуск', 25, canvas.height - 25);

    // Draw desktop icons
    const icons = [
      { x: 50, y: 50, name: 'Мой компьютер' },
      { x: 50, y: 150, name: 'Документы' },
      { x: 50, y: 250, name: 'Сеть' }
    ];

    icons.forEach(icon => {
      // Icon background
      ctx.fillStyle = '#374151';
      ctx.fillRect(icon.x, icon.y, 64, 64);
      
      // Icon text
      ctx.fillStyle = 'white';
      ctx.font = '12px Arial';
      ctx.fillText(icon.name, icon.x, icon.y + 80);
    });

    // Simulate cursor
    ctx.fillStyle = 'white';
    ctx.beginPath();
    ctx.moveTo(400, 300);
    ctx.lineTo(400, 320);
    ctx.lineTo(405, 315);
    ctx.lineTo(410, 320);
    ctx.lineTo(415, 315);
    ctx.lineTo(410, 310);
    ctx.lineTo(415, 305);
    ctx.closePath();
    ctx.fill();
  };

  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      containerRef.current?.requestFullscreen();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen();
      setIsFullscreen(false);
    }
  };

  const handleInputChange = (e) => {
    setConnectionInfo({
      ...connectionInfo,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {!isConnected ? (
        <div className="max-w-2xl mx-auto">
          <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
            <CardHeader>
              <CardTitle className="text-white flex items-center">
                <Monitor className="w-6 h-6 mr-3 text-purple-400" />
                RDP Подключение
              </CardTitle>
              <CardDescription className="text-gray-400">
                Настройте параметры подключения к удаленному рабочему столу
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-gray-200">Хост</Label>
                  <Input
                    name="host"
                    value={connectionInfo.host}
                    onChange={handleInputChange}
                    className="bg-black/50 border-gray-600 text-white"
                    placeholder="192.168.1.100"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-200">Порт</Label>
                  <Input
                    name="port"
                    value={connectionInfo.port}
                    onChange={handleInputChange}
                    className="bg-black/50 border-gray-600 text-white"
                    placeholder="3389"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-gray-200">Пользователь</Label>
                  <Input
                    name="username"
                    value={connectionInfo.username}
                    onChange={handleInputChange}
                    className="bg-black/50 border-gray-600 text-white"
                    placeholder="Administrator"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-gray-200">Пароль</Label>
                  <Input
                    name="password"
                    type="password"
                    value={connectionInfo.password}
                    onChange={handleInputChange}
                    className="bg-black/50 border-gray-600 text-white"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-gray-200">Качество</Label>
                <select
                  name="quality"
                  value={connectionInfo.quality}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded-md text-white focus:border-purple-500"
                >
                  <option value="low">Низкое (экономия трафика)</option>
                  <option value="medium">Среднее</option>
                  <option value="high">Высокое</option>
                  <option value="ultra">Ультра (локальная сеть)</option>
                </select>
              </div>

              <div className="flex items-center justify-between p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
                <div className="flex items-center space-x-2">
                  <Info className="w-5 h-5 text-blue-400" />
                  <span className="text-gray-200">Статус безопасности</span>
                </div>
                <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                  <Wifi className="w-3 h-3 mr-1" />
                  VPN активен
                </Badge>
              </div>

              <Button
                onClick={handleConnect}
                disabled={isConnecting}
                className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-3 rounded-lg transition-all duration-300 transform hover:scale-105"
              >
                {isConnecting ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Подключение...</span>
                  </div>
                ) : (
                  <div className="flex items-center space-x-2">
                    <Play className="w-4 h-4" />
                    <span>Подключиться</span>
                  </div>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Connection Controls */}
          <div className="flex items-center justify-between bg-black/60 backdrop-blur-lg rounded-lg p-4 border border-purple-500/20">
            <div className="flex items-center space-x-4">
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                <Wifi className="w-3 h-3 mr-1" />
                Подключено к {connectionInfo.host}
              </Badge>
              <div className="flex items-center space-x-4 text-sm text-gray-400">
                <span>Задержка: {stats.latency}ms</span>
                <span>Скорость: {stats.bandwidth} MB/s</span>
                <span>FPS: {stats.fps}</span>
                <span>Разрешение: {stats.resolution}</span>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setAudioEnabled(!audioEnabled)}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                {audioEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={toggleFullscreen}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <Maximize2 className="w-4 h-4" />
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <Settings className="w-4 h-4" />
              </Button>
              
              <Button
                onClick={handleConnect}
                variant="destructive"
                size="sm"
                className="bg-red-600 hover:bg-red-700"
              >
                <Square className="w-4 h-4 mr-2" />
                Отключить
              </Button>
            </div>
          </div>

          {/* RDP Canvas */}
          <div ref={containerRef} className="relative bg-black rounded-lg overflow-hidden border border-purple-500/20">
            <canvas
              ref={canvasRef}
              className="w-full h-auto max-h-[70vh] cursor-crosshair"
              style={{ imageRendering: 'pixelated' }}
            />
            
            {/* Overlay Controls */}
            <div className="absolute top-4 right-4 flex items-center space-x-2">
              <Badge className="bg-black/80 text-green-400">
                <MousePointer className="w-3 h-3 mr-1" />
                Мышь
              </Badge>
              <Badge className="bg-black/80 text-blue-400">
                <Keyboard className="w-3 h-3 mr-1" />
                Клавиатура
              </Badge>
            </div>
          </div>

          {/* Connection Info */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <Card className="bg-black/40 border-green-500/20 backdrop-blur-lg">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-gray-200">Соединение стабильно</span>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Wifi className="w-4 h-4 text-blue-400" />
                  <span className="text-gray-200">Шифрование: AES-256</span>
                </div>
              </CardContent>
            </Card>
            
            <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Monitor className="w-4 h-4 text-purple-400" />
                  <span className="text-gray-200">Режим: Полный доступ</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
};

export default RDPClient;