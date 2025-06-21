import React, { useState, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  FolderOpen, 
  File, 
  Upload, 
  Download, 
  Trash2, 
  MoreVertical,
  ArrowLeft,
  Search,
  Grid,
  List,
  Lock,
  Unlock,
  FileText,
  Image,
  Archive,
  Folder
} from 'lucide-react';
import { mockFileSystem } from '../utils/mockData';
import { toast } from 'sonner';

const FileManager = () => {
  const [currentPath, setCurrentPath] = useState(mockFileSystem.currentPath);
  const [files, setFiles] = useState(mockFileSystem.files);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [viewMode, setViewMode] = useState('grid');
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const getFileIcon = (file) => {
    if (file.type === 'folder') return <Folder className="w-6 h-6 text-yellow-400" />;
    
    const extension = file.name.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf':
      case 'doc':
      case 'docx':
      case 'txt':
        return <FileText className="w-6 h-6 text-blue-400" />;
      case 'jpg':
      case 'jpeg':
      case 'png':
      case 'gif':
        return <Image className="w-6 h-6 text-green-400" />;
      case 'zip':
      case 'rar':
      case '7z':
        return <Archive className="w-6 h-6 text-purple-400" />;
      default:
        return <File className="w-6 h-6 text-gray-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return '-';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('ru-RU');
  };

  const handleFileSelect = (fileName) => {
    setSelectedFiles(prev => 
      prev.includes(fileName) 
        ? prev.filter(name => name !== fileName)
        : [...prev, fileName]
    );
  };

  const handleFileUpload = (uploadedFiles) => {
    setIsUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsUploading(false);
          
          // Add uploaded files to the file list
          const newFiles = Array.from(uploadedFiles).map(file => ({
            name: file.name,
            type: 'file',
            size: file.size,
            modified: new Date().toISOString(),
            permissions: 'rw-'
          }));
          
          setFiles(prevFiles => [...prevFiles, ...newFiles]);
          toast.success(`Загружено файлов: ${uploadedFiles.length}`);
          return 100;
        }
        return prev + 10;
      });
    }, 200);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      handleFileUpload(droppedFiles);
    }
  };

  const handleDownload = () => {
    if (selectedFiles.length === 0) {
      toast.error('Выберите файлы для скачивания');
      return;
    }
    
    toast.success(`Начато скачивание ${selectedFiles.length} файлов`);
    setSelectedFiles([]);
  };

  const handleDelete = () => {
    if (selectedFiles.length === 0) {
      toast.error('Выберите файлы для удаления');
      return;
    }
    
    setFiles(prev => prev.filter(file => !selectedFiles.includes(file.name)));
    toast.success(`Удалено файлов: ${selectedFiles.length}`);
    setSelectedFiles([]);
  };

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Файловый менеджер</h1>
          <p className="text-gray-400">Управление файлами удаленной системы</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
            <Lock className="w-3 h-3 mr-1" />
            Шифрование активно
          </Badge>
        </div>
      </div>

      {/* Toolbar */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="outline"
                size="sm"
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Назад
              </Button>
              
              <div className="text-gray-300 font-mono bg-black/50 px-3 py-1 rounded border border-gray-600">
                {currentPath}
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('grid')}
                className="border-gray-600"
              >
                <Grid className="w-4 h-4" />
              </Button>
              
              <Button
                variant={viewMode === 'list' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setViewMode('list')}
                className="border-gray-600"
              >
                <List className="w-4 h-4" />
              </Button>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <Input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Поиск файлов..."
                className="pl-10 bg-black/50 border-gray-600 text-white"
              />
            </div>

            <Button
              onClick={() => fileInputRef.current?.click()}
              className="bg-purple-600 hover:bg-purple-700"
            >
              <Upload className="w-4 h-4 mr-2" />
              Загрузить
            </Button>

            <Button
              onClick={handleDownload}
              variant="outline"
              disabled={selectedFiles.length === 0}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              <Download className="w-4 h-4 mr-2" />
              Скачать ({selectedFiles.length})
            </Button>

            <Button
              onClick={handleDelete}
              variant="destructive"
              disabled={selectedFiles.length === 0}
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Удалить
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {isUploading && (
        <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white">Загрузка файлов...</span>
              <span className="text-gray-400">{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="mb-2" />
            <p className="text-sm text-gray-400">
              Файлы шифруются перед передачей
            </p>
          </CardContent>
        </Card>
      )}

      {/* File Grid/List */}
      <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
        <CardContent className="p-4">
          <div
            className={`${dragOver ? 'border-purple-500 bg-purple-500/10' : 'border-gray-600'} border-2 border-dashed rounded-lg transition-colors`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            {viewMode === 'grid' ? (
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 p-4">
                {filteredFiles.map((file) => (
                  <div
                    key={file.name}
                    onClick={() => handleFileSelect(file.name)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all hover:scale-105 ${
                      selectedFiles.includes(file.name)
                        ? 'border-purple-500 bg-purple-500/20'
                        : 'border-gray-600 bg-black/50 hover:bg-gray-700/50'
                    }`}
                  >
                    <div className="flex flex-col items-center space-y-2">
                      {getFileIcon(file)}
                      <span className="text-white text-sm text-center truncate w-full">
                        {file.name}
                      </span>
                      {file.type === 'file' && (
                        <span className="text-gray-400 text-xs">
                          {formatFileSize(file.size)}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="border-b border-gray-600">
                    <tr className="text-left">
                      <th className="pb-2 text-gray-300">Название</th>
                      <th className="pb-2 text-gray-300">Размер</th>
                      <th className="pb-2 text-gray-300">Изменен</th>
                      <th className="pb-2 text-gray-300">Права</th>
                      <th className="pb-2 text-gray-300"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredFiles.map((file) => (
                      <tr
                        key={file.name}
                        onClick={() => handleFileSelect(file.name)}
                        className={`border-b border-gray-700 cursor-pointer hover:bg-gray-700/50 ${
                          selectedFiles.includes(file.name) ? 'bg-purple-500/20' : ''
                        }`}
                      >
                        <td className="py-3">
                          <div className="flex items-center space-x-3">
                            {getFileIcon(file)}
                            <span className="text-white">{file.name}</span>
                          </div>
                        </td>
                        <td className="py-3 text-gray-400">
                          {formatFileSize(file.size)}
                        </td>
                        <td className="py-3 text-gray-400">
                          {formatDate(file.modified)}
                        </td>
                        <td className="py-3 text-gray-400 font-mono">
                          {file.permissions}
                        </td>
                        <td className="py-3">
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {dragOver && (
              <div className="absolute inset-0 flex items-center justify-center bg-purple-500/20 backdrop-blur-sm rounded-lg">
                <div className="text-center">
                  <Upload className="w-12 h-12 text-purple-400 mx-auto mb-4" />
                  <p className="text-white text-lg font-semibold">
                    Перетащите файлы сюда
                  </p>
                  <p className="text-gray-400">
                    Файлы будут автоматически зашифрованы
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Storage Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-black/40 border-green-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-200">Выбрано файлов</span>
              <span className="text-white font-bold">{selectedFiles.length}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-black/40 border-blue-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-200">Всего файлов</span>
              <span className="text-white font-bold">{files.length}</span>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-black/40 border-purple-500/20 backdrop-blur-lg">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-200">Безопасность</span>
              <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                <Lock className="w-3 h-3 mr-1" />
                AES-256
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        onChange={(e) => e.target.files && handleFileUpload(e.target.files)}
      />
    </div>
  );
};

export default FileManager;