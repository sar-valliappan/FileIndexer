'use client';

import { useState } from 'react';
import { indexDirectory, getIndexingStatus } from '@/lib/api';


const IndexingPanel = () => {
  const [directory, setDirectory] = useState('');
  const [error, setError] = useState('');
  const [indexingStatus, setIndexingStatus] = useState(null);
  const [stats, setStats] = useState(null);

  const handleStartIndexing = async () => {
    if (!directory.trim()) {
      setError('Please enter a directory path');
      return;
    }

    setError('');
    try {
      await indexDirectory(directory);
      setDirectory('');
    } catch (err) {
        const detail = err.response?.data?.detail;

        if (Array.isArray(detail)) {
          setError(detail.map(d => d.msg).join(', '));
        } else if (typeof detail === 'string') {
          setError(detail);
        } else {
          setError('Failed to start indexing');
        }
    }
  };

  const getProgressPercentage = () => {
    if (!indexingStatus || !indexingStatus.total) return 0;
    return Math.round((indexingStatus.progress / indexingStatus.total) * 100);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
      <h2 className="text-2xl font-bold text-gray-800 mb-4">Index Files</h2>

      {/* Directory Input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Directory Path
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={directory}
            onChange={(e) => setDirectory(e.target.value)}
            placeholder="/Users/yourname/Documents"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={indexingStatus?.is_indexing}
          />
          <button
            onClick={handleStartIndexing}
            disabled={indexingStatus?.is_indexing || !directory.trim()}
            className="px-6 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {indexingStatus?.is_indexing ? 'Indexing...' : 'Start'}
          </button>
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-600">{error}</p>
        )}
      </div>

      {/* Indexing Progress */}
      {indexingStatus?.is_indexing && (
        <div className="mb-4 p-4 bg-blue-50 rounded-md border border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-blue-900">
              Indexing in progress...
            </span>
            <span className="text-sm font-semibold text-blue-900">
              {getProgressPercentage()}%
            </span>
          </div>
          <div className="w-full bg-blue-200 rounded-full h-2 mb-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
          <div className="text-xs text-blue-700">
            <p className="truncate">
              {indexingStatus.progress} / {indexingStatus.total} files
            </p>
            <p className="truncate mt-1" title={indexingStatus.current_file}>
              Current: {indexingStatus.current_file.split('/').pop()}
            </p>
          </div>
        </div>
      )}

      {/* Last Result */}
      {indexingStatus?.last_result && !indexingStatus?.is_indexing && (
        <div className="mb-4 p-4 bg-green-50 rounded-md border border-green-200">
          <h3 className="text-sm font-semibold text-green-900 mb-2">
            ✓ Indexing Complete
          </h3>
          <div className="text-sm text-green-700 space-y-1">
            <p>Total files: {indexingStatus.last_result.total_files}</p>
            <p>Successful: {indexingStatus.last_result.successful}</p>
            <p>Failed: {indexingStatus.last_result.failed}</p>
            <p>Total chunks: {indexingStatus.last_result.collection_count}</p>
          </div>
        </div>
      )}

      {/* Quick Tips */}
      <div className="mt-4 p-3 bg-yellow-50 rounded-md border border-yellow-200">
        <p className="text-xs text-yellow-800">
          <strong>💡 Tips:</strong> Use absolute paths like <code className="bg-yellow-100 px-1 rounded">/Users/name/Documents</code> or expand ~ like <code className="bg-yellow-100 px-1 rounded">$HOME/Documents</code>
        </p>
      </div>
    </div>
  );
};

export default IndexingPanel;