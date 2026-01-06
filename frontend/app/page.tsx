import React from "react";
import Chat from "./components/Chat";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-black via-zinc-900 to-black text-white">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <h1 className="text-3xl font-semibold mb-1">Perplexity for Fashion 👗</h1>
        <p className="text-zinc-400 mb-6">Agentic multimodal search over a custom fashion catalogue</p>
        <Chat />
      </div>
    </main>
  );
}
