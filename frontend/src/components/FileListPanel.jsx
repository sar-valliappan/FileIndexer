'use client';

import { useState, useEffect } from 'react';
import { getIndexedFiles, openFile } from '@/lib/api';

const FileListPanel = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await getIndexedFiles();
      setFiles(data.files);
    } catch (err) {
      console.error('Failed to load files:', err);
      setError('Failed to load indexed files');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenFile = async (filePath) => {
    try {
      await openFile(filePath);
    } catch (error) {
      console.error('Failed to open file:', error);
      alert('Failed to open file: ' + filePath);
    }
  };

  const filteredFiles = files.filter(file => 
    file.file_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    file.file_path.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const sortedFiles = [...filteredFiles].sort((a, b) => {
    let comparison = 0;

    switch (sortBy) {
      case 'name':
        comparison = a.file_name.localeCompare(b.file_name);
        break;
      case 'size':
        comparison = b.file_size - a.file_size;
        break;
      case 'date':
        comparison = new Date(b.modified_time) - new Date(a.modified_time);
        break;
      default:
        comparison = 0;
    }

    return sortOrder === 'asc' ? comparison : -comparison;
  });

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Indexed Files</h2>
        <button
          onClick={loadFiles}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 transition-colors text-sm font-medium"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="mb-4 space-y-3">
        <input
          type="text"
          placeholder="Search files..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
        />
        
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">Sort by:</span>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
          >
            <option value="name">Name</option>
            <option value="size">Size</option>
            <option value="date">Date Modified</option>
          </select>

          <button
            onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm hover:bg-gray-50 transition-colors flex items-center gap-1"
            title={sortOrder === 'asc' ? 'Sort Descending' : 'Sort Ascending'}
          >
            {sortOrder === 'asc' ? (
              <span>↑</span>
            ) : (
              <span>↓</span>
            )}
          </button>
        </div>
      </div>

      {/* File Count */}
      <div className="mb-3 text-sm text-gray-600">
        Showing {sortedFiles.length} of {files.length} files
      </div>

      {/* Files List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
            <p className="text-gray-600 text-sm">Loading files...</p>
          </div>
        </div>
      ) : sortedFiles.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">
            {searchTerm ? 'No files match your search' : 'No files indexed yet'}
          </p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {sortedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 rounded-md border border-gray-200 transition-colors"
            >
              <div className="flex items-center gap-3 flex-1 min-w-0">
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 truncate" title={file.file_name}>
                    {file.file_name}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                    <span>{formatFileSize(file.file_size)}</span>
                    <span>•</span>
                    <span>{file.total_chunks} chunks</span>
                    <span>•</span>
                    <span>{formatDate(file.modified_time)}</span>
                  </div>
                </div>
              </div>
              <div className="flex gap-2 ml-2">
                <button
                  onClick={() => handleOpenFile(file.file_path)}
                  className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-xs font-medium"
                >
                  Open
                </button>
                <button
                  onClick={() => navigator.clipboard.writeText(file.file_path)}
                  className="px-3 py-1 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors text-xs font-medium"
                >
                  Copy Path
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Summary Stats */}
      {files.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-blue-600">{files.length}</p>
              <p className="text-xs text-gray-600">Total Files</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">
                {files.reduce((sum, f) => sum + f.total_chunks, 0)}
              </p>
              <p className="text-xs text-gray-600">Total Chunks</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-purple-600">
                {formatFileSize(files.reduce((sum, f) => sum + f.file_size, 0))}
              </p>
              <p className="text-xs text-gray-600">Total Size</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileListPanel;