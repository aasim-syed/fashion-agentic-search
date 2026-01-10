// frontend/app/page.tsx
import Chat from "./components/Chat";

export default function Page() {
  return (
    <>
      <header className="brandRow">
        <div className="logoDot" />
        <div>
          <div className="brandTitle">Fashion Agentic Search</div>
          <div className="brandSub">Multimodal semantic search • Qdrant + CLIP • Planner-driven</div>
        </div>

        <div style={{ marginLeft: "auto", display: "flex", gap: 10 }}>
          <a className="btn ghost" href="http://localhost:6333/dashboard" target="_blank" rel="noreferrer">
            Qdrant
          </a>
          <a className="btn ghost" href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            API Docs
          </a>
        </div>
      </header>

      <main>
        <Chat />
      </main>
    </>
  );
}
