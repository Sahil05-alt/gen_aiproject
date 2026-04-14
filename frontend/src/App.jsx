import React, { useState, useRef, useEffect } from 'react';
import { uploadDocument, getDocuments, deleteDocument, chat, chatStream } from './utils/api';
import ChatMessage from './components/ChatMessage';
import ChatInput from './components/ChatInput';
import EmptyState from './components/EmptyState';

const uniqueIds = (ids) => [...new Set(ids)];

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const docs = await getDocuments();
      setDocuments(docs);
      // Auto-select indexed documents
      const indexed = docs.filter(d => d.status === 'indexed').map(d => d.doc_id);
      setSelectedDocs(uniqueIds(indexed));
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    try {
      await uploadDocument(file);
      // Poll for status
      const pollInterval = setInterval(async () => {
        const docs = await getDocuments();
        setDocuments(docs);

        const indexed = docs
          .filter(d => d.status === 'indexed')
          .map(d => d.doc_id);
        setSelectedDocs(uniqueIds(indexed));

        const uploaded = docs.find(d => d.doc_name === file.name);
        if (uploaded && uploaded.status !== 'processing') {
          clearInterval(pollInterval);
        }
      }, 1000);
    } catch (error) {
      alert(`Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleUpload(file);
    }
  };

  const handleDelete = async (docId) => {
    try {
      await deleteDocument(docId);
      setDocuments(prev => prev.filter(d => d.doc_id !== docId));
      setSelectedDocs(prev => prev.filter(id => id !== docId));
    } catch (error) {
      alert(`Delete failed: ${error.message}`);
    }
  };

  const handleSend = async (question) => {
    if (selectedDocs.length === 0) {
      alert('Please select at least one document to chat with');
      return;
    }

    const userMessage = { role: 'user', content: question };
    setMessages(prev => [...prev, userMessage]);
    setIsChatLoading(true);

    try {
      const stream = await chatStream(question, selectedDocs);
      const reader = stream.getReader();
      const decoder = new TextDecoder();

      const assistantMessage = {
        role: 'assistant',
        content: '',
        citations: [],
        confidence: 0,
      };

      setMessages(prev => [...prev, assistantMessage]);

      let buffer = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;

            try {
              const event = JSON.parse(data);
              if (event.type === 'meta') {
                assistantMessage.citations = event.citations;
                assistantMessage.confidence = event.confidence;
              } else if (event.type === 'token') {
                assistantMessage.content += event.text;
              } else if (event.type === 'error') {
                assistantMessage.content += `\n\nError: ${event.text}`;
              }
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { ...assistantMessage };
                return updated;
              });
            } catch (e) {
              console.error('Failed to parse SSE:', e);
            }
          }
        }
      }
    } catch (error) {
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: `Error: ${error.message}`, citations: [], confidence: 0 }
      ]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const toggleDocSelection = (docId) => {
    setSelectedDocs(prev =>
      prev.includes(docId)
        ? prev.filter(id => id !== docId)
        : uniqueIds([...prev, docId])
    );
  };

  return (
    <div className="h-screen flex bg-slate-100">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-72 bg-white border-r border-slate-200 flex flex-col">
          <div className="p-4 border-b border-slate-200">
            <div className="flex items-center justify-between mb-1">
              <h1 className="text-xl font-bold text-slate-800">DocMind</h1>
              <button
                onClick={() => setShowSidebar(false)}
                className="p-1 hover:bg-slate-100 rounded"
              >
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded">FAISS</span>
              <span className="bg-green-100 text-green-700 px-2 py-0.5 rounded">MMR</span>
              <span className="bg-amber-100 text-amber-700 px-2 py-0.5 rounded">Llama 3.3</span>
            </div>
          </div>

          <div className="p-4 border-b border-slate-200">
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              {isUploading ? 'Uploading...' : 'Upload Document'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">
              Documents
            </h2>
            {documents.length === 0 ? (
              <p className="text-sm text-slate-400">No documents uploaded</p>
            ) : (
              <ul className="space-y-2">
                {documents.map((doc) => (
                  <li
                    key={doc.doc_id}
                    className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-50 group"
                  >
                    <input
                      type="checkbox"
                      checked={selectedDocs.includes(doc.doc_id)}
                      onChange={() => toggleDocSelection(doc.doc_id)}
                      disabled={doc.status !== 'indexed'}
                      className="w-4 h-4 text-blue-600 rounded disabled:opacity-50"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-700 truncate">
                        {doc.doc_name}
                      </p>
                      <p className="text-xs text-slate-500">
                        {doc.status === 'indexed' && `${doc.total_chunks} chunks`}
                        {doc.status === 'processing' && 'Processing...'}
                        {doc.status === 'error' && `Error: ${doc.error}`}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDelete(doc.doc_id)}
                      className="p-1 text-slate-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Main chat area */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <div className="bg-white border-b border-slate-200 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {!showSidebar && (
              <button
                onClick={() => setShowSidebar(true)}
                className="p-1 hover:bg-slate-100 rounded"
              >
                <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            <div className="flex items-center gap-2">
              <span className="bg-amber-100 text-amber-700 px-2 py-1 rounded text-xs font-medium">
                Llama 3.3 · 70B
              </span>
              {selectedDocs.length > 0 && (
                <span className="text-sm text-slate-500">
                  {selectedDocs.length} document{selectedDocs.length !== 1 ? 's' : ''} selected
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <EmptyState onUpload={() => fileInputRef.current?.click()} />
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.map((msg, idx) => (
                <ChatMessage key={idx} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat input */}
        <ChatInput
          onSend={handleSend}
          disabled={selectedDocs.length === 0}
          loading={isChatLoading}
        />
      </div>
    </div>
  );
}
