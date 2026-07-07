import { createFileRoute, Link } from "@tanstack/react-router"

export const Route = createFileRoute("/")({
  component: HomePage,
})

function HomePage() {
  return (
    <div className="home-page">
      <section className="hero">
        <h1>Recherchez dans vos documents industriels</h1>
        <p className="hero-sub">
          Propulsé par Loom — moteur open-source du Cyber Command Suisse.
          OCR, full-text search, RAG chatbot.
        </p>
        <div className="hero-actions">
          <Link to="/search" id="cta-search" className="btn btn-primary">
            🔍 Lancer une recherche
          </Link>
          <Link to="/upload" id="cta-upload" className="btn btn-secondary">
            📤 Importer un document
          </Link>
        </div>
      </section>

      <section className="features-grid">
        {[
          { icon: "🔍", title: "Full-text Search",    desc: "Recherche instantanée dans tous vos documents indexés." },
          { icon: "🤖", title: "RAG Chatbot",         desc: "Posez des questions en langage naturel sur vos documents." },
          { icon: "📄", title: "OCR Automatique",     desc: "Extraction du texte depuis PDF, images et documents scannés." },
          { icon: "🏷️", title: "Tags & Périmètre",   desc: "Chaque utilisateur ne voit que les documents de son périmètre." },
          { icon: "📊", title: "Audit Trail",         desc: "Traçabilité complète des recherches pour la compliance." },
          { icon: "🔔", title: "Alertes",             desc: "Notification automatique à l'arrivée de nouveaux documents." },
        ].map((f) => (
          <div key={f.title} className="feature-card" id={`feature-${f.title.toLowerCase().replace(/\s+/g, "-")}`}>
            <span className="feature-icon">{f.icon}</span>
            <h3>{f.title}</h3>
            <p>{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  )
}
