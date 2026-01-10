// frontend/app/layout.tsx
import "./global.css";

export const metadata = {
  title: "Fashion Agentic Search",
  description: "Multimodal semantic search • Qdrant + CLIP • Planner-driven",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="appShell">
          <div className="layout">{children}</div>
        </div>
      </body>
    </html>
  );
}
