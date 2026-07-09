/** @vitest-environment jsdom */
import { describe, it, expect, beforeAll, afterEach, afterAll } from "vitest"
import { render, screen, fireEvent, waitFor } from "@testing-library/react"
import { setupServer } from "msw/node"
import { http, HttpResponse } from "msw"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { RouterProvider, createRouter, createMemoryHistory } from "@tanstack/react-router"
import { routeTree } from "../routeTree.gen"
import type { SearchResponse } from "../schemas/search.schema"

// ─── MSW Mock Server ─────────────────────────────────────────────────────────

const mockResults: SearchResponse = {
  results: [
    {
      id: "doc-1",
      title: "Manuel Utilisateur v2.pdf",
      content_preview: "Section 3: Comment configurer l'accès...",
      file_type: "pdf",
      tags: ["manuel", "v2"],
      score: 0.95,
      thumbnail_url: null,
    },
    {
      id: "doc-2",
      title: "Notes de Réunion Q3.docx",
      content_preview: "Discussions sur la roadmap Q3...",
      file_type: "docx",
      tags: ["réunion", "q3"],
      score: 0.88,
      thumbnail_url: null,
    }
  ],
  total: 2,
  query: "",
  page: 1,
  page_size: 20
}

const server = setupServer(
  http.get("*/api/search", ({ request }) => {
    const url = new URL(request.url)
    const q = url.searchParams.get("q")
    
    // Si la recherche contient "manuel", on renvoie juste doc-1
    if (q === "manuel") {
      return HttpResponse.json({
        ...mockResults,
        results: [mockResults.results[0]],
        total: 1,
        query: "manuel"
      })
    }
    
    return HttpResponse.json(mockResults)
  }),
  
  http.get("*/api/search/tags", () => {
    return HttpResponse.json(["manuel", "v2", "réunion", "q3", "rh"])
  })
)

beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())

// ─── Setup Tests ─────────────────────────────────────────────────────────────

const createTestRouter = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } }
  })
  
  const router = createRouter({ 
    routeTree,
    history: createMemoryHistory({ initialEntries: ["/search"] }),
    context: { queryClient }
  })
  
  return { router, queryClient }
}

describe("Search Page", () => {
  it("renders search bar and fetches initial results", async () => {
    const { router, queryClient } = createTestRouter()
    
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    )

    // Vérifie le rendu de la search bar
    expect(screen.getByPlaceholderText(/Rechercher dans vos documents/i)).toBeDefined()
    
    // Vérifie que les filtres sont rendus
    expect(await screen.findByText("Filtres")).toBeDefined()
    expect(await screen.findByText("Types de fichiers")).toBeDefined()
    
    // Vérifie l'appel initial et le rendu des données MSW
    expect(await screen.findByText("Manuel Utilisateur v2.pdf")).toBeDefined()
    expect(await screen.findByText("Notes de Réunion Q3.docx")).toBeDefined()
    
    // Vérifie que le tag est rendu
    expect(await screen.findByText("rh")).toBeDefined()
  })

  it("debounces search input", async () => {
    const { router, queryClient } = createTestRouter()
    
    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    )
    
    // Attend initial render
    expect(await screen.findByText("Notes de Réunion Q3.docx")).toBeDefined()

    const input = screen.getByPlaceholderText(/Rechercher dans vos documents/i)
    
    fireEvent.change(input, { target: { value: "manuel" } })
    
    // Notes de Réunion Q3 devrait disparaître après le debounce de 300ms + fetch
    await waitFor(() => {
      expect(screen.queryByText("Notes de Réunion Q3.docx")).toBeNull()
    }, { timeout: 1500 })
    
    // Manuel devrait toujours être là
    expect(screen.getByText("Manuel Utilisateur v2.pdf")).toBeDefined()
  })
})
