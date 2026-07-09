import { createFileRoute } from "@tanstack/react-router"

export const Route = createFileRoute("/upload")({
  component: () => (
    <div style={{ padding: "2rem", textAlign: "center" }}>
      <h1>Importation de documents</h1>
      <p>Cette fonctionnalité sera bientôt disponible.</p>
    </div>
  ),
})
