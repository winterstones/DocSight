import type { SearchResult } from "../../schemas/search.schema"

interface DocumentCardProps {
  document: SearchResult
  view?: "list" | "grid"
}

export function DocumentCard({ document, view = "grid" }: DocumentCardProps) {
  return (
    <div className={`document-card ${view}`}>
      {document.thumbnail_url ? (
        <img src={document.thumbnail_url} alt={document.title} className="doc-thumbnail" />
      ) : (
        <div className="doc-thumbnail placeholder">
          <span className={`badge badge-${document.file_type}`}>{document.file_type}</span>
        </div>
      )}
      <div className="doc-content">
        <h3 className="doc-title">{document.title}</h3>
        <p className="doc-preview">{document.content_preview}</p>
        <div className="doc-meta">
          <div className="doc-tags">
            {document.tags.map((tag) => (
              <span key={tag} className="tag">{tag}</span>
            ))}
          </div>
          <span className="doc-score">Pertinence: {Math.round(document.score * 100)}%</span>
        </div>
      </div>
    </div>
  )
}
