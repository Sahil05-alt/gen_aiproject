import React, { useState } from 'react';
import { exportChatPdf } from '../utils/api';

function getDocTitle(selectedDocs, documents) {
  const selectedNames = documents
    .filter((doc) => selectedDocs.includes(doc.doc_id))
    .map((doc) => doc.doc_name);

  if (selectedNames.length === 0) {
    return 'Document Chat';
  }

  if (selectedNames.length === 1) {
    return selectedNames[0];
  }

  return `${selectedNames.length} documents`;
}

export default function ExportPDFButton({ messages, documents, selectedDocs, disabled }) {
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const docTitle = getDocTitle(selectedDocs, documents);
      const { blob, filename } = await exportChatPdf(docTitle, messages);
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) {
      alert(`Export failed: ${error.message}`);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <button
      onClick={handleExport}
      disabled={disabled || isExporting}
      className="px-3 py-1.5 text-sm font-medium text-slate-600 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {isExporting ? 'Exporting...' : 'Export PDF'}
    </button>
  );
}
