"use client";

import React from "react";
import { useState } from "react";
import ProductCard from "./ProductCard";
import DebugPanel from "./DebugPanel";

type Result = {
  product_id: string;
  description: string;
  image: string;
  score: number;
};

export default function Chat() {
  const [message, setMessage] = useState("");
  const [image, setImage] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [assistant, setAssistant] = useState("");
  const [results, setResults] = useState<Result[]>([]);
  const [debug, setDebug] = useState<any>(null);

  const handleSend = async () => {
    if (!message && !image) return;

    setLoading(true);
    setAssistant("");
    setResults([]);
    setDebug(null);

    const formData = new FormData();
    formData.append("message", message);
    if (image) formData.append("image", image);

    const res = await fetch("http://localhost:8000/api/chat", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    setAssistant(data.assistant_message);
    setResults(data.results || []);
    setDebug(data.debug || null);
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Assistant Answer */}
      {assistant && (
        <div className="bg-white/5 backdrop-blur rounded-xl p-4 border border-white/10">
          <p className="text-lg">{assistant}</p>
        </div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
          {results.map((r) => (
            <ProductCard key={r.product_id} product={r} />
          ))}
        </div>
      )}

      {/* Debug Panel */}
      {debug && <DebugPanel debug={debug} />}

      {/* Input Area */}
      <div className="bg-white/5 backdrop-blur rounded-xl p-4 border border-white/10">
        <textarea
          className="w-full bg-transparent border border-white/10 rounded-lg p-3 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-white/20"
          rows={3}
          placeholder="Describe what you're looking for..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
        />

        <div className="flex items-center justify-between mt-3">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setImage(e.target.files?.[0] || null)}
            className="text-sm text-zinc-400"
          />

          <button
            onClick={handleSend}
            disabled={loading}
            className="px-5 py-2 rounded-lg bg-white text-black font-medium hover:bg-zinc-200 transition disabled:opacity-50"
          >
            {loading ? "Searching..." : "Search"}
          </button>
        </div>
      </div>
    </div>
  );
}
