import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { AlertCircle, Shield, Lock, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const LoginPage = () => {
  const { login, loading } = useAuth();
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    totpCode: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [requiresTOTP, setRequiresTOTP] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const result = await login(formData.username, formData.password, formData.totpCode);
    
    if (result.success) {
      toast.success('Успешная авторизация');
    } else if (result.requiresTOTP) {
      setRequiresTOTP(true);
      toast.info('Введите код двухфакторной аутентификации');
    } else {
      toast.error(result.error || 'Ошибка авторизации');
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/20 backdrop-blur-sm"></div>
      
      <Card className="w-full max-w-md relative z-10 bg-black/40 backdrop-blur-lg border-purple-500/20 shadow-2xl">
        <CardHeader className="text-center space-y-2">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded-full flex items-center justify-center mb-4 shadow-lg">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl font-bold text-white">Stealth RDP Access</CardTitle>
          <CardDescription className="text-gray-300">
            Безопасный доступ к панели управления
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="username" className="text-gray-200">Имя пользователя</Label>
              <Input
                id="username"
                name="username"
                type="text"
                value={formData.username}
                onChange={handleInputChange}
                className="bg-black/50 border-gray-600 text-white focus:border-purple-500 transition-colors"
                placeholder="admin"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-gray-200">Пароль</Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  value={formData.password}
                  onChange={handleInputChange}
                  className="bg-black/50 border-gray-600 text-white focus:border-purple-500 pr-10 transition-colors"
                  placeholder="admin123"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {requiresTOTP && (
              <div className="space-y-2">
                <Label htmlFor="totpCode" className="text-gray-200">Код 2FA</Label>
                <Input
                  id="totpCode"
                  name="totpCode"
                  type="text"
                  value={formData.totpCode}
                  onChange={handleInputChange}
                  className="bg-black/50 border-gray-600 text-white focus:border-purple-500 transition-colors"
                  placeholder="123456"
                  maxLength={6}
                  required
                />
                <p className="text-xs text-gray-400">
                  Для демо используйте код: 123456
                </p>
              </div>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white font-semibold py-3 rounded-lg transition-all duration-300 transform hover:scale-105 shadow-lg"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Авторизация...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <Lock className="w-4 h-4" />
                  <span>Войти</span>
                </div>
              )}
            </Button>
          </form>

          <div className="mt-6 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
            <div className="flex items-start space-x-2">
              <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-yellow-200">
                <p className="font-semibold mb-1">Демо данные:</p>
                <p>Логин: admin</p>
                <p>Пароль: admin123</p>
                <p>2FA код: 123456</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default LoginPage;