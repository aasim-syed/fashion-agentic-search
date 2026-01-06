import React from 'react';

export default function DebugPanel({ debug }: { debug: any }) {
    return (
      <div className="bg-black/40 border border-white/10 rounded-xl p-4">
        <h3 className="text-sm font-semibold mb-2 text-zinc-300">Debug / Retrieval Plan</h3>
        <pre className="text-xs text-zinc-400 whitespace-pre-wrap">
          {JSON.stringify(debug, null, 2)}
        </pre>
      </div>
    );
  }
  