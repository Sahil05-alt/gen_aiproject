import React from 'react';

export default function CitationCard({ citation, index }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-medium">
          [{index + 1}]
        </span>
        <span className="font-semibold text-slate-700 truncate">
          {citation.doc_name}
        </span>
        {citation.page > 0 && (
          <span className="text-slate-500 text-xs">
            Page {citation.page}
          </span>
        )}
      </div>
      <p className="text-slate-600 line-clamp-2">{citation.excerpt}</p>
    </div>
  );
}
