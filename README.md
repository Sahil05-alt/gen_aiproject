# DocMind

DocMind is a simple RAG app that lets you upload documents, index them with FAISS, and chat with them through a React UI.

## What It Does

- Uploads `.pdf`, `.docx`, and `.txt` files
- Splits documents into chunks
- Stores embeddings in a per-document FAISS index
- Lets you ask questions against one or more selected documents
- Streams answers back in the chat UI with citations

## Tech Stack

- Frontend: React + Vite + Tailwind CSS
- Backend: FastAPI + Uvicorn
- Vector store: FAISS
- Embeddings: `sentence-transformers/all-MiniLM-L6-v2`
- LLM: Groq `llama-3.3-70b-versatile`

## Project Structure

```text
docmind/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── routers/
│   └── services/
├── frontend/
│   ├── package.json
│   └── src/
└── README.md
```

## Environment Setup

Create `backend/.env` from `backend/.env.example`.

Example:

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

## Install

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

If `npm` is not available in your shell but Node is installed with `nvm`, load it first:

```bash
source ~/.nvm/nvm.sh
nvm use
```

## Run

Open two terminals.

### Terminal 1: backend

```bash
cd backend
source venv/bin/activate
python main.py
```

Backend runs on `http://localhost:8000`.

### Terminal 2: frontend

```bash
cd frontend
source ~/.nvm/nvm.sh
nvm use
npm run dev -- --host 0.0.0.0
```

Frontend runs on `http://localhost:5173`.

## Simple Walkthrough

1. Start the backend and frontend.
2. Open `http://localhost:5173`.
3. Click `Upload Document`.
4. Upload a `.pdf`, `.docx`, or `.txt` file.
5. Wait until the document status changes from `Processing...` to an indexed state with chunk count.
6. Make sure the document is selected in the sidebar.
7. Ask a question in the chat box.
8. Read the streamed answer and check the citations shown with it.
9. Select multiple documents if you want answers grounded across more than one file.
10. Delete a document from the sidebar if you want to remove its index.

## API Overview

### Document endpoints

- `POST /api/documents/upload`
- `GET /api/documents`
- `GET /api/documents/{doc_id}/status`
- `DELETE /api/documents/{doc_id}`

### Chat endpoints

- `POST /api/chat`
- `POST /api/chat/stream`

### Health endpoint

- `GET /api/health`

## Notes

- Uploaded files are stored under `backend/data/uploads`.
- FAISS indexes are stored under `backend/data/vectorstore`.
- Each document gets its own vector index directory.
- The app currently keeps document status in memory, so restarting the backend clears the in-memory registry.

## Troubleshooting

### `npm: command not found`

Load Node through `nvm` first:

```bash
source ~/.nvm/nvm.sh
nvm use
```

### Frontend cannot reach backend

Make sure the backend is running on port `8000` before opening the frontend.

### Missing Groq key

If chat fails, check that `GROQ_API_KEY` is set in `backend/.env`.
