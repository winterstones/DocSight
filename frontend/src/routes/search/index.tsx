/**
 * SEMAINE 4 — TanStack Router : route de recherche avec search params typés
 *
 * Concepts démontrés :
 *  - validateSearch : params URL validés par Zod → erreur TypeScript si invalide
 *  - loader : données préchargées AVANT le rendu → 0 spinner de chargement
 *  - TanStack Table : tri, filtres, pagination côté serveur
 */
import { createFileRoute } from "@tanstack/react-router"
import { useRef } from "react"
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table"

import { SearchParamsSchema, type SearchResult } from "../../schemas/search.schema"
import { searchKeys }       from "../../hooks/queryKeys"
import { useSearch, useTags } from "../../hooks/useSearch"
import { searchApi }         from "../../api/search.api"

// ─── Route definition ─────────────────────────────────────────────────────────

export const Route = createFileRoute("/search/")({
  // Search params validés par Zod — TypeScript erreur si invalide
  validateSearch: SearchParamsSchema,

  // Loader : précharge les données avant le rendu du composant
  // => L'utilisateur ne voit jamais de spinner sur la page de recherche
  loader: ({ context: { queryClient }, search }) => {
    if (search.q) {
      queryClient.prefetchQuery({
        queryKey: searchKeys.list(search),
        queryFn:  () => searchApi.search(search),
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

  // AbortController pour la barre de recherche live
  const abortRef = useRef<AbortController | null>(null)

  const table = useReactTable({
    data:             data?.results ?? [],
    columns,
    getCoreRowModel:  getCoreRowModel(),
    manualPagination: true,                    // Pagination côté serveur
    pageCount:        data ? Math.ceil(data.total / search.page_size) : 0,
  })

  const handleSearch = (q: string) => {
    abortRef.current?.abort()
    abortRef.current = new AbortController()
    navigate({ search: (prev) => ({ ...prev, q, page: 1 }) })
  }

  return (
    <div className="search-page">
      {/* Barre de recherche */}
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

      {/* Filtres tags */}
      <div className="tag-filters">
        {tags?.map((tag) => (
          <button
            key={tag}
            id={`filter-tag-${tag}`}
            className={`tag-filter ${search.tags.includes(tag) ? "active" : ""}`}
            onClick={() =>
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
          >
            {tag}
          </button>
        ))}
      </div>

      {/* TanStack Table */}
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
          {isLoading
            ? Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  {columns.map((_, j) => (
                    <td key={j}><div className="skeleton" /></td>
                  ))}
                </tr>
              ))
            : table.getRowModel().rows.map((row) => (
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
    </div>
  )
}
