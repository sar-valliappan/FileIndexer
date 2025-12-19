'use client';

import { openFile } from '@/lib/api';

const SearchResult = ({ result, index }) => {
  const fileName = result.file_path.split('/').pop();

  const handleOpen = async () => {
    try {
      await openFile(result.file_path);
    } catch (error) {
      console.error('Failed to open file:', error);
      alert('Failed to open file. You can manually open: ' + result.file_path);
    }
  };

  // Calculate relevance color
  const getRelevanceColor = (distance) => {
    if (!distance) return 'bg-green-100 text-green-800';
    if (distance < 0.3) return 'bg-green-100 text-green-800';
    if (distance < 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-orange-100 text-orange-800';
  };

  const relevanceClass = getRelevanceColor(result.distance);

  return (
    <div className="bg-white rounded-lg shadow-md p-5 hover:shadow-lg transition-shadow border border-gray-200">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-lg text-gray-900 truncate">
              {fileName}
            </h3>
            <p className="text-sm text-gray-500 truncate" title={result.file_path}>
              {result.file_path}
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${relevanceClass}`}>
          {result.distance ? `${(1 - result.distance).toFixed(2)}` : 'High'} Match
        </span>
      </div>

      {/* Content Preview */}
      <div className="mb-3">
        <p className="text-gray-700 text-sm leading-relaxed line-clamp-3">
          {result.chunk_text}
        </p>
      </div>

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
        <span>
          Chunk {result.metadata.chunk_index + 1} of {result.metadata.total_chunks}
        </span>
        <span>
          {(result.metadata.file_size / 1024).toFixed(1)} KB
        </span>
      </div>

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleOpen}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
        >
          Open File
        </button>
        <button
          onClick={() => navigator.clipboard.writeText(result.file_path)}
          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors text-sm font-medium"
        >
          Copy Path
        </button>
      </div>
    </div>
  );
};

const SearchResults = ({ results, query }) => {
  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500 text-lg">
          {query ? 'No results found. Try a different search.' : 'Enter a search query to find files.'}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold text-white-800 mb-4">
        Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
      </h2>
      {results.map((result, index) => (
        <SearchResult key={index} result={result} index={index} />
      ))}
    </div>
  );
};

export default SearchResults;