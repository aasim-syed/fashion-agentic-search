// app/page.tsx
import Chat from "./components/Chat";

export default function Home() {
  return (
    <main className="page">
      <div className="container">
        <header className="header">
          <div>
            <h1 className="title">
              Perplexity for Fashion <span aria-hidden>👗</span>
            </h1>
            <p className="subtitle">
              Agentic multimodal search over a custom fashion catalogue
            </p>
          </div>
          <div className="headerRight">
            <span className="pill">Local: FastAPI + Qdrant + Ollama</span>
          </div>
        </header>

        <Chat />
      </div>
    </main>
  );
}
