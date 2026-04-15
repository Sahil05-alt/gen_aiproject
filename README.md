# DocMind

DocMind is a full-stack RAG application for chatting with uploaded documents through a grounded, citation-aware interface. It combines a FastAPI backend, a React frontend, FAISS vector search, and Groq-hosted LLM responses so you can upload files, index them locally, and ask questions against one or more selected documents.

The project is designed for local development and experimentation. You can upload `.pdf`, `.docx`, and `.txt` files, stream answers in real time, clear session history, export chat transcripts as PDF, and generate multiple-choice quizzes from retrieved context.

## What It Does

- Uploads supported documents through a simple web UI
- Parses files and splits them into retrieval-friendly chunks
- Embeds chunks with `sentence-transformers/all-MiniLM-L6-v2`
- Stores each document in its own FAISS index on disk
- Lets you select one or many indexed documents before asking a question
- Retrieves relevant chunks with MMR-based search
- Streams answers token by token from Groq
- Shows citations and a lightweight confidence score with each answer
- Keeps short session-scoped chat memory in memory
- Exports the conversation as a PDF transcript
- Generates quizzes from the latest retrieved citation context

## Demo Workflow

1. Start the backend and frontend.
2. Open the app in the browser.
3. Upload a `.pdf`, `.docx`, or `.txt` file.
4. Wait for the document status to change from `processing` to `indexed`.
5. Select one or more indexed documents from the sidebar.
6. Ask a question in natural language.
7. Review the streamed answer, inline citations, and confidence score.
8. Optionally clear history, export the chat as PDF, or generate a quiz.

## Tech Stack

- Frontend: React 18, Vite, Tailwind CSS
- Backend: FastAPI, Uvicorn
- Retrieval: LangChain, FAISS, MMR retrieval
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- LLM: Groq via `langchain-groq`
- Parsing: `pypdf`, `docx2txt`, `TextLoader`

## Architecture Overview

DocMind uses a straightforward retrieval pipeline:

1. The frontend uploads a file to `POST /api/documents/upload`.
2. The backend stores the raw file in `backend/data/uploads`.
3. A background task parses the file and splits it into chunks using `RecursiveCharacterTextSplitter`.
4. Each chunk is enriched with metadata such as document ID, document name, chunk index, and source path.
5. Embeddings are generated and saved into a FAISS index under `backend/data/vectorstore/<doc_id>`.
6. When a user asks a question, the backend loads the selected document indexes and merges them when needed.
7. The retriever performs MMR search to reduce duplicate context and improve coverage.
8. Retrieved chunks are formatted into a grounded prompt and sent to Groq.
9. The answer is streamed back to the frontend with citation metadata and a confidence estimate.

## Key Features

### 1. Multi-document chat

You can select several indexed documents at once. At query time, DocMind loads the corresponding FAISS indexes, merges them if needed, and retrieves across the combined result set.

### 2. Streaming answers

The frontend consumes a server-sent event stream from `POST /api/chat/stream` and progressively updates the assistant message as tokens arrive.

### 3. Grounded citations

Each answer includes structured citation metadata with:

- document name
- chunk index
- excerpt
- source path

The model prompt explicitly instructs the assistant to answer only from retrieved context and to use inline citations.

### 4. Session memory

DocMind stores recent turns in an in-memory session dictionary keyed by a browser-generated session ID stored in `localStorage`. This lets follow-up questions reuse prior chat context during the same backend process.

### 5. PDF export

The chat transcript can be exported as a downloadable PDF using `POST /api/export-pdf`.

### 6. Quiz generation

The frontend can send retrieved citation text to `POST /api/generate-quiz` to generate multiple-choice questions from the most recent grounded context.

## Repository Structure

```text
docmind/
├── backend/
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/
│   │   ├── uploads/
│   │   └── vectorstore/
│   ├── routers/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   └── health.py
│   └── services/
│       ├── embeddings.py
│       ├── export_pdf.py
│       ├── ingestion.py
│       ├── quiz.py
│       └── rag.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── index.css
│       ├── main.jsx
│       ├── components/
│       │   ├── CitationCard.jsx
│       │   ├── ChatInput.jsx
│       │   ├── ChatMessage.jsx
│       │   ├── EmptyState.jsx
│       │   ├── ExportPDFButton.jsx
│       │   └── QuizGenerator.jsx
│       └── utils/
│           └── api.js
└── README.md
```

## Backend Components

### `backend/main.py`

- boots the FastAPI app
- registers CORS for local frontend ports
- mounts the health, document, and chat routers

### `backend/routers/documents.py`

- validates uploaded file types
- saves files to disk
- starts ingestion in a background task
- exposes list, status, and delete endpoints
- maintains an in-memory document registry

### `backend/routers/chat.py`

- provides standard and streaming chat endpoints
- clears session history
- handles PDF export
- exposes quiz generation

### `backend/services/ingestion.py`

- picks the correct loader based on file extension
- chunks parsed content using `RecursiveCharacterTextSplitter`
- writes metadata-rich chunks into FAISS
- merges vector stores across selected documents when retrieving

### `backend/services/rag.py`

- manages in-memory chat sessions
- builds grounded prompts from retrieved chunks
- calls Groq through LangChain
- streams SSE token events to the frontend
- computes a simple confidence score from retrieved chunk count

## Frontend Components

### `frontend/src/App.jsx`

The main UI manages:

- uploaded document state
- indexed document selection
- streaming chat messages
- session persistence through `localStorage`
- export and quiz actions
- mobile sidebar visibility

### `frontend/src/utils/api.js`

Contains lightweight wrappers for all frontend API calls:

- document upload, list, status, delete
- chat and streaming chat
- clear history
- PDF export
- quiz generation
- health check

## Supported File Types

- `.pdf`
- `.docx`
- `.txt`

Unsupported extensions are rejected by the backend before ingestion begins.

## Prerequisites

- Python `3.10+`
- Node.js `18+`
- npm
- A valid Groq API key

## Environment Variables

Copy the provided example file:

```bash
cd backend
cp .env.example .env
```

Then update `backend/.env`:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=5
VECTOR_STORE_PATH=./data/vectorstore
UPLOADS_PATH=./data/uploads
METADATA_PATH=./data/metadata
CORS_ORIGINS=http://localhost:5173,http://localhost:5174,http://localhost:3000
```

### Variable Reference

- `GROQ_API_KEY`: required API key for Groq
- `GROQ_MODEL`: model name used for answer generation
- `EMBEDDING_MODEL`: sentence-transformers model used for chunk embeddings
- `CHUNK_SIZE`: max chunk size used during ingestion
- `CHUNK_OVERLAP`: overlap between adjacent chunks
- `TOP_K`: default number of retrieved chunks
- `VECTOR_STORE_PATH`: folder where FAISS indexes are stored
- `UPLOADS_PATH`: folder where raw uploaded files are stored
- `METADATA_PATH`: folder where persisted document metadata JSON is stored
- `CORS_ORIGINS`: comma-separated or JSON array list of allowed frontend origins

## Installation

### Backend setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend setup

```bash
cd frontend
npm install
```

If you use `nvm` for Node:

```bash
source ~/.nvm/nvm.sh
nvm use
```

## Running Locally

Run the backend and frontend in separate terminals.

### Terminal 1: backend

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend will be available at `http://localhost:8000`.

### Terminal 2: frontend

```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use
npm run dev -- --host 0.0.0.0
```

Frontend will be available at `http://localhost:5173`.

The frontend uses a Vite proxy, so requests to `/api` are forwarded to `http://localhost:8000`.

## Deploying

### Frontend on Vercel

This repository is now configured so the React frontend can be deployed directly from the repo root on Vercel using [vercel.json](/home/sahil05/Documents/docmind/vercel.json).

Before deploying, add this environment variable in your Vercel project:

```env
VITE_API_BASE_URL=https://your-backend.example.com/api
```

Vercel will:

- install frontend dependencies from `frontend/package-lock.json`
- build the Vite app from `frontend/`
- publish `frontend/dist` as the production output

### Why the backend should not be deployed to Vercel as-is

The current FastAPI backend is not a good fit for Vercel serverless functions because it:

- writes uploads and FAISS indexes to the local filesystem
- relies on in-memory registries and session history
- loads heavy packages such as `torch`, `sentence-transformers`, and `faiss-cpu`
- expects long-lived local storage for uploaded files and vector indexes

For production, the recommended setup is:

1. Deploy the frontend to Vercel.
2. Deploy the FastAPI backend to a persistent Python host such as Render, Railway, Fly.io, or a VM/container.
3. Point `VITE_API_BASE_URL` at that backend's `/api` base URL.

### Backend on Render

This repo now includes [render.yaml](/home/sahil05/Documents/docmind/render.yaml) for the FastAPI backend. It configures:

- a Python web service rooted at `backend/`
- `uvicorn main:app` as the start command
- `/api/health` as the health check
- a persistent disk mounted at `/var/data/docmind`
- environment variables for uploads, vector indexes, metadata, and CORS

To deploy the backend on Render:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint or Web Service from the repo.
3. Let Render read `render.yaml`.
4. Set `GROQ_API_KEY` in the Render dashboard.
5. Set `CORS_ORIGINS` to your Vercel frontend URL, for example `https://your-frontend.vercel.app`.
6. Deploy the service and wait for `/api/health` to pass.
7. Copy the Render backend URL and set it as `VITE_API_BASE_URL` in Vercel, for example `https://your-service.onrender.com/api`.

### Persistent metadata behavior

The backend now writes document metadata JSON to disk and reloads it on startup. That means uploaded document entries can survive normal service restarts as long as the persistent disk is still attached.

## API Summary

### Health

- `GET /api/health`

### Documents

- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{doc_id}/status`
- `DELETE /api/documents/{doc_id}`

### Chat

- `POST /api/chat`
- `POST /api/chat/stream`
- `POST /api/clear-history`

### Utilities

- `POST /api/export-pdf`
- `POST /api/generate-quiz`

## Example Chat Request

```json
{
  "question": "Summarize the document in 5 bullet points.",
  "session_id": "browser-session-id",
  "doc_ids": ["document-id-1"],
  "top_k": 5,
  "stream": true
}
```

## Example Document Status Response

```json
{
  "doc_id": "0f9f4f62-8bb0-4c57-9321-cc8f6b33ab12",
  "doc_name": "sample.pdf",
  "status": "indexed",
  "total_chunks": 18,
  "total_pages": 7,
  "error": null
}
```

## Storage Model

DocMind stores state in two different ways:

- In memory: document registry and chat session history
- On disk: uploaded files, document metadata, and FAISS indexes in the configured storage paths

This means:

- restarting the backend clears chat history
- restarting the backend reloads persisted document metadata from disk when available
- uploaded files and vector indexes remain on disk unless deleted

## Current Limitations

- Chat memory is in memory, so sessions reset when the backend process restarts.
- There is no authentication or multi-user isolation.
- There is no database for document metadata; persistence is file-based.
- Confidence is heuristic and based only on retrieved chunk count, not model certainty.
- The first embedding/model load can be slow on a fresh environment.

## Troubleshooting

### `GROQ_API_KEY` is missing

Create `backend/.env` from `backend/.env.example` and add a valid key.

### Frontend cannot reach the backend

Make sure:

- the backend is running on `http://localhost:8000`
- the frontend is running on `http://localhost:5173`
- the Vite proxy is still configured for `/api`

### `npm: command not found`

Load your Node environment first:

```bash
source ~/.nvm/nvm.sh
nvm use
```

### Documents stay in `processing`

Check the backend logs for:

- parsing failures
- model download delays
- invalid file contents
- embedding initialization issues

### Upload fails for a valid-looking file

Only `.pdf`, `.docx`, and `.txt` are accepted. Files with other extensions are rejected before ingestion.

### Answers say no relevant information was found

Confirm that:

- the document finished indexing
- the correct document is selected in the sidebar
- your question is actually answerable from the uploaded text

## Future Improvements

- persist document metadata in a database
- restore indexed documents automatically on backend restart
- add user authentication
- support more document formats
- improve citation ranking and confidence scoring
- add test coverage for ingestion and chat routes

## License

This repository currently does not include a license file. Add one if you plan to distribute or open-source the project broadly.
