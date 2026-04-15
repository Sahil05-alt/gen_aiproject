# DocMind

DocMind is a full-stack document chat application that lets you upload files, index them with FAISS, and ask grounded questions through a streaming chat interface. It is built for fast local experimentation with retrieval-augmented generation (RAG) using FastAPI on the backend and React on the frontend.

## Highlights

- Upload `.pdf`, `.docx`, and `.txt` documents
- Split documents into chunks and embed them with `sentence-transformers/all-MiniLM-L6-v2`
- Store each document in its own FAISS index
- Query one or many selected documents at the same time
- Stream answers back to the UI with citations and a simple confidence score
- Keep lightweight session-based chat memory in memory
- Export chat transcripts as PDF
- Generate multiple-choice quizzes from retrieved document context

## Tech Stack

- Frontend: React 18, Vite, Tailwind CSS
- Backend: FastAPI, Uvicorn
- Retrieval: LangChain + FAISS with MMR retrieval
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- LLM: Groq via `langchain-groq`
- Document parsing: `pypdf`, `docx2txt`

## How It Works

1. A document is uploaded through the React UI.
2. The FastAPI backend stores the file in `backend/data/uploads`.
3. The ingestion service loads the document, splits it into chunks, and adds metadata like document name and chunk index.
4. Embeddings are generated and written to a per-document FAISS index under `backend/data/vectorstore`.
5. At question time, DocMind loads the selected indexes, merges them if needed, retrieves relevant chunks with MMR, and sends the grounded context to Groq.
6. The UI streams the answer, shows citations, and can reuse the retrieved context for quiz generation.

## Project Structure

```text
docmind/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env.example
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
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── components/
│       └── utils/
└── README.md
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- An active Groq API key

## Environment Setup

Create a backend environment file from the example:

```bash
cd backend
cp .env.example .env
```

Update `backend/.env` with your values:

```env
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K=5
VECTOR_STORE_PATH=./data/vectorstore
UPLOADS_PATH=./data/uploads
```

## Installation

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend

```bash
cd frontend
npm install
```

If Node is managed by `nvm`, load it first:

```bash
source ~/.nvm/nvm.sh
nvm use
```

## Running the App

Start the backend and frontend in separate terminals.

### Terminal 1: backend

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend URL: `http://localhost:8000`

### Terminal 2: frontend

```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use
npm run dev -- --host 0.0.0.0
```

Frontend URL: `http://localhost:5173`

## Using DocMind

1. Launch both services.
2. Open `http://localhost:5173`.
3. Upload one or more `.pdf`, `.docx`, or `.txt` files.
4. Wait for each document to move from `Processing...` to `indexed`.
5. Select the documents you want to query from the sidebar.
6. Ask a question in the chat input.
7. Review the streamed answer, inline citations, and confidence indicator.
8. Optionally export the conversation as PDF or generate a quiz from the latest retrieved citations.

## API Overview

### Health

- `GET /api/health`

### Documents

- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{doc_id}/status`
- `DELETE /api/documents/{doc_id}`

### Chat and Session

- `POST /api/chat`
- `POST /api/chat/stream`
- `POST /api/clear-history`

### Extras

- `POST /api/export-pdf`
- `POST /api/generate-quiz`

## Notes and Limitations

- Document metadata and chat session history are stored in memory, so they reset when the backend restarts.
- Uploaded files and FAISS indexes remain on disk unless you delete them through the app or remove them manually.
- The backend enables CORS for local frontend ports `5173`, `5174`, and `3000`.
- Retrieval is limited to the selected documents, which keeps answers grounded but also means unselected documents are ignored.

## Troubleshooting

### `GROQ_API_KEY` is missing

Make sure `backend/.env` exists and contains a valid `GROQ_API_KEY`.

### Frontend cannot reach the backend

Confirm the backend is running on `http://localhost:8000` and the frontend is using the default `/api` proxy setup.

### `npm: command not found`

Load Node through `nvm` and retry:

```bash
source ~/.nvm/nvm.sh
nvm use
```

### Documents stay in `Processing...`

Check the backend logs for parsing, embedding, or model-loading errors. Large model downloads or invalid files can delay indexing on first run.
