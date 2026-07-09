/**
 * SEMAINE 4 — TanStack Router : route de recherche avec search params typés
 */
import { createFileRoute } from "@tanstack/react-router"
import { useRef, useState } from "react"
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"

import { SearchParamsSchema, type SearchResult, FileTypeSchema } from "../../schemas/search.schema"
import { searchKeys }       from "../../hooks/queryKeys"
import { useSearch, useTags } from "../../hooks/useSearch"
import { searchApi }         from "../../api/search.api"
import { DocumentCard } from "../../components/DocumentCard"

// ─── Route definition ─────────────────────────────────────────────────────────

export const Route = createFileRoute("/search/")({
  validateSearch: SearchParamsSchema,

  loaderDeps: ({ search: { q, tags, file_types, page, page_size } }) => ({
    q,
    tags,
    file_types,
    page,
    page_size,
  }),

  loader: ({ context: { queryClient }, deps }) => {
    if (deps.q) {
      queryClient.prefetchQuery({
        queryKey: searchKeys.list(deps),
        queryFn:  () => searchApi.search(deps),
      })
    }
  },

  component: SearchPage,
})

// ─── TanStack Table : définition des colonnes ─────────────────────────────────

const columnHelper = createColumnHelper<SearchResult>()

const columns = [
  columnHelper.accessor("title", {
    header:       "Document",
    enableSorting: true,
    cell: (info) => (
      <div>
        <p style={{ fontWeight: 600, margin: 0 }}>{info.getValue()}</p>
        <p style={{ fontSize: 12, color: "#888", margin: 0 }}>
          {info.row.original.content_preview}
        </p>
      </div>
    ),
  }),
  columnHelper.accessor("file_type", {
    header: "Type",
    cell:   (info) => <span className={`badge badge-${info.getValue()}`}>{info.getValue()}</span>,
  }),
  columnHelper.accessor("tags", {
    header: "Tags",
    cell:   (info) => (
      <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
        {info.getValue().map((tag) => (
          <span key={tag} className="tag">{tag}</span>
        ))}
      </div>
    ),
  }),
  columnHelper.accessor("score", {
    header:       "Pertinence",
    enableSorting: true,
    cell:         (info) => `${Math.round(info.getValue() * 100)}%`,
  }),
]

// ─── Page Component ───────────────────────────────────────────────────────────

function SearchPage() {
  const search   = Route.useSearch()
  const navigate = Route.useNavigate()

  const { data, isLoading, isFetching } = useSearch(search)
  const { data: tags }                  = useTags()

  // View toggle
  const [viewMode, setViewMode] = useState<"list" | "grid">("list")

  // Debounce ref
  const debounceRef = useRef<NodeJS.Timeout | null>(null)

  const table = useReactTable({
    data:             data?.results ?? [],
    columns,
    getCoreRowModel:  getCoreRowModel(),
    manualPagination: true,
    pageCount:        data ? Math.ceil(data.total / search.page_size) : 0,
  })

  const handleSearch = (q: string) => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current)
    }
    
    debounceRef.current = setTimeout(() => {
      navigate({ search: (prev) => ({ ...prev, q, page: 1 }) })
    }, 300)
  }

  const toggleTag = (tag: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: 1,
        tags: prev.tags.includes(tag)
          ? prev.tags.filter((t) => t !== tag)
          : [...prev.tags, tag],
      }),
    })
  }

  const toggleFileType = (type: string) => {
    navigate({
      search: (prev) => ({
        ...prev,
        page: 1,
        file_types: prev.file_types.includes(type)
          ? prev.file_types.filter((t) => t !== type)
          : [...prev.file_types, type],
      }),
    })
  }

  const resetFilters = () => {
    navigate({
      search: (prev) => ({
        ...prev,
        q: "",
        tags: [],
        file_types: [],
        page: 1
      })
    })
    const input = document.getElementById("search-input") as HTMLInputElement
    if (input) input.value = ""
  }

  return (
    <div className="search-page-layout">
      {/* Sidebar Filters */}
      <aside className="search-sidebar">
        <div className="sidebar-header">
          <h3>Filtres</h3>
          <button onClick={resetFilters} className="btn-reset">Réinitialiser</button>
        </div>

        <div className="filter-section">
          <h4>Types de fichiers</h4>
          <div className="filter-list">
            {FileTypeSchema.options.map(type => (
              <label key={type} className="filter-checkbox">
                <input 
                  type="checkbox" 
                  checked={search.file_types.includes(type)}
                  onChange={() => toggleFileType(type)}
                />
                <span className={`badge badge-${type}`}>{type}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="filter-section">
          <h4>Tags</h4>
          <div className="filter-list tags-list">
            {tags?.map((tag) => (
              <label key={tag} className="filter-checkbox">
                <input 
                  type="checkbox" 
                  checked={search.tags.includes(tag)}
                  onChange={() => toggleTag(tag)}
                />
                <span className="tag">{tag}</span>
              </label>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="search-main">
        <div className="search-header-bar">
          <div className="search-bar">
            <input
              id="search-input"
              type="text"
              placeholder="Rechercher dans vos documents..."
              defaultValue={search.q}
              onChange={(e) => handleSearch(e.target.value)}
            />
            {isFetching && <span className="loading-indicator">⟳</span>}
          </div>

          <div className="view-toggle">
            <button 
              className={viewMode === "list" ? "active" : ""} 
              onClick={() => setViewMode("list")}
            >
              ☰ Liste
            </button>
            <button 
              className={viewMode === "grid" ? "active" : ""} 
              onClick={() => setViewMode("grid")}
            >
              ⊞ Grille
            </button>
          </div>
        </div>

        <div className="results-container">
          {isLoading ? (
            <div className="loading-skeleton">Chargement...</div>
          ) : viewMode === "list" ? (
            <table id="results-table" className="results-table">
              <thead>
                {table.getHeaderGroups().map((headerGroup) => (
                  <tr key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <th
                        key={header.id}
                        onClick={header.column.getToggleSortingHandler()}
                        style={{ cursor: header.column.getCanSort() ? "pointer" : "default" }}
                      >
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{ asc: " ↑", desc: " ↓" }[header.column.getIsSorted() as string] ?? ""}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody>
                {table.getRowModel().rows.map((row) => (
                  <tr key={row.id} id={`result-row-${row.original.id}`}>
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id}>
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="results-grid">
              {data?.results.map(doc => (
                <DocumentCard key={doc.id} document={doc} view="grid" />
              ))}
            </div>
          )}
        </div>

        {/* Pagination côté serveur */}
        <div className="pagination" id="pagination-controls">
          <button
            id="prev-page"
            disabled={search.page <= 1}
            onClick={() => navigate({ search: (prev) => ({ ...prev, page: prev.page - 1 }) })}
          >
            ← Précédent
          </button>
          <span>Page {search.page} / {Math.ceil((data?.total ?? 0) / search.page_size)}</span>
          <button
            id="next-page"
            disabled={!data || search.page >= Math.ceil(data.total / search.page_size)}
            onClick={() => navigate({ search: (prev) => ({ ...prev, page: prev.page + 1 }) })}
          >
            Suivant →
          </button>
        </div>

        <p className="results-count">
          {data ? `${data.total} document(s) trouvé(s)` : ""}
        </p>
      </main>
    </div>
  )
}
