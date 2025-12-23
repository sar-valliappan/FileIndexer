
# AI File Search

A semantic search engine for local files powered by AI embeddings, enabling natural language queries across your document collection without relying on external APIs or cloud services.

## Project Overview

As developers and knowledge workers accumulate thousands of documents, PDFs, and code files, finding specific information becomes increasingly challenging. Traditional file search relies on exact keyword matching and filename searches, missing the semantic meaning of queries like "machine learning optimization techniques" or "API authentication best practices."

This project solves that problem by implementing a local-first semantic search system that:
- **Understands context**: Search for concepts, not just keywords
- **Preserves privacy**: All processing happens locally using Ollama
- **Works offline**: No API keys or internet connection required
- **Scales efficiently**: Handles thousands of documents with fast retrieval

## Motivation

This project emerged from the practical challenge of managing my files. My files are often disorganized, sitting in one large folder, even though they should ideally be in specific folders. 

I wanted to demonstrate the following skills while also solving a personal problem:

- **Full-stack development skills**: Building a complete application from database to UI
- **AI/ML integration**: Implementing semantic search with vector embeddings
- **System design**: Creating an efficient indexing and retrieval pipeline
- **Modern web development**: Using cutting-edge frameworks (Next.js 14, FastAPI)
- **Problem-solving approach**: Building production-ready solutions for real-world challenges

## Technical Architecture

### Backend Technology Stack

**Python + FastAPI**
- FastAPI for high-performance async API endpoints
- Pydantic for type-safe request/response validation
- Uvicorn ASGI server for production deployment

**Vector Database**
- ChromaDB for persistent embedding storage, built-in HNSW search algorithm and cosine similarity

**AI/ML Pipeline**
- Ollama for local LLM deployment
- nomic-embed-text for generating 768-dimensional embeddings
- Custom chunking algorithm with overlap for context preservation

**Document Processing**
- pypdf for PDF text extraction
- python-docx for Word document parsing
- python-pptx for Powerpoint parsing
- Multi-encoding support for text files (UTF-8, Latin-1, CP1252)

### Frontend Technology Stack

**Next.js + React**
- App Router for file-based routing
- Server Components for optimal performance
- Client Components for interactive search interface

**UI/UX**
- Responsive design with mobile-first approach
- Real-time search with loading states and error handling

**HTTP Client**
- Axios for API communication
- Request/response interceptors for debugging
- Automatic retry logic and error handling

## Core Features Implementation

### 1. Intelligent Document Indexing

**Multi-Format Support**
```python
# Supports: .txt, .pdf, .docx, .md, .pptx (More to be added soon!)
supported_formats = ['.txt', '.pdf', '.docx', '.md', '.pptx']
```

**Smart Text Chunking**
- Configurable chunk size (default: 1000 characters)
- Overlap regions (200 characters) to preserve context at boundaries
- Smart chunking to avoid an extremely short tail chunk
- Sentence-aware splitting to avoid mid-sentence breaks

**Metadata Tracking**
- File path, size, extension, and modification time
- Chunk index and total chunks per file
- File hash for change detection and incremental updates

### 2. Semantic Search Engine

**File-Level Result Aggregation**
- Prevents duplicate results from the same file
- Scoring: average of k-most similar chunks (default: 3)

**Visual Match Indicators**
- Color-coded relevance: Green (>70%), Yellow (>50%), Orange (<50%)
- Percentage-based scoring for clarity

### 3. Real-Time Search Interface

**Search Experience**
- Example queries for user guidance
- Error handling with helpful messages

**Results Display**
- File preview with best matching chunk
- Match percentage and relevance indicators
- One-click file opening in default application
- Copy-to-clipboard for file paths

### 4. Background Indexing System

**Async Processing**
- FastAPI BackgroundTasks for non-blocking indexing
- Progress tracking without blocking search
- Configurable directory exclusions (.git, node_modules, etc.)

**Incremental Updates**
- File hash comparison for change detection
- Selective re-indexing of modified files
- Batch processing for efficiency

## Installation and Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Ollama installed and running

### Backend Setup

```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Pull embedding model
ollama pull nomic-embed-text

# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend
python main.py
# Server runs on http://localhost:8000
```

### Frontend Setup (separate terminal)

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Run development server
npm run dev
# App runs on http://localhost:3000
```

## Usage

### 1. Index Your Files

1. Open the application at `http://localhost:3000`
2. Click "Show Indexing" in the top-right corner
3. Enter an absolute directory path (e.g., `/Users/yourname/Documents`)
4. Click "Start" to begin background indexing
5. Indexing progress shows in the panel

### 2. Search Your Files

1. In the main search bar, enter a natural language query:
   - "Python async functions"
   - "machine learning algorithms"
   - "database normalization techniques"
2. Click "Search" or press Enter
3. View results ranked by relevance
4. Click "Open File" to view the document
5. Use "Copy Path" to get the file location

### 3. Understanding Results

**Match Percentage**: Overall relevance score (0-100%)
- Combines chunk similarity, coverage, and diversity
- Higher percentage = more relevant document

**Color Coding**:
- 🟢 Green: Highly relevant (>70%)
- 🟡 Yellow: Moderately relevant (50-70%)
- 🟠 Orange: Somewhat relevant (<50%)

## Project Structure

```
ai-file-search/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── indexer.py              # File indexing and search logic
│   ├── generate_embeddings.py  # Ollama embedding service
│   ├── file_processor.py       # Document text extraction
│   ├── config.py               # Application configuration
│   ├── requirements.txt        # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.js        # Main application page
│   │   │   ├── layout.js      # Root layout
│   │   │   └── globals.css    # Global styles
│   │   ├── components/
│   │   │   ├── SearchBar.jsx       # Search input component
│   │   │   ├── SearchResults.jsx   # Results display
│   │   │   └── IndexingPanel.jsx   # Indexing controls
│   │   └── lib/
│   │       └── api.js         # API client service
│   ├── package.json
|		├── package-lock.json
|		├── eslint.config.mjs
|		├── postcss.config.mjs
│   ├── jsconfig.json
│   └── next.config.mjs
├── data/
│   └── chroma_db/             # Vector database storage (gitignored)
├── .gitignore
└── README.md

```

## Skills Demonstrated

### Full-Stack Development
- **Backend**: FastAPI, async Python, RESTful API design
- **Frontend**: Next.js, React, modern JavaScript/JSX
- **Database**: Vector database management, query optimization

### AI/ML Engineering
- **Embeddings**: Understanding and implementing vector representations
- **Semantic Search**: Building retrieval systems with similarity metrics
- **Model Integration**: Working with local LLMs (Ollama)

### System Design
- **Scalability**: Efficient indexing for thousands of documents
- **Performance**: Optimized search with approximate nearest neighbors

### Software Engineering Practices
- **Clean Code**: Modular architecture with clear separation of concerns
- **Error Handling**: Comprehensive try-catch blocks and user feedback
- **Documentation**: Clear README
- **Version Control**: Git workflow with meaningful commits

### Problem-Solving
- **File Aggregation**: Preventing duplicate results through smart grouping
- **Scoring Algorithm**: Tuning to find an accurate algorithm
- **Chunking Strategy**: Maintaining context across document segments by overlapping

## Performance Considerations

### Indexing Speed
- **~40ms per chunk**
- Background tasks prevent UI blocking

### Search Speed
- **<1 second** for typical queries
- HNSW algorithm for fast approximate search

### Memory Usage
- **~100MB baseline** for ChromaDB
- **~50KB per indexed chunk** (document + embedding + metadata)
- Efficient for personal document collections (<10,000 files)

## Future Enhancements

### Planned Features
- **Image support**: Index images into the database
- **Improved re-indexing**: Only index changed files, rather than the entire directory
- **Better scoring algorithm**: Add a second layer of sorting to supplement the embedding distance scoring algorithm
- **Advanced filters**: Filter by file type, date range, or location
- **Search history**: Track and revisit previous queries
- **Batch operations**: Index multiple directories simultaneously
- **Export results**: Save search results as JSON/CSV

### UI/UX Enhancements
- **Dark mode**: Theme toggle for user preference
- **Keyboard shortcuts**: Keyboard for quick search access
- **File preview**: In-app document viewer
- **Drag-and-drop**: Visual directory selection
- **Progress visualization**: Real-time indexing statistics

## Contributing

This is a portfolio project, but I'm open to suggestions! If you find bugs or have ideas:

1. Open an issue describing the problem/enhancement
2. Fork the repository
3. Create a feature branch
4. Submit a pull request with clear description

## Contact

Created by Saravanan Natarajan Valliappan
- LinkedIn: linkedin.com/in/saravanan-valliappan
- GitHub: @sar-valliappan

---

**Built with**: Python, FastAPI, Next.js, React, ChromaDB, Ollama
