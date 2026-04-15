const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '');

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

export async function getDocuments() {
  const response = await fetch(`${API_BASE}/documents`);
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }
  return response.json();
}

export async function getDocumentStatus(docId) {
  const response = await fetch(`${API_BASE}/documents/${docId}/status`);
  if (!response.ok) {
    throw new Error('Failed to fetch document status');
  }
  return response.json();
}

export async function deleteDocument(docId) {
  const response = await fetch(`${API_BASE}/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error('Failed to delete document');
  }
  return response.json();
}

export async function chat(question, docIds, sessionId, topK = 5) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      doc_ids: docIds,
      top_k: topK,
      stream: false,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Chat failed');
  }

  return response.json();
}

export async function chatStream(question, docIds, sessionId, topK = 5) {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      question,
      session_id: sessionId,
      doc_ids: docIds,
      top_k: topK,
      stream: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Chat failed');
  }

  return response.body;
}

export async function clearHistory(sessionId) {
  const response = await fetch(`${API_BASE}/clear-history`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to clear history');
  }

  return response.json();
}

export async function exportChatPdf(docTitle, messages) {
  const response = await fetch(`${API_BASE}/export-pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      doc_title: docTitle,
      messages,
    }),
  });

  if (!response.ok) {
    let errorMessage = 'Failed to export PDF';
    try {
      const error = await response.json();
      errorMessage = error.detail || errorMessage;
    } catch {
      // Keep the default message if the error body is not JSON.
    }
    throw new Error(errorMessage);
  }

  return {
    blob: await response.blob(),
    filename: getFilenameFromDisposition(response.headers.get('Content-Disposition')),
  };
}

export async function generateQuiz(context, numQuestions) {
  const response = await fetch(`${API_BASE}/generate-quiz`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      context,
      num_questions: numQuestions,
    }),
  });

  if (!response.ok) {
    let errorMessage = 'Failed to generate quiz';
    try {
      const error = await response.json();
      errorMessage = error.detail || errorMessage;
    } catch {
      // Keep the default message if the error body is not JSON.
    }
    throw new Error(errorMessage);
  }

  return response.json();
}

function getFilenameFromDisposition(disposition) {
  if (!disposition) {
    return 'docmind-chat-export.pdf';
  }

  const match = disposition.match(/filename="([^"]+)"/);
  return match?.[1] || 'docmind-chat-export.pdf';
}

export async function healthCheck() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error('Health check failed');
  }
  return response.json();
}
