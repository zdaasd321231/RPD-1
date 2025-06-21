import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Badge } from './ui/badge';
import { Switch } from './ui/switch';
import { 
  Settings as SettingsIcon, 
  Shield, 
  Network, 
  Monitor, 
  FileText,
  Bell,
  Lock,
  Key,
  Globe,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Eye,
  EyeOff,
  Smartphone
} from 'lucide-react';
import { toast } from 'sonner';

const Settings = () => {
  const [settings, setSettings] = useState({
    // Security Settings
    autoLockTimeout: 30,
    requireTwoFactor: true,
    allowedIPs: '192.168.1.0/24, 10.0.0.0/8',
    vpnRequired: true,
    encryptionLevel: 'AES-256',
    
    // RDP Settings
    rdpPort: 3389,
    rdpQuality: 'high',
    audioRedirection: true,
    clipboardSync: true,
    stealthMode: true,
    
    // File Transfer Settings
    maxFileSize: 100,
    allowedExtensions: 'pdf,doc,docx,txt,jpg,png,zip',
    quarantineFiles: true,
    
    // Notification Settings
    emailNotifications: true,
    loginAlerts: true,
    fileTransferAlerts: false,
    systemAlerts: true,
    notificationEmail: 'admin@rdpstealth.com',
    
    // System Settings
    logLevel: 'INFO',
    logRetention: 30,
    autoBackup: true,
    backupInterval: 24
  });

  const [showPasswords, setShowPasswords] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setHasChanges(true);
  };

  const saveSettings = () => {
    // In real app, this would save to backend
    toast.success('Настройки сохранены');
    setHasChanges(false);
  };

  const resetSettings = () => {
    // Reset to default values
    toast.success('Настройки сброшены');
    setHasChanges(false);
  };

  const generateNewKey = () => {
    toast.success('Новый ключ шифрования сгенерирован');
  };

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Настройки</h1>
          <p className="text-gray-400">Конфигурация системы безопасности и параметров</p>
        </div>
        <div className="flex items-center space-x-4">
          {hasChanges && (
            <Badge className="bg-yellow-500/20 text-yellow-400 border-yellow-500/30">
              <AlertTriangle className="w-3 h-3 mr-1" />
              Есть изменения
            </Badge>
          )}
        </div>
      </div>

      {/* Save/Reset Actions */}
      {hasChanges && (
        <Card className="bg-gradient-to-r from-yellow-500/10 to-orange-500/10 border-yellow-500/30 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertTriangle className="w-5 h-5 text-yellow-400" />
                <span className="text-white">У вас есть несохраненные изменения</span>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={resetSettings}
                  variant="outline"
                  className="border-gray-600 text-gray-300 hover:bg-gray-700"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Сбросить
                </Button>
                <Button
                  onClick={saveSettings}
                  className="bg-green-600 hover:bg-green-700"
                >
                  <Save className="w-4 h-4 mr-2" />
                  Сохранить
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Settings */}
        <Card className="bg-black/40 border-red-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Shield className="w-5 h-5 mr-2 text-red-400" />
              Безопасность
            </CardTitle>
            <CardDescription className="text-gray-400">
              Настройки аутентификации и доступа
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-200">Автоблокировка (минуты)</Label>
              <Input
                type="number"
                value={settings.autoLockTimeout}
                onChange={(e) => handleSettingChange('autoLockTimeout', parseInt(e.target.value))}
                className="bg-black/50 border-gray-600 text-white"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Двухфакторная аутентификация</Label>
                <p className="text-xs text-gray-400">Обязательный TOTP код</p>
              </div>
              <Switch
                checked={settings.requireTwoFactor}
                onCheckedChange={(checked) => handleSettingChange('requireTwoFactor', checked)}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-200">Разрешенные IP адреса</Label>
              <Input
                value={settings.allowedIPs}
                onChange={(e) => handleSettingChange('allowedIPs', e.target.value)}
                className="bg-black/50 border-gray-600 text-white"
                placeholder="192.168.1.0/24, 10.0.0.0/8"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Обязательный VPN</Label>
                <p className="text-xs text-gray-400">Блокировать без VPN</p>
              </div>
              <Switch
                checked={settings.vpnRequired}
                onCheckedChange={(checked) => handleSettingChange('vpnRequired', checked)}
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-200">Уровень шифрования</Label>
              <select
                value={settings.encryptionLevel}
                onChange={(e) => handleSettingChange('encryptionLevel', e.target.value)}
                className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded-md text-white focus:border-purple-500"
              >
                <option value="AES-128">AES-128</option>
                <option value="AES-256">AES-256</option>
                <option value="ChaCha20">ChaCha20</option>
              </select>
            </div>

            <Button
              onClick={generateNewKey}
              variant="outline"
              className="w-full border-red-500/20 text-red-400 hover:bg-red-500/10"
            >
              <Key className="w-4 h-4 mr-2" />
              Сгенерировать новый ключ
            </Button>
          </CardContent>
        </Card>

        {/* RDP Settings */}
        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Monitor className="w-5 h-5 mr-2 text-purple-400" />
              RDP Настройки
            </CardTitle>
            <CardDescription className="text-gray-400">
              Конфигурация удаленного рабочего стола
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-200">Порт RDP</Label>
              <Input
                type="number"
                value={settings.rdpPort}
                onChange={(e) => handleSettingChange('rdpPort', parseInt(e.target.value))}
                className="bg-black/50 border-gray-600 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-200">Качество изображения</Label>
              <select
                value={settings.rdpQuality}
                onChange={(e) => handleSettingChange('rdpQuality', e.target.value)}
                className="w-full px-3 py-2 bg-black/50 border border-gray-600 rounded-md text-white focus:border-purple-500"
              >
                <option value="low">Низкое</option>
                <option value="medium">Среднее</option>
                <option value="high">Высокое</option>
                <option value="ultra">Ультра</option>
              </select>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Передача звука</Label>
                <p className="text-xs text-gray-400">Перенаправление аудио</p>
              </div>
              <Switch
                checked={settings.audioRedirection}
                onCheckedChange={(checked) => handleSettingChange('audioRedirection', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Синхронизация буфера</Label>
                <p className="text-xs text-gray-400">Общий буфер обмена</p>
              </div>
              <Switch
                checked={settings.clipboardSync}
                onCheckedChange={(checked) => handleSettingChange('clipboardSync', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Скрытый режим</Label>
                <p className="text-xs text-gray-400">Без уведомлений на экране</p>
              </div>
              <Switch
                checked={settings.stealthMode}
                onCheckedChange={(checked) => handleSettingChange('stealthMode', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* File Transfer Settings */}
        <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <FileText className="w-5 h-5 mr-2 text-blue-400" />
              Передача файлов
            </CardTitle>
            <CardDescription className="text-gray-400">
              Настройки файлового менеджера
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-200">Максимальный размер файла (MB)</Label>
              <Input
                type="number"
                value={settings.maxFileSize}
                onChange={(e) => handleSettingChange('maxFileSize', parseInt(e.target.value))}
                className="bg-black/50 border-gray-600 text-white"
              />
            </div>

            <div className="space-y-2">
              <Label className="text-gray-200">Разрешенные расширения</Label>
              <Input
                value={settings.allowedExtensions}
                onChange={(e) => handleSettingChange('allowedExtensions', e.target.value)}
                className="bg-black/50 border-gray-600 text-white"
                placeholder="pdf,doc,docx,txt,jpg,png"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Карантин файлов</Label>
                <p className="text-xs text-gray-400">Проверка перед загрузкой</p>
              </div>
              <Switch
                checked={settings.quarantineFiles}
                onCheckedChange={(checked) => handleSettingChange('quarantineFiles', checked)}
              />
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="bg-black/40 border-green-500/20 backdrop-blur-lg">
          <CardHeader>
            <CardTitle className="text-white flex items-center">
              <Bell className="w-5 h-5 mr-2 text-green-400" />
              Уведомления
            </CardTitle>
            <CardDescription className="text-gray-400">
              Настройки алертов и оповещений
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label className="text-gray-200">Email для уведомлений</Label>
              <Input
                type="email"
                value={settings.notificationEmail}
                onChange={(e) => handleSettingChange('notificationEmail', e.target.value)}
                className="bg-black/50 border-gray-600 text-white"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Email уведомления</Label>
                <p className="text-xs text-gray-400">Отправлять на почту</p>
              </div>
              <Switch
                checked={settings.emailNotifications}
                onCheckedChange={(checked) => handleSettingChange('emailNotifications', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Алерты входа</Label>
                <p className="text-xs text-gray-400">Уведомления о входе</p>
              </div>
              <Switch
                checked={settings.loginAlerts}
                onCheckedChange={(checked) => handleSettingChange('loginAlerts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Передача файлов</Label>
                <p className="text-xs text-gray-400">Уведомления о файлах</p>
              </div>
              <Switch
                checked={settings.fileTransferAlerts}
                onCheckedChange={(checked) => handleSettingChange('fileTransferAlerts', checked)}
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <Label className="text-gray-200">Системные события</Label>
                <p className="text-xs text-gray-400">Уведомления системы</p>
              </div>
              <Switch
                checked={settings.systemAlerts}
                onCheckedChange={(checked) => handleSettingChange('systemAlerts', checked)}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System Information */}
      <Card className="bg-black/40 border-gray-500/20 backdrop-blur-lg">
        <CardHeader>
          <CardTitle className="text-white flex items-center">
            <SettingsIcon className="w-5 h-5 mr-2 text-gray-400" />
            Информация о системе
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
              <div className="flex items-center space-x-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span className="text-white font-semibold">Статус системы</span>
              </div>
              <p className="text-green-400">Все службы работают</p>
            </div>

            <div className="p-4 bg-blue-500/10 rounded-lg border border-blue-500/20">
              <div className="flex items-center space-x-2 mb-2">
                <Shield className="w-5 h-5 text-blue-400" />
                <span className="text-white font-semibold">Безопасность</span>
              </div>
              <p className="text-blue-400">Высокий уровень</p>
            </div>

            <div className="p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex items-center space-x-2 mb-2">
                <Network className="w-5 h-5 text-purple-400" />
                <span className="text-white font-semibold">Соединение</span>
              </div>
              <p className="text-purple-400">VPN активен</p>
            </div>
          </div>

          <div className="mt-6 p-4 bg-gray-500/10 rounded-lg border border-gray-500/20">
            <h4 className="text-white font-semibold mb-3">Технические детали</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="text-gray-400">Версия:</span>
                <p className="text-white">2.1.0</p>
              </div>
              <div>
                <span className="text-gray-400">Сборка:</span>
                <p className="text-white">20250101</p>
              </div>
              <div>
                <span className="text-gray-400">Архитектура:</span>
                <p className="text-white">x64</p>
              </div>
              <div>
                <span className="text-gray-400">Лицензия:</span>
                <p className="text-white">Enterprise</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Settings;